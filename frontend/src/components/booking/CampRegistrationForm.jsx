import React, { useState } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import * as z from 'zod'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Calendar } from '@/components/ui/calendar'
import toast from 'react-hot-toast'
import { format } from 'date-fns'

const campSchema = z.object({
  parentName: z.string().min(2, 'Parent name is required'),
  phoneNumber: z.string().min(10, 'Valid phone number required'),
  smsOptIn: z.boolean().optional(),
  childName: z.string().min(2, 'Child name is required'),
  childAge: z.string().min(1, 'Child age is required'),
  sport: z.string().min(1, 'Please select a sport'),
  experienceLevel: z.string().min(1, 'Please select experience level'),
  additionalNotes: z.string().optional(),
})

export default function CampRegistrationForm({ customerId }) {
  const [selectedDates, setSelectedDates] = useState([])
  const [sport, setSport] = useState('')
  const [experienceLevel, setExperienceLevel] = useState('')

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
    reset,
    setValue,
  } = useForm({
    resolver: zodResolver(campSchema),
  })

  const handleDateSelect = (date) => {
    if (selectedDates.some((d) => d.getTime() === date.getTime())) {
      setSelectedDates(selectedDates.filter((d) => d.getTime() !== date.getTime()))
    } else {
      setSelectedDates([...selectedDates, date])
    }
  }

  const onSubmit = async (data) => {
    if (selectedDates.length === 0) {
      toast.error('Please select at least one camp date')
      return
    }

    const bookingData = {
      ...data,
      smsOptIn: Boolean(data.smsOptIn),
      campDates: selectedDates.map((date) => format(date, 'yyyy-MM-dd')),
      bookingType: 'camp_registration',
      customerId,
    }
    try {
      const response = await fetch('/api/bookings', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(bookingData),
      })

      const result = await response.json()
      if (response.status === 409) {
        toast.error('Selected camp dates are unavailable.')
        return
      }
      if (!response.ok && response.status !== 207) {
        throw new Error(result.error || 'Unable to create camp booking')
      }

      if (response.status === 207) {
        toast.success('Some camp dates were booked. Unavailable dates were skipped.')
      } else {
        toast.success('Camp registration booked and synced to calendar. Reminder scheduled by SMS.')
      }

      reset()
      setSelectedDates([])
      setSport('')
      setExperienceLevel('')
    } catch (err) {
      toast.error(err.message || 'Camp booking failed')
    }
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
      <div className="rounded-md border p-3 bg-slate-50">
        <label htmlFor="smsOptIn" className="flex gap-2 items-start text-sm text-gray-700">
          <input
            id="smsOptIn"
            type="checkbox"
            className="mt-1 h-4 w-4"
            {...register('smsOptIn')}
          />
          <span>
            Text me reminders (optional). Msg &amp; data rates may apply. Reply STOP to unsubscribe, HELP for help.
          </span>
        </label>
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
            placeholder="12"
            type="number"
          />
          {errors.childAge && (
            <p className="text-sm text-red-500">{errors.childAge.message}</p>
          )}
        </div>
      </div>

      <div className="grid md:grid-cols-2 gap-4">
        <div className="space-y-2">
          <Label htmlFor="sport">Sport *</Label>
          <Select
            value={sport}
            onValueChange={(value) => {
              setSport(value)
              setValue('sport', value)
            }}
          >
            <SelectTrigger>
              <SelectValue placeholder="Select sport" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="baseball">Baseball</SelectItem>
              <SelectItem value="softball">Softball</SelectItem>
            </SelectContent>
          </Select>
          {errors.sport && (
            <p className="text-sm text-red-500">{errors.sport.message}</p>
          )}
        </div>

        <div className="space-y-2">
          <Label htmlFor="experienceLevel">Experience Level *</Label>
          <Select
            value={experienceLevel}
            onValueChange={(value) => {
              setExperienceLevel(value)
              setValue('experienceLevel', value)
            }}
          >
            <SelectTrigger>
              <SelectValue placeholder="Select level" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="beginner">Beginner</SelectItem>
              <SelectItem value="intermediate">Intermediate</SelectItem>
              <SelectItem value="advanced">Advanced</SelectItem>
            </SelectContent>
          </Select>
          {errors.experienceLevel && (
            <p className="text-sm text-red-500">{errors.experienceLevel.message}</p>
          )}
        </div>
      </div>

      <div className="space-y-2">
        <Label>Preferred Camp Dates * (Select multiple if interested)</Label>
        <Calendar
          mode="multiple"
          selected={selectedDates}
          onSelect={handleDateSelect}
          disabled={(date) => date < new Date()}
          className="rounded-md border"
        />
        {selectedDates.length > 0 && (
          <div className="text-sm text-green-600">
            <p className="font-semibold">Selected dates:</p>
            <ul className="list-disc list-inside">
              {selectedDates.map((date, idx) => (
                <li key={idx}>{format(date, 'MMMM d, yyyy')}</li>
              ))}
            </ul>
          </div>
        )}
      </div>

      <div className="space-y-2">
        <Label htmlFor="additionalNotes">Additional Notes</Label>
        <textarea
          id="additionalNotes"
          {...register('additionalNotes')}
          placeholder="Any questions or special considerations?"
          className="w-full min-h-24 px-3 py-2 border rounded-md"
        />
      </div>

      <Button type="submit" className="w-full" disabled={isSubmitting}>
        {isSubmitting ? 'Submitting...' : 'Submit Camp Registration'}
      </Button>

      <p className="text-sm text-gray-500 text-center">
        We'll call you within 24 hours to confirm availability and discuss camp details.
      </p>
    </form>
  )
}
