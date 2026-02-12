import React from 'react'
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import { Toaster } from 'react-hot-toast'
import CustomerSelection from './pages/CustomerSelection'
import BookingPage from './pages/BookingPage'
import VoiceDemo from './pages/VoiceDemo'
import SiteMenu from './components/SiteMenu'
import DbatLandingPage from './pages/DbatLandingPage'
import AdminLayout from './components/admin/AdminLayout'
import AdminDashboard from './pages/admin/AdminDashboard'
import AdminBookings from './pages/admin/AdminBookings'
import AdminCalendar from './pages/admin/AdminCalendar'
import AdminCalls from './pages/admin/AdminCalls'

function App() {
  return (
    <Router>
      <div className="min-h-screen bg-gray-50">
        <SiteMenu />
        <Routes>
          <Route path="/" element={<CustomerSelection />} />
          <Route path="/booking" element={<CustomerSelection />} />
          <Route path="/landing/dbat-pearl" element={<DbatLandingPage />} />
          <Route path="/booking/dbat_pearl/landing" element={<DbatLandingPage />} />
          <Route path="/booking/:customerId" element={<BookingPage />} />
          <Route path="/demo/:customerId" element={<VoiceDemo />} />
          <Route path="/booking/demo/:customerId" element={<VoiceDemo />} />
          <Route path="/booking/admin" element={<AdminLayout />}>
            <Route index element={<AdminDashboard />} />
            <Route path="bookings" element={<AdminBookings />} />
            <Route path="calendar" element={<AdminCalendar />} />
            <Route path="calls" element={<AdminCalls />} />
          </Route>
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
        <Toaster position="top-center" />
      </div>
    </Router>
  )
}

export default App
