# Call Center Booking UI

Modern React-based booking interface for the Call Center Voice Agent Accelerator, featuring customer-specific booking forms and integrated voice agent demo.

## Features

- **Multi-Customer Support**: Select from different customer services (D-BAT Pearl, Mercy House, etc.)
- **Online Booking Forms**:
  - Birthday party reservations for D-BAT Pearl
  - Camp registration with date selection
- **Voice Agent Demo**: Test the AI voice agent directly in the browser with WebSocket integration
- **Responsive Design**: Mobile-friendly interface built with Tailwind CSS
- **Modern UI**: shadcn/ui components with Radix UI primitives

## Technology Stack

- **Framework**: Vite 6.1 + React 18
- **Styling**: Tailwind CSS
- **UI Components**: Radix UI + shadcn/ui
- **Routing**: React Router DOM v6
- **Forms**: React Hook Form + Zod validation
- **Notifications**: React Hot Toast
- **Animations**: Framer Motion
- **Date Handling**: date-fns + React Day Picker

## Development Setup

### Prerequisites

- Node.js 18+
- npm or yarn
- Python server running on port 8000 (see `../server/`)

### Installation

```bash
# Install dependencies
npm install

# Start development server
npm run dev
```

The dev server runs on `http://localhost:3000` and proxies WebSocket requests to `localhost:8000`.

### Build for Production

```bash
# Build the app
npm run build
```

This builds the app into `../server/static/booking/` so the Python server can serve it at `/booking`.

## Project Structure

```
frontend/
├── src/
│   ├── components/
│   │   ├── ui/              # shadcn/ui components (Button, Card, Input, etc.)
│   │   └── booking/         # Booking form components
│   │       ├── BirthdayPartyForm.jsx
│   │       └── CampRegistrationForm.jsx
│   ├── pages/               # Page components
│   │   ├── CustomerSelection.jsx  # Landing page with customer cards
│   │   ├── BookingPage.jsx        # Booking forms container
│   │   └── VoiceDemo.jsx          # Voice agent demo with WebSocket
│   ├── hooks/
│   │   └── useVoiceAgent.js       # WebSocket voice agent hook
│   ├── lib/
│   │   └── utils.js               # Utility functions (cn, etc.)
│   ├── App.jsx              # Root component with routing
│   ├── main.jsx             # React entry point
│   └── index.css            # Global styles with Tailwind
├── public/
│   └── audio-processor.js   # Audio worklet for voice streaming
├── package.json
├── vite.config.js           # Vite configuration
└── tailwind.config.js       # Tailwind CSS configuration
```

## Usage

### Customer Selection

Visit `http://localhost:3000` to see the customer selection page with three services:

1. **D-BAT Pearl**: Birthday party and camp bookings
2. **Mercy House & Sacred Grove**: Intake services
3. **Customer XYZ Healthcare**: Healthcare appointments

### Booking Flow

1. Select a customer from the home page
2. Choose "Book Online" to fill out forms or "Try Voice Agent" to speak with AI
3. For D-BAT Pearl bookings:
   - **Birthday Party**: Select date, enter contact info, specify number of kids
   - **Camp Registration**: Select multiple dates, choose sport and experience level

### Voice Agent Demo

The voice demo page:
- Connects to the Python backend via WebSocket
- Uses Web Audio API for real-time audio streaming
- Automatically routes to customer-specific agents based on URL

**WebSocket URL Pattern**: `/web/ws?customerId={customerId}`

## Key Components

### useVoiceAgent Hook

Manages WebSocket connection, audio streaming, and transcript display:

```jsx
const { isConnected, isListening, transcript, connect, disconnect } = useVoiceAgent(customerId)
```

### Form Components

Both booking forms use:
- React Hook Form for state management
- Zod for validation
- React Day Picker for calendar selection
- Toast notifications for feedback

## Integration with Python Server

The frontend integrates with the Python server (Quart) in two ways:

1. **WebSocket Voice Streaming**: `/web/ws?customerId=<customer>`
2. **Static File Serving**: Server serves built React app at `/booking`

The server routes are defined in `server/server.py`:

```python
@app.route("/booking")
@app.route("/booking/<path:path>")
async def booking_app(path=""):
    return await app.send_static_file("booking/index.html")
```

## Customization

### Adding a New Customer

1. Update `customer_routing.json` in the server
2. Add customer to the `customers` array in `CustomerSelection.jsx`
3. Optionally create custom booking forms in `src/components/booking/`

### Styling

The app uses CSS variables defined in `index.css` for theming. Modify the `:root` section to change colors:

```css
:root {
  --primary: 221.2 83.2% 53.3%;
  --accent: 210 40% 96.1%;
  /* etc. */
}
```

## Troubleshooting

**WebSocket connection fails**:
- Ensure Python server is running on port 8000
- Check Vite proxy configuration in `vite.config.js`
- Verify `customerId` parameter is being passed correctly

**Build fails**:
- Run `npm install` to ensure all dependencies are installed
- Check Node.js version (18+ required)

**Forms not submitting**:
- Check browser console for validation errors
- Ensure all required fields are filled
- Verify date selection for calendar fields

## Development Notes

- The audio-processor.js file in `public/` handles PCM audio streaming via AudioWorklet
- WebSocket binary messages are PCM audio at 24kHz sample rate
- The useVoiceAgent hook manages audio context lifecycle and cleanup
- Forms currently log to console; integrate with backend API as needed

## Next Steps

- Connect booking forms to backend API endpoints
- Add booking confirmation emails
- Implement calendar availability checking
- Add analytics tracking
- Enhance error handling and offline support
