import React, { useEffect, useState } from 'react'

export default function AdminBookings() {
  const [items, setItems] = useState([])
  const [error, setError] = useState('')

  useEffect(() => {
    const load = async () => {
      try {
        const res = await fetch('/api/admin/bookings?limit=500')
        const data = await res.json()
        if (!res.ok) throw new Error(data.error || 'Failed loading bookings')
        setItems(data.items || [])
      } catch (err) {
        setError(err.message || 'Failed loading bookings')
      }
    }
    load()
  }, [])

  if (error) return <div className="text-red-400">{error}</div>

  return (
    <div>
      <h2 className="text-lg font-semibold mb-3">Bookings</h2>
      <div className="overflow-auto rounded-lg border border-slate-800">
        <table className="min-w-full text-sm">
          <thead className="bg-slate-950">
            <tr className="text-left text-slate-300">
              <th className="p-3">Date</th>
              <th className="p-3">Customer</th>
              <th className="p-3">Type</th>
              <th className="p-3">Parent</th>
              <th className="p-3">Child</th>
              <th className="p-3">Revenue</th>
              <th className="p-3">Status</th>
            </tr>
          </thead>
          <tbody>
            {items.length === 0 && (
              <tr>
                <td className="p-3 text-slate-400" colSpan={7}>
                  No bookings found.
                </td>
              </tr>
            )}
            {items.map((b) => (
              <tr key={b.booking_id} className="border-t border-slate-800">
                <td className="p-3">{new Date(b.start_time_utc).toLocaleString()}</td>
                <td className="p-3">{b.customer_id}</td>
                <td className="p-3">{b.booking_type}</td>
                <td className="p-3">{b.parent_name}</td>
                <td className="p-3">{b.child_name}</td>
                <td className="p-3 text-lime-400">${Number(b.estimated_revenue || 0).toFixed(2)}</td>
                <td className="p-3">{b.status}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

