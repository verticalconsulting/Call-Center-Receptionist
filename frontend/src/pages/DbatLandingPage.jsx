import React from 'react'
import { Link } from 'react-router-dom'
import { CalendarDays, CheckCircle2, Image as ImageIcon, MessageSquareQuote, PhoneCall } from 'lucide-react'

const campFlyers = [
  {
    id: 'spring-break-hitting',
    title: 'Spring Break Hitting Camp',
    date: 'March 18-20, 2026',
    age: 'Ages 8-13',
    image:
      'https://images.unsplash.com/photo-1518604666860-9ed391f76460?auto=format&fit=crop&w=1200&q=80',
  },
  {
    id: 'summer-skills-clinic',
    title: 'Summer Skills Clinic',
    date: 'June 8-12, 2026',
    age: 'Ages 10-16',
    image:
      'https://images.unsplash.com/photo-1461896836934-ffe607ba8211?auto=format&fit=crop&w=1200&q=80',
  },
  {
    id: 'elite-catching-camp',
    title: 'Elite Catching Camp',
    date: 'July 15-16, 2026',
    age: 'Ages 11-17',
    image:
      'https://images.unsplash.com/photo-1471295253337-3ceaaedca402?auto=format&fit=crop&w=1200&q=80',
  },
]

const partyPackages = [
  {
    name: 'Rookie Package',
    price: '$299',
    details: ['90-minute cage rental', 'Up to 12 kids', 'Private party host', 'Birthday shoutout'],
  },
  {
    name: 'All-Star Package',
    price: '$449',
    details: ['2-hour party experience', 'Up to 20 kids', 'Coach-led games', 'Reserved party area'],
    featured: true,
  },
  {
    name: 'MVP Package',
    price: '$649',
    details: ['2.5-hour premium event', 'Up to 28 kids', 'Skills challenge + awards', 'Photo backdrop + setup'],
  },
]

const partyPhotos = [
  'https://images.unsplash.com/photo-1530541930197-ff16ac917b0e?auto=format&fit=crop&w=900&q=80',
  'https://images.unsplash.com/photo-1557804506-669a67965ba0?auto=format&fit=crop&w=900&q=80',
  'https://images.unsplash.com/photo-1544717302-de2939b7ef71?auto=format&fit=crop&w=900&q=80',
  'https://images.unsplash.com/photo-1511988617509-a57c8a288659?auto=format&fit=crop&w=900&q=80',
  'https://images.unsplash.com/photo-1527525443983-6e60c75fff46?auto=format&fit=crop&w=900&q=80',
  'https://images.unsplash.com/photo-1511632765486-a01980e01a18?auto=format&fit=crop&w=900&q=80',
]

const reviews = [
  {
    name: 'Amanda R.',
    text: 'The party was organized from start to finish. The kids were active the whole time and the staff made it easy for parents.',
  },
  {
    name: 'Chris M.',
    text: 'Our son still talks about his birthday at D-BAT. Booking was simple and the team handled every detail.',
  },
  {
    name: 'Jasmine T.',
    text: 'Camp coaches were great with all skill levels. My daughter came home excited and more confident every day.',
  },
]

