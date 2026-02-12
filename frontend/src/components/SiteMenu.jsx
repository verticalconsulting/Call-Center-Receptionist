import React from 'react'
import { NavLink, useLocation } from 'react-router-dom'

function resolveHomePath(pathname) {
  return pathname.startsWith('/booking') ? '/booking' : '/'
}

export default function SiteMenu() {
  const location = useLocation()
  const homePath = resolveHomePath(location.pathname)

  const links = [
    { to: homePath, label: 'Services' },
    { to: '/landing/dbat-pearl', label: 'D-BAT Landing' },
    { to: '/booking/dbat_pearl', label: 'Booking' },
    { to: '/booking/sms-opt-in', label: 'SMS Opt-In' },
    { to: '/demo/dbat_pearl', label: 'Voice Demo' },
    { to: '/booking/admin', label: 'Admin' },
    { to: '/booking/admin/bookings', label: 'Bookings' },
    { to: '/booking/admin/calendar', label: 'Calendar' },
    { to: '/booking/admin/calls', label: 'Calls' },
  ]

  return (
    <header className="sticky top-0 z-40 border-b border-slate-800 bg-slate-950/95 backdrop-blur">
      <div className="max-w-7xl mx-auto px-4 py-3">
        <div className="flex flex-wrap items-center gap-3">
          <NavLink to="/booking" className="mr-1 inline-flex items-center">
            <img
              src="https://imagedelivery.net/dXRounTcgmfhZwbsZCZLTw/19208c5d-9371-42de-436c-fbe365f38900/small"
              alt="D-BAT Pearl logo"
              className="h-10 w-auto sm:h-12"
            />
          </NavLink>
          {links.map((link) => (
            <NavLink
              key={`${link.to}-${link.label}`}
              to={link.to}
              className={({ isActive }) =>
                `text-xs sm:text-sm px-3 py-1.5 rounded-md border transition ${
                  isActive
                    ? 'bg-lime-500 border-lime-500 text-black font-semibold'
                    : 'border-slate-700 text-slate-300 hover:bg-slate-800'
                }`
              }
            >
              {link.label}
            </NavLink>
          ))}
        </div>
      </div>
    </header>
  )
}
