import { useState, useRef, useEffect } from 'react'

export function useVoiceAgent(customerId) {
  const [isConnected, setIsConnected] = useState(false)
  const [isListening, setIsListening] = useState(false)
  const [transcript, setTranscript] = useState([])
  const [error, setError] = useState(null)

  const socketRef = useRef(null)
  const mediaStreamRef = useRef(null)
  const audioContextRef = useRef(null)
  const processorRef = useRef(null)
  const workletNodeRef = useRef(null)

  useEffect(() => {
    // Initialize audio context
    audioContextRef.current = new AudioContext({ sampleRate: 24000 })

    // Load audio worklet processor
    const loadAudioProcessor = async () => {
      try {
        await audioContextRef.current.audioWorklet.addModule('/audio-processor.js')
        workletNodeRef.current = new AudioWorkletNode(audioContextRef.current, 'audio-processor')
        workletNodeRef.current.connect(audioContextRef.current.destination)
      } catch (err) {
        console.error('Failed to load audio processor:', err)
      }
    }

    loadAudioProcessor()

    return () => {
      disconnect()
      if (audioContextRef.current) {
        audioContextRef.current.close()
      }
    }
  }, [])

  const float32ToInt16 = (float32Array) => {
    const int16 = new Int16Array(float32Array.length)
    for (let i = 0; i < float32Array.length; i++) {
      const s = Math.max(-1, Math.min(1, float32Array[i]))
      int16[i] = s < 0 ? s * 0x8000 : s * 0x7FFF
    }
    return int16
  }

  const playAudio = async (arrayBuffer) => {
    if (!workletNodeRef.current) return

    if (audioContextRef.current.state === 'suspended') {
      await audioContextRef.current.resume()
    }

    const int16 = new Int16Array(arrayBuffer)
    const float32 = new Float32Array(int16.length)
    for (let i = 0; i < int16.length; i++) {
      float32[i] = int16[i] / (int16[i] < 0 ? 0x8000 : 0x7FFF)
    }
    workletNodeRef.current.port.postMessage({ pcm: float32 })
  }

  const stopPlayback = () => {
    if (workletNodeRef.current) {
      workletNodeRef.current.port.postMessage({ clear: true })
    }
  }

  const startMicrophone = async () => {
    try {
      mediaStreamRef.current = await navigator.mediaDevices.getUserMedia({
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
        },
      })

      const source = audioContextRef.current.createMediaStreamSource(mediaStreamRef.current)
      processorRef.current = audioContextRef.current.createScriptProcessor(4096, 1, 1)

      processorRef.current.onaudioprocess = (event) => {
        const input = event.inputBuffer.getChannelData(0)
        const pcm = float32ToInt16(input)
        if (socketRef.current?.readyState === WebSocket.OPEN) {
          socketRef.current.send(pcm.buffer)
        }
      }

      source.connect(processorRef.current)
      processorRef.current.connect(audioContextRef.current.destination)
      setIsListening(true)
    } catch (err) {
      setError('Failed to access microphone: ' + err.message)
    }
  }

  const stopMicrophone = () => {
    if (processorRef.current) {
      processorRef.current.disconnect()
      processorRef.current = null
    }
    if (mediaStreamRef.current) {
      mediaStreamRef.current.getTracks().forEach((t) => t.stop())
      mediaStreamRef.current = null
    }
    setIsListening(false)
  }

  const connect = () => {
    const protocol = window.location.protocol === 'https:' ? 'wss' : 'ws'
    const host = window.location.host.includes('localhost:3000') ? 'localhost:8000' : window.location.host

    // Use customerId parameter to route to correct agent
    const wsUrl = `${protocol}://${host}/web/ws?customerId=${customerId || 'default'}`

    socketRef.current = new WebSocket(wsUrl)
    socketRef.current.binaryType = 'arraybuffer'

    socketRef.current.onopen = async () => {
      console.log('WebSocket connected')
      setIsConnected(true)
      setError(null)
      await audioContextRef.current.resume()
      await startMicrophone()
    }

    socketRef.current.onmessage = async (event) => {
      if (typeof event.data === 'string') {
        const msg = JSON.parse(event.data)
        if (msg.Kind === 'StopAudio') {
          stopPlayback()
        }
        if (msg.Kind === 'Transcription') {
          setTranscript((prev) => [...prev, { role: 'user', text: msg.Text }])
        }
      } else if (event.data instanceof ArrayBuffer) {
        await playAudio(event.data)
      }
    }

    socketRef.current.onclose = () => {
      console.log('WebSocket closed')
      setIsConnected(false)
      stopMicrophone()
    }

    socketRef.current.onerror = (err) => {
      console.error('WebSocket error', err)
      setError('Connection error')
    }
  }

  const disconnect = () => {
    if (socketRef.current) {
      socketRef.current.close()
    }
    stopMicrophone()
  }

  return {
    isConnected,
    isListening,
    transcript,
    error,
    connect,
    disconnect,
  }
}
