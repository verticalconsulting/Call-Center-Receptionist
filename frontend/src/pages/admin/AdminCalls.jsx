import React, { useEffect, useState } from 'react'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'

function parseTranscript(raw) {
  if (!raw) return []
  try {
    const value = typeof raw === 'string' ? JSON.parse(raw) : raw
    return Array.isArray(value) ? value : []
  } catch {
    return []
  }
}

export default function AdminCalls() {
  const [items, setItems] = useState([])
  const [error, setError] = useState('')
  const [selectedCall, setSelectedCall] = useState(null)

  useEffect(() => {
    const load = async () => {
      try {
        const res = await fetch('/api/admin/calls?limit=500')
        const data = await res.json()
        if (!res.ok) throw new Error(data.error || 'Failed loading calls')
        setItems(data.items || [])
      } catch (err) {
        setError(err.message || 'Failed loading calls')
      }
    }
    load()
  }, [])

  if (error) return <div className="text-red-400">{error}</div>

  return (
    <div>
      <h2 className="text-lg font-semibold mb-3">Call History</h2>
      <div className="overflow-auto rounded-lg border border-slate-800">
        <table className="min-w-full text-sm">
          <thead className="bg-slate-950">
            <tr className="text-left text-slate-300">
              <th className="p-3">Started</th>
              <th className="p-3">Customer</th>
              <th className="p-3">Channel</th>
              <th className="p-3">Duration</th>
              <th className="p-3">User Turns</th>
              <th className="p-3">Assistant Turns</th>
              <th className="p-3">First User Utterance</th>
            </tr>
          </thead>
          <tbody>
            {items.length === 0 && (
              <tr>
                <td className="p-3 text-slate-400" colSpan={7}>
                  No calls found.
                </td>
              </tr>
            )}
            {items.map((c) => (
              <tr
                key={c.call_id}
                className="border-t border-slate-800 hover:bg-slate-900/70 cursor-pointer"
                onClick={() => setSelectedCall(c)}
              >
                <td className="p-3">{new Date(c.started_at_utc).toLocaleString()}</td>
                <td className="p-3">{c.customer_id}</td>
                <td className="p-3">{c.channel}</td>
                <td className="p-3">{Math.round(Number(c.duration_seconds || 0))}s</td>
                <td className="p-3">{c.user_turns}</td>
                <td className="p-3">{c.assistant_turns}</td>
                <td className="p-3 max-w-[260px] truncate">{c.first_user_utterance || '-'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <Dialog open={!!selectedCall} onOpenChange={(open) => !open && setSelectedCall(null)}>
        <DialogContent className="max-w-3xl bg-slate-950 border-slate-700 text-slate-100 max-h-[80vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Call Transcript</DialogTitle>
            <DialogDescription className="text-slate-400">
              {selectedCall
                ? `${selectedCall.customer_id} • ${new Date(selectedCall.started_at_utc).toLocaleString()}`
                : ''}
            </DialogDescription>
          </DialogHeader>

          {selectedCall && (
            <div className="space-y-3">
              <div className="grid grid-cols-2 md:grid-cols-4 gap-2 text-xs">
                <div className="rounded border border-slate-800 p-2">
                  <p className="text-slate-400">Duration</p>
                  <p>{Math.round(Number(selectedCall.duration_seconds || 0))}s</p>
                </div>
                <div className="rounded border border-slate-800 p-2">
                  <p className="text-slate-400">Channel</p>
                  <p>{selectedCall.channel}</p>
                </div>
                <div className="rounded border border-slate-800 p-2">
                  <p className="text-slate-400">User Turns</p>
                  <p>{selectedCall.user_turns}</p>
                </div>
                <div className="rounded border border-slate-800 p-2">
                  <p className="text-slate-400">Assistant Turns</p>
                  <p>{selectedCall.assistant_turns}</p>
                </div>
              </div>

              <div className="space-y-2">
                {parseTranscript(selectedCall.transcript_json)
                  .filter((e) => e.event_type === 'transcript')
                  .map((entry, index) => {
                    const isUser = entry.speaker === 'user'
                    return (
                      <div
                        key={`${entry.timestamp}-${index}`}
                        className={`rounded-md border px-3 py-2 text-sm ${
                          isUser
                            ? 'border-cyan-700/50 bg-cyan-900/20'
                            : 'border-lime-700/50 bg-lime-900/20'
                        }`}
                      >
                        <div className="flex justify-between text-xs mb-1">
                          <span className="font-semibold">{isUser ? 'Caller' : 'AI Agent'}</span>
                          <span className="text-slate-400">
                            {entry.timestamp ? new Date(entry.timestamp).toLocaleTimeString() : ''}
                          </span>
                        </div>
                        <p className="whitespace-pre-wrap">{entry.text}</p>
                      </div>
                    )
                  })}
                {parseTranscript(selectedCall.transcript_json).filter((e) => e.event_type === 'transcript').length === 0 && (
                  <p className="text-sm text-slate-400">No transcript messages available for this call.</p>
                )}
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  )
}
