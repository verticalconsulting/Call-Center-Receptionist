import React from 'react'
import { useNavigate } from 'react-router-dom'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Calendar, Phone, Building2, LayoutDashboard } from 'lucide-react'

const customers = [
  {
    id: 'dbat_pearl',
    name: 'D-BAT Pearl',
    description: 'Birthday parties and baseball/softball camp bookings',
    icon: Calendar,
    color: 'bg-blue-500',
  },
  {
    id: 'mercy_house',
    name: 'Mercy House & Sacred Grove',
    description: 'Substance abuse recovery intake services',
    icon: Building2,
    color: 'bg-green-500',
  },
  {
    id: 'customer_xyz',
    name: 'Customer XYZ Healthcare',
    description: 'Healthcare appointment scheduling',
    icon: Phone,
    color: 'bg-purple-500',
  },
]

export default function CustomerSelection() {
  const navigate = useNavigate()

  return (
    <div className="container max-w-6xl mx-auto px-4 py-12">
      <div className="text-center mb-12">
        <img
          src="https://imagedelivery.net/dXRounTcgmfhZwbsZCZLTw/19208c5d-9371-42de-436c-fbe365f38900/small"
          alt="D-BAT Pearl logo"
          className="mx-auto w-36 md:w-48 h-auto mb-5"
        />
        <h1 className="text-4xl font-bold mb-4">Welcome to Call Center Services</h1>
        <p className="text-lg text-gray-600">Select a service to get started</p>
      </div>

      <div className="grid md:grid-cols-3 gap-6">
        {customers.map((customer) => {
          const Icon = customer.icon
          return (
            <Card key={customer.id} className="hover:shadow-lg transition-shadow">
              <CardHeader>
                <div className={`w-12 h-12 rounded-full ${customer.color} flex items-center justify-center mb-4`}>
                  <Icon className="w-6 h-6 text-white" />
                </div>
                <CardTitle>{customer.name}</CardTitle>
                <CardDescription>{customer.description}</CardDescription>
              </CardHeader>
              <CardContent className="space-y-2">
                <Button
                  className="w-full"
                  onClick={() =>
                    customer.id === 'dbat_pearl'
                      ? navigate('/landing/dbat-pearl')
                      : navigate(`/booking/${customer.id}`)
                  }
                >
                  {customer.id === 'dbat_pearl' ? 'View Landing Page' : 'Book Online'}
                </Button>
                <Button
                  variant="outline"
                  className="w-full"
                  onClick={() => navigate(`/demo/${customer.id}`)}
                >
                  Try Voice Agent
                </Button>
              </CardContent>
            </Card>
          )
        })}
      </div>

      <Card className="mt-8 border-lime-500/40 bg-lime-500/5">
        <CardHeader>
          <div className="w-12 h-12 rounded-full bg-lime-500 flex items-center justify-center mb-4">
            <LayoutDashboard className="w-6 h-6 text-black" />
          </div>
          <CardTitle>Admin Console</CardTitle>
          <CardDescription>View bookings, schedule, calls, and AI receptionist revenue reports.</CardDescription>
        </CardHeader>
        <CardContent>
          <Button className="w-full md:w-auto" onClick={() => navigate('/booking/admin')}>
            Open Admin Dashboard
          </Button>
        </CardContent>
      </Card>
    </div>
  )
}
