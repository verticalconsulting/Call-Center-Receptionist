import React, { useState } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import * as z from 'zod'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Calendar } from '@/components/ui/calendar'
import toast from 'react-hot-toast'
import { format } from 'date-fns'

const partySchema = z.object({
  parentName: z.string().min(2, 'Parent name is required'),
  phoneNumber: z.string().min(10, 'Valid phone number required'),
  childName: z.string().min(2, 'Child name is required'),
  childAge: z.string().min(1, 'Child age is required'),
  numberOfKids: z.string().min(1, 'Number of kids is required'),
  preferredTime: z.string().min(1, 'Preferred time is required'),
  additionalNotes: z.string().optional(),
})

export default function BirthdayPartyForm() {
  const [selectedDate, setSelectedDate] = useState(null)
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
    reset,
  } = useForm({
    resolver: zodResolver(partySchema),
  })

  const onSubmit = async (data) => {
    if (!selectedDate) {
      toast.error('Please select a date for the party')
      return
    }

    const bookingData = {
      ...data,
      preferredDate: format(selectedDate, 'yyyy-MM-dd'),
      bookingType: 'birthday_party',
    }

    console.log('Birthday Party Booking:', bookingData)

    // Simulate API call
    await new Promise((resolve) => setTimeout(resolve, 1000))

    toast.success('Birthday party booking submitted! We will call you to confirm.')
    reset()
    setSelectedDate(null)
  }

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-6 mt-6">
      <div className="grid md:grid-cols-2 gap-4">
        <div className="space-y-2">
          <Label htmlFor="parentName">Parent/Guardian Name *</Label>
          <Input
            id="parentName"
            {...register('parentName')}
            placeholder="John Doe"
          />
          {errors.parentName && (
            <p className="text-sm text-red-500">{errors.parentName.message}</p>
          )}
        </div>

        <div className="space-y-2">
          <Label htmlFor="phoneNumber">Phone Number *</Label>
          <Input
            id="phoneNumber"
            {...register('phoneNumber')}
            placeholder="(555) 123-4567"
            type="tel"
          />
          {errors.phoneNumber && (
            <p className="text-sm text-red-500">{errors.phoneNumber.message}</p>
          )}
        </div>
      </div>

      <div className="grid md:grid-cols-2 gap-4">
        <div className="space-y-2">
          <Label htmlFor="childName">Child's Name *</Label>
          <Input
            id="childName"
            {...register('childName')}
            placeholder="Sarah Doe"
          />
          {errors.childName && (
            <p className="text-sm text-red-500">{errors.childName.message}</p>
          )}
        </div>

        <div className="space-y-2">
          <Label htmlFor="childAge">Child's Age *</Label>
          <Input
            id="childAge"
            {...register('childAge')}
            placeholder="8"
            type="number"
          />
          {errors.childAge && (
            <p className="text-sm text-red-500">{errors.childAge.message}</p>
          )}
        </div>
      </div>

      <div className="space-y-2">
        <Label>Preferred Party Date *</Label>
        <Calendar
          mode="single"
          selected={selectedDate}
          onSelect={setSelectedDate}
          disabled={(date) => date < new Date()}
          className="rounded-md border"
        />
        {selectedDate && (
          <p className="text-sm text-green-600">
            Selected: {format(selectedDate, 'MMMM d, yyyy')}
          </p>
        )}
      </div>

      <div className="grid md:grid-cols-2 gap-4">
        <div className="space-y-2">
          <Label htmlFor="preferredTime">Preferred Time *</Label>
          <Input
            id="preferredTime"
            {...register('preferredTime')}
            placeholder="2:00 PM"
            type="time"
          />
          {errors.preferredTime && (
            <p className="text-sm text-red-500">{errors.preferredTime.message}</p>
          )}
        </div>

        <div className="space-y-2">
          <Label htmlFor="numberOfKids">Number of Kids Attending *</Label>
          <Input
            id="numberOfKids"
            {...register('numberOfKids')}
            placeholder="10"
            type="number"
          />
          {errors.numberOfKids && (
            <p className="text-sm text-red-500">{errors.numberOfKids.message}</p>
          )}
        </div>
      </div>

      <div className="space-y-2">
        <Label htmlFor="additionalNotes">Additional Notes</Label>
        <textarea
          id="additionalNotes"
          {...register('additionalNotes')}
          placeholder="Any special requests or questions about cages, instructors, or add-ons?"
          className="w-full min-h-24 px-3 py-2 border rounded-md"
        />
      </div>

      <Button type="submit" className="w-full" disabled={isSubmitting}>
        {isSubmitting ? 'Submitting...' : 'Submit Party Booking'}
      </Button>

      <p className="text-sm text-gray-500 text-center">
        We'll call you within 24 hours to confirm availability and finalize details.
      </p>
    </form>
  )
}
