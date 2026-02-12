import React from 'react'
import { useNavigate } from 'react-router-dom'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Calendar, Phone, Building2 } from 'lucide-react'

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
                  onClick={() => navigate(`/booking/${customer.id}`)}
                >
                  Book Online
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
    </div>
  )
}