export default function DbatLandingPage() {
  return (
    <div className="min-h-screen bg-slate-950 text-slate-100">
      <section className="relative overflow-hidden border-b border-slate-800">
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_top_right,_rgba(132,204,22,0.22),_transparent_45%),radial-gradient(circle_at_bottom_left,_rgba(56,189,248,0.18),_transparent_45%)]" />
        <div className="relative max-w-7xl mx-auto px-4 py-16 md:py-24">
          <p className="text-lime-400 font-medium tracking-wide uppercase text-xs mb-3">D-BAT Pearl</p>
          <h1 className="text-4xl md:text-6xl font-bold leading-tight max-w-3xl">
            Epic Birthday Parties. Game-Changing Skills Camps.
          </h1>
          <p className="text-slate-300 mt-5 max-w-2xl">
            Train hard. Celebrate big. Memories—and results—that last.
          </p>
          <div className="flex flex-wrap gap-3 mt-8">
            <Link
              to="/booking/dbat_pearl"
              className="px-5 py-3 rounded-md bg-lime-500 text-black font-semibold hover:bg-lime-400"
            >
              Book a Party
            </Link>
            <Link
              to="/demo/dbat_pearl"
              className="px-5 py-3 rounded-md border border-slate-600 hover:bg-slate-800"
            >
              Talk to Chip AI
            </Link>
            <a href="tel:+16015551234" className="px-5 py-3 rounded-md border border-slate-600 hover:bg-slate-800">
              Call Front Desk
            </a>
          </div>
        </div>
      </section>

      <section className="max-w-7xl mx-auto px-4 py-12 md:py-16">
        <div className="flex items-center gap-2 mb-5">
          <CalendarDays className="w-5 h-5 text-lime-400" />
          <h2 className="text-2xl md:text-3xl font-bold">Upcoming Camp Flyers</h2>
        </div>
        <div className="grid md:grid-cols-3 gap-4">
          {campFlyers.map((camp) => (
            <article key={camp.id} className="rounded-xl overflow-hidden border border-slate-800 bg-slate-900/60">
              <img src={camp.image} alt={camp.title} className="w-full h-44 object-cover" />
              <div className="p-4">
                <h3 className="font-semibold">{camp.title}</h3>
                <p className="text-sm text-slate-300 mt-1">{camp.date}</p>
                <p className="text-sm text-slate-400">{camp.age}</p>
                <button className="mt-4 w-full text-sm py-2 rounded-md border border-slate-700 hover:bg-slate-800">
                  View Flyer
                </button>
              </div>
            </article>
          ))}
        </div>
      </section>

      <section className="max-w-7xl mx-auto px-4 py-12 md:py-16 border-t border-slate-800">
        <div className="flex items-center gap-2 mb-5">
          <CheckCircle2 className="w-5 h-5 text-lime-400" />
          <h2 className="text-2xl md:text-3xl font-bold">Birthday Party Packages</h2>
        </div>
        <div className="grid md:grid-cols-3 gap-4">
          {partyPackages.map((pkg) => (
            <article
              key={pkg.name}
              className={`rounded-xl border p-5 ${pkg.featured ? 'border-lime-500 bg-lime-500/10' : 'border-slate-800 bg-slate-900/60'}`}
            >
              <p className="text-sm uppercase tracking-wide text-slate-300">{pkg.name}</p>
              <p className="text-3xl font-bold mt-2">{pkg.price}</p>
              <ul className="mt-4 space-y-2 text-sm text-slate-300">
                {pkg.details.map((detail) => (
                  <li key={detail} className="flex items-start gap-2">
                    <span className="text-lime-400 mt-0.5">•</span>
                    <span>{detail}</span>
                  </li>
                ))}
              </ul>
              <Link
                to="/booking/dbat_pearl"
                className="mt-5 inline-block w-full text-center py-2 rounded-md bg-slate-800 hover:bg-slate-700"
              >
                Select Package
              </Link>
            </article>
          ))}
        </div>
      </section>

      <section className="max-w-7xl mx-auto px-4 py-12 md:py-16 border-t border-slate-800">
        <div className="flex items-center gap-2 mb-5">
          <ImageIcon className="w-5 h-5 text-lime-400" />
          <h2 className="text-2xl md:text-3xl font-bold">Photos From Past Parties</h2>
        </div>
        <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
          {partyPhotos.map((photo) => (
            <img
              key={photo}
              src={photo}
              alt="Past D-BAT party event"
              className="w-full h-40 md:h-56 object-cover rounded-lg border border-slate-800"
            />
          ))}
        </div>
      </section>

      <section className="max-w-7xl mx-auto px-4 py-12 md:py-16 border-t border-slate-800">
        <div className="flex items-center gap-2 mb-5">
          <MessageSquareQuote className="w-5 h-5 text-lime-400" />
          <h2 className="text-2xl md:text-3xl font-bold">Customer Reviews</h2>
        </div>
        <div className="grid md:grid-cols-3 gap-4">
          {reviews.map((review) => (
            <article key={review.name} className="rounded-xl border border-slate-800 bg-slate-900/60 p-4">
              <p className="text-sm text-slate-200">"{review.text}"</p>
              <p className="mt-4 text-sm font-semibold text-lime-400">{review.name}</p>
            </article>
          ))}
        </div>
      </section>

      <section className="border-t border-slate-800">
        <div className="max-w-7xl mx-auto px-4 py-12 md:py-16">
          <div className="rounded-2xl border border-lime-500/40 bg-gradient-to-r from-lime-500/15 to-cyan-500/10 p-6 md:p-8 flex flex-col md:flex-row md:items-center md:justify-between gap-4">
            <div>
              <h3 className="text-2xl font-bold">Ready to reserve your date?</h3>
              <p className="text-slate-300 mt-1">Book online or call us now and we will lock in your preferred time.</p>
            </div>
            <div className="flex flex-wrap gap-3">
              <Link to="/booking/dbat_pearl" className="px-5 py-3 rounded-md bg-lime-500 text-black font-semibold hover:bg-lime-400">
                Book Now
              </Link>
              <a href="tel:+16015551234" className="px-5 py-3 rounded-md border border-slate-600 hover:bg-slate-800 inline-flex items-center gap-2">
                <PhoneCall className="w-4 h-4" />
                Call D-BAT
              </a>
            </div>
          </div>
        </div>
      </section>
    </div>
  )
}
