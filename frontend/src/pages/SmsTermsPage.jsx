import React from 'react'

export default function SmsTermsPage() {
  return (
    <main className="bg-slate-950 text-slate-100 min-h-[70vh]">
      <div className="max-w-3xl mx-auto px-4 py-10 space-y-4">
        <h1 className="text-3xl font-black">SMS Terms</h1>
        <p className="text-slate-300">
          By opting in, you consent to receive recurring text messages from D-BAT Pearl for bookings, reminders, camps,
          birthday events, and promotions.
        </p>
        <p className="text-slate-300">Message frequency varies. Msg &amp; data rates may apply.</p>
        <p className="text-slate-300">Reply STOP to unsubscribe. Reply HELP for help.</p>
        <p className="text-slate-300">
          Consent is not a condition of purchase. Carriers are not liable for delayed or undelivered messages.
        </p>
      </div>
    </main>
  )
}

