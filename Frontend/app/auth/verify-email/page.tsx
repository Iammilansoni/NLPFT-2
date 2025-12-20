'use client'

import { Suspense, useState, useEffect } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import { Mail, ArrowRight, Loader2, CheckCircle2, AlertCircle, RefreshCw } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { toast } from '@/hooks/use-toast'
import apiClient from '@/lib/api-client'

function VerifyEmailContent() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const email = searchParams.get('email') || ''

  const [otp, setOtp] = useState('')
  const [isVerifying, setIsVerifying] = useState(false)
  const [isResending, setIsResending] = useState(false)
  const [isVerified, setIsVerified] = useState(false)
  const [error, setError] = useState('')
  const [countdown, setCountdown] = useState(0)

  // Countdown timer for resend button
  useEffect(() => {
    if (countdown > 0) {
      const timer = setTimeout(() => setCountdown(countdown - 1), 1000)
      return () => clearTimeout(timer)
    }
  }, [countdown])

  const handleVerify = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')

    if (!otp || otp.length !== 6) {
      setError('Please enter a valid 6-digit OTP')
      return
    }

    setIsVerifying(true)

    try {
      const response = await apiClient.post('/api/v1/auth/verify-otp', {
        email,
        otp
      })

      setIsVerified(true)

      toast({
        title: "Email Verified!",
        description: "Your email has been verified successfully. Redirecting to login...",
      })

      // Redirect to login after 2 seconds
      setTimeout(() => {
        router.push('/auth/login')
      }, 2000)
    } catch (err: any) {
      const errorMessage = err.response?.data?.detail || 'Invalid or expired OTP'
      setError(errorMessage)
      toast({
        title: "Verification Failed",
        description: errorMessage,
        variant: "destructive",
      })
    } finally {
      setIsVerifying(false)
    }
  }

  const handleResend = async () => {
    if (countdown > 0) return

    setIsResending(true)
    setError('')

    try {
      await apiClient.post('/api/v1/auth/resend-otp', {
        email
      })

      setCountdown(60) // 60 second cooldown

      toast({
        title: "OTP Resent",
        description: "A new OTP has been sent to your email.",
      })
    } catch (err: any) {
      const errorMessage = err.response?.data?.detail || 'Failed to resend OTP'
      setError(errorMessage)
      toast({
        title: "Resend Failed",
        description: errorMessage,
        variant: "destructive",
      })
    } finally {
      setIsResending(false)
    }
  }

  if (isVerified) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background p-6">
        <Card className="max-w-md w-full">
          <CardContent className="pt-6">
            <div className="text-center space-y-4">
              <div>
                <CheckCircle2 className="h-16 w-16 text-green-600 mx-auto" />
              </div>
              <h2 className="text-2xl font-bold">Email Verified!</h2>
              <p className="text-muted-foreground">
                Your email has been verified successfully. Redirecting to login...
              </p>
              <Loader2 className="h-6 w-6 animate-spin mx-auto text-primary" />
            </div>
          </CardContent>
        </Card>
      </div>
    )
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-background p-6">
      <div className="w-full max-w-md">
        <Card>
          <CardHeader className="space-y-1">
            <div className="flex items-center justify-center mb-4">
              <div className="w-12 h-12 rounded-full bg-primary/10 flex items-center justify-center">
                <Mail className="h-6 w-6 text-primary" />
              </div>
            </div>
            <CardTitle className="text-2xl font-bold text-center">
              Verify Your Email
            </CardTitle>
            <CardDescription className="text-center">
              We've sent a 6-digit code to<br />
              <span className="font-semibold text-foreground">{email}</span>
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleVerify} className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="otp">Enter OTP Code</Label>
                <Input
                  id="otp"
                  placeholder="000000"
                  value={otp}
                  onChange={(e) => {
                    const value = e.target.value.replace(/\D/g, '').slice(0, 6)
                    setOtp(value)
                    setError('')
                  }}
                  className="text-center text-2xl font-mono tracking-widest"
                  maxLength={6}
                  autoFocus
                />
                <p className="text-xs text-muted-foreground text-center">
                  OTP expires in 10 minutes
                </p>
              </div>

              {error && (
                <div className="rounded-lg bg-destructive/10 border border-destructive/20 p-3 flex items-start gap-2">
                  <AlertCircle className="h-4 w-4 text-destructive mt-0.5" />
                  <p className="text-sm text-destructive">{error}</p>
                </div>
              )}

              <Button
                type="submit"
                className="w-full"
                disabled={isVerifying || otp.length !== 6}
              >
                {isVerifying ? (
                  <>
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                    Verifying...
                  </>
                ) : (
                  <>
                    Verify Email
                    <ArrowRight className="h-4 w-4 ml-2" />
                  </>
                )}
              </Button>

              <div className="relative my-6">
                <div className="absolute inset-0 flex items-center">
                  <div className="w-full border-t border-border" />
                </div>
                <div className="relative flex justify-center text-xs uppercase">
                  <span className="bg-background px-2 text-muted-foreground">
                    Didn't receive code?
                  </span>
                </div>
              </div>

              <Button
                type="button"
                variant="outline"
                className="w-full"
                onClick={handleResend}
                disabled={isResending || countdown > 0}
              >
                {isResending ? (
                  <>
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                    Resending...
                  </>
                ) : countdown > 0 ? (
                  <>
                    <RefreshCw className="h-4 w-4 mr-2" />
                    Resend in {countdown}s
                  </>
                ) : (
                  <>
                    <RefreshCw className="h-4 w-4 mr-2" />
                    Resend OTP
                  </>
                )}
              </Button>

              <p className="text-center text-sm text-muted-foreground">
                Check your spam folder if you don't see the email
              </p>
            </form>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}

export default function VerifyEmailPage() {
  return (
    <Suspense fallback={
      <div className="flex min-h-screen items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    }>
      <VerifyEmailContent />
    </Suspense>
  )
}
