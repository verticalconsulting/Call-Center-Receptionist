import React from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import * as z from 'zod'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Link } from 'react-router-dom'
import toast from 'react-hot-toast'

const smsOptInSchema = z.object({
  phoneNumber: z.string().min(10, 'Phone number is required'),
  keyword: z.string().min(1, 'Keyword is required'),
})

const keywordOptions = ['BIRTHDAY', 'CAMPS', 'DEALS', 'EVENTS']

export default function SmsOptInPage() {
  const {
    register,
    handleSubmit,
    setValue,
    watch,
    formState: { errors, isSubmitting },
    reset,
  } = useForm({
    resolver: zodResolver(smsOptInSchema),
    defaultValues: {
      keyword: 'CAMPS',
    },
  })

  const selectedKeyword = watch('keyword')

  const onSubmit = async (data) => {
    // Frontend-only capture for compliance UX; integrate API when provider onboarding is complete.
    await Promise.resolve()
    toast.success(`You are opted in for ${data.keyword} updates.`)
    reset({ phoneNumber: '', keyword: data.keyword })
  }

  return (
    <main className="bg-slate-950 text-slate-100 min-h-[70vh]">
      <div className="max-w-3xl mx-auto px-4 py-10">
        <h1 className="text-3xl md:text-4xl font-black mb-3">Text Updates / SMS Opt-In</h1>
        <p className="text-slate-300 mb-6">
          Get camp alerts, birthday updates, and promo notices from D-BAT Pearl.
        </p>

        <section className="rounded-xl border border-slate-800 bg-slate-900/70 p-5 md:p-6">
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="phoneNumber">Phone Number *</Label>
              <Input id="phoneNumber" {...register('phoneNumber')} placeholder="+1 (601) 555-0100" type="tel" />
              {errors.phoneNumber && <p className="text-sm text-red-400">{errors.phoneNumber.message}</p>}
            </div>

            <div className="space-y-2">
              <Label htmlFor="keyword">Keyword *</Label>
              <Select
                value={selectedKeyword}
                onValueChange={(value) => setValue('keyword', value, { shouldValidate: true })}
              >
                <SelectTrigger id="keyword">
                  <SelectValue placeholder="Choose keyword" />
                </SelectTrigger>
                <SelectContent>
                  {keywordOptions.map((keyword) => (
                    <SelectItem key={keyword} value={keyword}>
                      {keyword}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              {errors.keyword && <p className="text-sm text-red-400">{errors.keyword.message}</p>}
            </div>

            <Button type="submit" className="w-full" disabled={isSubmitting}>
              {isSubmitting ? 'Submitting...' : 'Opt in to texts'}
            </Button>
          </form>

          <div className="mt-5 space-y-2 text-sm text-slate-300">
            <p>By submitting, you agree to receive recurring SMS messages from D-BAT Pearl. Msg &amp; data rates may apply.</p>
            <p>Reply STOP to unsubscribe, HELP for help.</p>
            <p>
              View our <Link className="text-lime-400 hover:underline" to="/booking/privacy">Privacy Policy</Link> and{' '}
              <Link className="text-lime-400 hover:underline" to="/booking/sms-terms">SMS Terms</Link>.
            </p>
          </div>
        </section>

        <section className="mt-6 rounded-xl border border-slate-800 bg-slate-900/40 p-5">
          <p className="text-sm text-slate-300">
            Fast opt-in option: Text <span className="font-semibold text-lime-400">CAMPS</span> to{' '}
            <span className="font-semibold text-lime-400">+1 (833) 793-9008</span>.
          </p>
        </section>
      </div>
    </main>
  )
}
