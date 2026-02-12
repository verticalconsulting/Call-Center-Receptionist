import React, { useEffect, useMemo, useState } from 'react'

export default function AdminCalendar() {
  const [items, setItems] = useState([])
  const [error, setError] = useState('')

  useEffect(() => {
    const load = async () => {
      try {
        const res = await fetch('/api/admin/bookings?limit=500')
        const data = await res.json()
        if (!res.ok) throw new Error(data.error || 'Failed loading schedule')
        setItems(data.items || [])
      } catch (err) {
        setError(err.message || 'Failed loading schedule')
      }
    }
    load()
  }, [])

  const grouped = useMemo(() => {
    const map = {}
    for (const booking of items) {
      const day = new Date(booking.start_time_utc).toISOString().slice(0, 10)
      map[day] = map[day] || []
      map[day].push(booking)
    }
    return Object.entries(map).sort((a, b) => a[0].localeCompare(b[0]))
  }, [items])

  if (error) return <div className="text-red-400">{error}</div>

  return (
    <div>
      <h2 className="text-lg font-semibold mb-3">Calendar & Schedule</h2>
      <div className="space-y-4">
        {grouped.length === 0 && <p className="text-slate-400">No scheduled bookings yet.</p>}
        {grouped.map(([day, bookings]) => (
          <section key={day} className="rounded-lg border border-slate-800 bg-slate-950/70 p-3">
            <h3 className="font-medium mb-2">{new Date(day).toLocaleDateString()}</h3>
            <div className="space-y-2">
              {bookings
                .sort((a, b) => a.start_time_utc.localeCompare(b.start_time_utc))
                .map((booking) => (
                  <div
                    key={booking.booking_id}
                    className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-1 text-sm border-b border-slate-800 pb-2"
                  >
                    <div>
                      <p className="font-medium">{booking.child_name} ({booking.booking_type})</p>
                      <p className="text-slate-400">{booking.parent_name} • {booking.customer_id}</p>
                    </div>
                    <div className="text-right">
                      <p>{new Date(booking.start_time_utc).toLocaleTimeString()}</p>
                      <p className="text-lime-400">${Number(booking.estimated_revenue || 0).toFixed(2)}</p>
                    </div>
                  </div>
                ))}
            </div>
          </section>
        ))}
      </div>
    </div>
  )
}

