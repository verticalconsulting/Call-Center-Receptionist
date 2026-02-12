import React, { useEffect, useState } from 'react'

function StatCard({ label, value, subtitle }) {
  return (
    <div className="rounded-lg border border-slate-800 bg-slate-950/70 p-4">
      <p className="text-xs uppercase tracking-wide text-slate-400">{label}</p>
      <p className="text-2xl font-semibold mt-1">{value}</p>
      {subtitle && <p className="text-xs text-slate-400 mt-1">{subtitle}</p>}
    </div>
  )
}

function TrendBars({ title, data, valueKey, colorClass, emptyLabel, formatter }) {
  const max = Math.max(...data.map((d) => Number(d[valueKey] || 0)), 0)

  return (
    <section className="rounded-lg border border-slate-800 bg-slate-950/70 p-4">
      <h2 className="font-semibold mb-3">{title}</h2>
      {data.length === 0 && <p className="text-sm text-slate-400">{emptyLabel}</p>}
      {data.length > 0 && (
        <div className="space-y-2">
          {data.map((d) => {
            const raw = Number(d[valueKey] || 0)
            const pct = max > 0 ? Math.max(4, Math.round((raw / max) * 100)) : 4
            return (
              <div key={`${title}-${d.day}`} className="grid grid-cols-[70px_1fr_90px] items-center gap-3 text-xs">
                <p className="text-slate-400">{d.day}</p>
                <div className="h-2 rounded bg-slate-800 overflow-hidden">
                  <div className={`h-2 rounded ${colorClass}`} style={{ width: `${pct}%` }} />
                </div>
                <p className="text-right text-slate-200">{formatter(raw)}</p>
              </div>
            )
          })}
        </div>
      )}
    </section>
  )
}

export default function AdminDashboard() {
  const [summary, setSummary] = useState(null)
  const [bookings, setBookings] = useState([])
  const [calls, setCalls] = useState([])
  const [error, setError] = useState('')

  useEffect(() => {
    const load = async () => {
      try {
        const [summaryRes, bookingsRes, callsRes] = await Promise.all([
          fetch('/api/admin/reports/summary?days=30'),
          fetch('/api/admin/bookings?limit=6'),
          fetch('/api/admin/calls?limit=6'),
        ])
        const summaryData = await summaryRes.json()
        const bookingsData = await bookingsRes.json()
        const callsData = await callsRes.json()
        if (!summaryRes.ok) {
          throw new Error(summaryData.error || 'Failed to load summary')
        }
        setSummary(summaryData)
        setBookings(bookingsData.items || [])
        setCalls(callsData.items || [])
      } catch (err) {
        setError(err.message || 'Failed loading dashboard')
      }
    }
    load()
  }, [])

  if (error) return <div className="text-red-400">{error}</div>
  if (!summary) return <div className="text-slate-400">Loading dashboard...</div>

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
        <StatCard label="Revenue (All Time)" value={`$${summary.totalRevenue.toFixed(2)}`} />
        <StatCard label="Revenue (30 Days)" value={`$${summary.revenueInWindow.toFixed(2)}`} />
        <StatCard label="Bookings (30 Days)" value={summary.bookingsInWindow} />
        <StatCard label="Call to Booking" value={`${summary.conversionRate}%`} subtitle={`${summary.callsInWindow} calls in 30 days`} />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <TrendBars
          title="Revenue Trend (30 Days)"
          data={summary.daily || []}
          valueKey="revenue"
          colorClass="bg-lime-500"
          emptyLabel="No revenue yet."
          formatter={(v) => `$${v.toFixed(0)}`}
        />
        <TrendBars
          title="Bookings Trend (30 Days)"
          data={summary.daily || []}
          valueKey="bookings"
          colorClass="bg-cyan-500"
          emptyLabel="No bookings yet."
          formatter={(v) => `${v}`}
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <section className="rounded-lg border border-slate-800 bg-slate-950/70 p-4">
          <h2 className="font-semibold mb-3">Recent Bookings</h2>
          <div className="space-y-2">
            {bookings.length === 0 && <p className="text-sm text-slate-400">No bookings yet.</p>}
            {bookings.map((b) => (
              <div key={b.booking_id} className="flex justify-between text-sm border-b border-slate-800 pb-2">
                <div>
                  <p className="font-medium">{b.child_name}</p>
                  <p className="text-slate-400">{new Date(b.start_time_utc).toLocaleString()}</p>
                </div>
                <p className="text-lime-400">${Number(b.estimated_revenue || 0).toFixed(2)}</p>
              </div>
            ))}
          </div>
        </section>

        <section className="rounded-lg border border-slate-800 bg-slate-950/70 p-4">
          <h2 className="font-semibold mb-3">Recent Calls</h2>
          <div className="space-y-2">
            {calls.length === 0 && <p className="text-sm text-slate-400">No calls yet.</p>}
            {calls.map((c) => (
              <div key={c.call_id} className="flex justify-between text-sm border-b border-slate-800 pb-2">
                <div>
                  <p className="font-medium">{c.customer_id}</p>
                  <p className="text-slate-400">{new Date(c.started_at_utc).toLocaleString()}</p>
                </div>
                <p className="text-slate-300">{Math.round(Number(c.duration_seconds || 0))}s</p>
              </div>
            ))}
          </div>
        </section>
      </div>
    </div>
  )
}
