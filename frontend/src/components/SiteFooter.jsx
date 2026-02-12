import React from 'react'
import { Link } from 'react-router-dom'

export default function SiteFooter() {
  return (
    <footer className="border-t border-slate-800 bg-slate-950 text-slate-300">
      <div className="max-w-7xl mx-auto px-4 py-8 grid gap-6 md:grid-cols-2">
        <section className="space-y-2">
          <h3 className="text-sm font-semibold text-white">SMS Opt-In</h3>
          <p className="text-sm text-slate-400">
            Text <span className="font-semibold text-lime-400">CAMPS</span> to{' '}
            <span className="font-semibold text-lime-400">+1 (833) 793-9008</span> for camp alerts.
          </p>
          <p className="text-xs text-slate-500">Msg &amp; data rates may apply. Reply STOP to opt out.</p>
        </section>
        <section className="space-y-2 md:text-right">
          <h3 className="text-sm font-semibold text-white">Compliance Links</h3>
          <div className="flex flex-wrap gap-3 md:justify-end text-sm">
            <Link className="hover:text-lime-400" to="/booking/sms-opt-in">SMS Opt-In</Link>
            <Link className="hover:text-lime-400" to="/booking/privacy">Privacy Policy</Link>
            <Link className="hover:text-lime-400" to="/booking/sms-terms">SMS Terms</Link>
          </div>
        </section>
      </div>
    </footer>
  )
}
