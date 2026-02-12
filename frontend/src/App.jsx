import React from 'react'
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import { Toaster } from 'react-hot-toast'
import CustomerSelection from './pages/CustomerSelection'
import BookingPage from './pages/BookingPage'
import VoiceDemo from './pages/VoiceDemo'

function App() {
  return (
    <Router>
      <div className="min-h-screen bg-gray-50">
        <Routes>
          <Route path="/" element={<CustomerSelection />} />
          <Route path="/booking/:customerId" element={<BookingPage />} />
          <Route path="/demo/:customerId" element={<VoiceDemo />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
        <Toaster position="top-center" />
      </div>
    </Router>
  )
}

export default App
