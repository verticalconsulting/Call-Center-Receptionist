# Frontend Setup Guide

Quick start guide for the React booking UI.

## Quick Start

```bash
cd frontend
npm install
npm run dev
```

Visit `http://localhost:3000` to see the booking interface.

## What Was Built

A modern React booking interface with:

✅ **Customer Selection Page**: Landing page showing all available services
✅ **Voice Agent Demo**: Browser-based voice client with WebSocket integration
✅ **D-BAT Pearl Booking Forms**:
  - Birthday party reservations
  - Camp registration
✅ **Calendar Integration**: Date selection with react-day-picker
✅ **Form Validation**: Zod schemas with React Hook Form
✅ **Responsive Design**: Mobile-friendly Tailwind CSS
✅ **Component Library**: shadcn/ui with Radix UI primitives

## Architecture

### Components Imported from Evelina

The following UI components were copied from the Evelina AI Receptionist project:

- Button, Card, Input, Label (form basics)
- Calendar (date picker)
- Select, Tabs, Dialog, Toast (advanced UI)
- Utils library (cn helper for className merging)

### Custom Components Built

**Pages:**
- `CustomerSelection.jsx` - Landing page with customer cards
- `BookingPage.jsx` - Container for booking forms with tabs
- `VoiceDemo.jsx` - Voice agent demo with visual indicators

**Booking Components:**
- `BirthdayPartyForm.jsx` - Party booking with date/time selection
- `CampRegistrationForm.jsx` - Camp registration with multi-date selection

**Hooks:**
- `useVoiceAgent.js` - WebSocket connection manager with audio streaming

## Integration Points

### WebSocket Voice Client

The `useVoiceAgent` hook connects to:
```
/web/ws?customerId={customerId}
```

This routes to the appropriate voice agent based on customer configuration.

### Audio Streaming

- Uses Web Audio API with AudioWorkletNode
- PCM audio at 24kHz sample rate
- Bidirectional streaming (microphone input + speaker output)

### Server Routes

The Python server (Quart) serves:
- `/` - Simple voice demo (legacy static HTML)
- `/booking` - React booking app (SPA with client-side routing)
- `/web/ws` - WebSocket for voice streaming
- `/acs/ws` - WebSocket for ACS phone calls

## Build Process

```bash
npm run build
```

Builds to: `../server/static/booking/`

The Python server automatically serves this at `/booking`.

## Development Workflow

1. **Frontend dev**: Run `npm run dev` in `frontend/` (port 3000)
2. **Backend dev**: Run `uv run server.py` in `server/` (port 8000)
3. **Edit code**: Changes hot-reload in dev mode
4. **Test voice**: Use `/demo/:customerId` route to test voice agents
5. **Production build**: Run `npm run build` when ready

## Environment Notes

- No `.env` file needed for frontend (proxies to backend)
- Backend `.env` contains Azure credentials (see `server/.env-sample.txt`)
- WebSocket connections auto-detect protocol (ws:// vs wss://)

## Next Steps

### Immediate:
- [ ] Test the frontend by running `npm install` and `npm run dev`
- [ ] Verify voice agent integration works
- [ ] Test booking forms submit correctly

### Future Enhancements:
- [ ] Connect forms to backend API (save to database)
- [ ] Add email confirmation for bookings
- [ ] Implement real calendar availability checking
- [ ] Add payment integration for birthday parties
- [ ] Create admin dashboard for viewing bookings
- [ ] Add SMS reminders 2-3 days before events

## Troubleshooting

**Port 3000 in use?**
```bash
# Change port in vite.config.js:
server: {
  port: 3001,  // Use different port
}
```

**WebSocket not connecting?**
- Ensure backend is running on port 8000
- Check browser console for errors
- Verify proxy configuration in `vite.config.js`

**Build fails?**
- Delete `node_modules` and `package-lock.json`
- Run `npm install` again
- Ensure Node.js 18+ is installed

**Forms not validating?**
- Check Zod schema in form components
- Ensure all required fields have values
- Look for validation errors in browser console

## Tech Stack Reference

| Category | Technology | Purpose |
|----------|-----------|---------|
| Framework | Vite 6 + React 18 | Fast dev server and build tool |
| Routing | React Router v6 | Client-side navigation |
| Styling | Tailwind CSS | Utility-first styling |
| UI Components | Radix UI + shadcn/ui | Accessible component primitives |
| Forms | React Hook Form | Form state management |
| Validation | Zod | Type-safe schema validation |
| Dates | date-fns + react-day-picker | Date formatting and selection |
| Notifications | react-hot-toast | Toast notifications |
| Animation | Framer Motion | UI animations |

## File Organization

```
frontend/
├── src/
│   ├── components/
│   │   ├── ui/              # Reusable UI components (from Evelina)
│   │   │   ├── button.jsx
│   │   │   ├── card.jsx
│   │   │   ├── calendar.jsx
│   │   │   └── ...
│   │   └── booking/         # Booking-specific components
│   │       ├── BirthdayPartyForm.jsx
│   │       └── CampRegistrationForm.jsx
│   ├── pages/               # Route components
│   │   ├── CustomerSelection.jsx
│   │   ├── BookingPage.jsx
│   │   └── VoiceDemo.jsx
│   ├── hooks/               # Custom React hooks
│   │   └── useVoiceAgent.js
│   ├── lib/                 # Utilities
│   │   └── utils.js         # cn() helper
│   ├── App.jsx              # Root component
│   ├── main.jsx             # React entry point
│   └── index.css            # Global styles
├── public/
│   └── audio-processor.js   # AudioWorklet for PCM streaming
├── package.json
├── vite.config.js
├── tailwind.config.js
├── postcss.config.js
├── index.html
├── README.md                # Detailed documentation
└── SETUP.md                 # This file
```

## Contributing

When adding new features:

1. **New customers**: Add to `CustomerSelection.jsx` and create prompt in `server/prompts/`
2. **New forms**: Create in `src/components/booking/` following existing patterns
3. **New pages**: Add to `src/pages/` and update routes in `App.jsx`
4. **New UI components**: Add to `src/components/ui/` (prefer using existing shadcn components)

Keep forms simple and focused. The voice agent can handle complex interactions.
