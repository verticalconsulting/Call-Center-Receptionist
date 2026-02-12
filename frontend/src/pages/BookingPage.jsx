import React, { useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { ArrowLeft, Calendar, Users } from 'lucide-react'
import BirthdayPartyForm from '@/components/booking/BirthdayPartyForm'
import CampRegistrationForm from '@/components/booking/CampRegistrationForm'

const customerTitles = {
  dbat_pearl: 'D-BAT Pearl',
  mercy_house: 'Mercy House & Sacred Grove',
  customer_xyz: 'Customer XYZ Healthcare',
}

export default function BookingPage() {
  const { customerId } = useParams()
  const navigate = useNavigate()

  return (
    <div className="container max-w-4xl mx-auto px-4 py-8">
      <Button
        variant="ghost"
        className="mb-6"
        onClick={() => navigate('/')}
      >
        <ArrowLeft className="w-4 h-4 mr-2" />
        Back to Services
      </Button>

      <Card>
        <CardHeader>
          <CardTitle className="text-2xl">
            {customerTitles[customerId] || 'Booking'}
          </CardTitle>
          <CardDescription>
            Fill out the form below to make a reservation
          </CardDescription>
        </CardHeader>
        <CardContent>
          {customerId === 'dbat_pearl' ? (
            <Tabs defaultValue="party" className="w-full">
              <TabsList className="grid w-full grid-cols-2">
                <TabsTrigger value="party">
                  <Calendar className="w-4 h-4 mr-2" />
                  Birthday Party
                </TabsTrigger>
                <TabsTrigger value="camp">
                  <Users className="w-4 h-4 mr-2" />
                  Camp Registration
                </TabsTrigger>
              </TabsList>
              <TabsContent value="party">
                <BirthdayPartyForm customerId={customerId} />
              </TabsContent>
              <TabsContent value="camp">
                <CampRegistrationForm customerId={customerId} />
              </TabsContent>
            </Tabs>
          ) : (
            <div className="text-center py-12">
              <p className="text-gray-500 mb-4">
                Online booking is not yet available for this service.
              </p>
              <Button onClick={() => navigate(`/demo/${customerId}`)}>
                Try Voice Agent Instead
              </Button>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
