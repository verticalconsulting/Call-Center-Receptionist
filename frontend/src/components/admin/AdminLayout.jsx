import React from 'react'
import { Link, Outlet, useLocation } from 'react-router-dom'
import { BarChart3, CalendarDays, ClipboardList, PhoneCall } from 'lucide-react'

const navItems = [
  { to: '/booking/admin', label: 'Dashboard', icon: BarChart3 },
  { to: '/booking/admin/bookings', label: 'Bookings', icon: ClipboardList },
  { to: '/booking/admin/calendar', label: 'Calendar', icon: CalendarDays },
  { to: '/booking/admin/calls', label: 'Calls', icon: PhoneCall },
]

export default function AdminLayout() {
  const location = useLocation()

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100">
      <div className="max-w-7xl mx-auto px-4 py-6">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-2xl font-bold">AI Receptionist Admin</h1>
            <p className="text-sm text-slate-400">Bookings, schedule, calls, and revenue reporting</p>
          </div>
          <Link
            to="/booking"
            className="text-sm px-3 py-2 rounded-md border border-slate-700 hover:bg-slate-800"
          >
            Back to Services
          </Link>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-[220px_1fr] gap-4">
          <aside className="rounded-xl border border-slate-800 bg-slate-900/70 p-2 h-fit">
            <nav className="space-y-1">
              {navItems.map((item) => {
                const Icon = item.icon
                const active = location.pathname === item.to
                return (
                  <Link
                    key={item.to}
                    to={item.to}
                    className={`flex items-center gap-2 px-3 py-2 rounded-md text-sm transition ${
                      active ? 'bg-lime-500 text-black font-medium' : 'text-slate-300 hover:bg-slate-800'
                    }`}
                  >
                    <Icon className="w-4 h-4" />
                    {item.label}
                  </Link>
                )
              })}
            </nav>
          </aside>

          <main className="rounded-xl border border-slate-800 bg-slate-900/70 p-4">
            <Outlet />
          </main>
        </div>
      </div>
    </div>
  )
}
