import React, { useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Mic, PhoneOff, Loader2, ArrowLeft } from 'lucide-react'
import { motion } from 'framer-motion'
import { useVoiceAgent } from '@/hooks/useVoiceAgent'
import toast from 'react-hot-toast'

const customerNames = {
  dbat_pearl: 'D-BAT Pearl - Willie',
  mercy_house: 'Mercy House - Grace',
  customer_xyz: 'Customer XYZ Healthcare',
}

export default function VoiceDemo() {
  const { customerId } = useParams()
  const navigate = useNavigate()
  const { isConnected, isListening, transcript, error, connect, disconnect } = useVoiceAgent(customerId)

  useEffect(() => {
    if (error) {
      toast.error(error)
    }
  }, [error])

  const handleStart = () => {
    connect()
    toast.success('Connecting to voice agent...')
  }

  const handleStop = () => {
    disconnect()
    toast.success('Call ended')
  }

  return (
    <div className="container max-w-4xl mx-auto px-4 py-8">
      <Button
        variant="ghost"
        className="mb-6"
        onClick={() => navigate('/')}
      >
        <ArrowLeft className="w-4 h-4 mr-2" />
        Back to Services
      </Button>

      <Card>
        <CardHeader>
          <CardTitle className="text-2xl">
            Voice Agent Demo - {customerNames[customerId] || customerId}
          </CardTitle>
          <CardDescription>
            Click Start to talk with the AI voice agent. Speak naturally as you would on a phone call.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* Status Indicator */}
          <div className="flex items-center justify-center space-x-4">
            {!isConnected ? (
              <Button
                size="lg"
                onClick={handleStart}
                className="bg-blue-500 hover:bg-blue-600 text-white px-8 py-6 text-lg"
              >
                <Mic className="w-6 h-6 mr-2" />
                Start Talking to Agent
              </Button>
            ) : (
              <Button
                size="lg"
                variant="destructive"
                onClick={handleStop}
                className="px-8 py-6 text-lg"
              >
                <PhoneOff className="w-6 h-6 mr-2" />
                End Conversation
              </Button>
            )}
          </div>

          {/* Visual Indicator */}
          {isConnected && (
            <div className="flex flex-col items-center space-y-4">
              <motion.div
                className="w-32 h-32 rounded-full bg-blue-500 flex items-center justify-center"
                animate={{
                  scale: isListening ? [1, 1.1, 1] : 1,
                }}
                transition={{
                  duration: 1.5,
                  repeat: isListening ? Infinity : 0,
                }}
              >
                {isListening ? (
                  <Mic className="w-16 h-16 text-white" />
                ) : (
                  <Loader2 className="w-16 h-16 text-white animate-spin" />
                )}
              </motion.div>
              <p className="text-lg font-medium">
                {isListening ? '🎤 Listening...' : '🔄 Connecting...'}
              </p>
            </div>
          )}

          {/* Transcript */}
          {transcript.length > 0 && (
            <div className="mt-6">
              <h3 className="text-lg font-semibold mb-3">Conversation</h3>
              <div className="space-y-2 max-h-64 overflow-y-auto bg-gray-50 p-4 rounded-lg">
                {transcript.map((msg, idx) => (
                  <div
                    key={idx}
                    className={`p-2 rounded ${
                      msg.role === 'user' ? 'bg-blue-100 text-blue-900' : 'bg-gray-200 text-gray-900'
                    }`}
                  >
                    <span className="font-semibold">{msg.role === 'user' ? 'You' : 'Agent'}:</span>{' '}
                    {msg.text}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Instructions */}
          <div className="border-t pt-4 mt-4">
            <h4 className="font-semibold mb-2">How to use:</h4>
            <ul className="list-disc list-inside space-y-1 text-sm text-gray-600">
              <li>Click "Start Talking to Agent" to begin</li>
              <li>Allow microphone access when prompted</li>
              <li>Speak naturally - the agent will respond in real-time</li>
              <li>Click "End Conversation" when you're done</li>
            </ul>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
