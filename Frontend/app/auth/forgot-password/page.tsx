/**
 * Forgot Password Page
 * Enterprise-grade password reset with accessibility and polish
 */

'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { Mail, ArrowLeft, ArrowRight, CheckCircle, Zap, AlertCircle, Loader2 } from 'lucide-react';
import authService from '@/lib/auth';

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setIsLoading(true);

    try {
      await authService.forgotPassword({ email });
      setSuccess(true);
    } catch (err: any) {
      const errorMessage = err.response?.data?.detail || 'Failed to send reset email';
      setError(errorMessage);
    } finally {
      setIsLoading(false);
    }
  };

  if (success) {
    return (
      <div className="min-h-screen flex items-center justify-center py-12 px-4">
        <div className="w-full max-w-sm">
          <div className="bg-card border border-border rounded-xl p-6 shadow-sm text-center transition-shadow duration-200 hover:shadow-md">
            <div className="w-12 h-12 bg-emerald-100 dark:bg-emerald-900/30 rounded-full flex items-center justify-center mx-auto mb-4">
              <CheckCircle className="w-6 h-6 text-emerald-600 dark:text-emerald-400" />
            </div>
            <h2 className="text-xl font-semibold text-foreground mb-2">Check your email</h2>
            <p className="text-sm text-muted-foreground mb-4">
              We've sent a password reset link to <strong className="text-foreground">{email}</strong>
            </p>
            <p className="text-xs text-muted-foreground mb-6">
              Didn't receive the email? Check your spam folder or{' '}
              <button
                onClick={() => setSuccess(false)}
                className="text-primary hover:underline rounded focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary"
              >
                try again
              </button>
            </p>
            <Link
              href="/auth/login"
              className="inline-flex items-center gap-2 text-sm text-primary hover:underline rounded focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2 focus-visible:ring-offset-background"
            >
              <ArrowLeft className="w-4 h-4" />
              Back to login
            </Link>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex items-center justify-center py-12 px-4">
      <div className="w-full max-w-sm">
        {/* Logo and Header */}
        <div className="text-center mb-8">
          <Link
            href="/"
            className="inline-flex items-center gap-2 mb-6 rounded-lg focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2 focus-visible:ring-offset-background transition-opacity hover:opacity-80"
          >
            <div className="w-10 h-10 rounded-lg bg-primary flex items-center justify-center">
              <Zap className="w-5 h-5 text-white" />
            </div>
            <span className="font-bold text-xl text-foreground">NLPForge</span>
          </Link>
          <h1 className="text-2xl font-bold text-foreground mb-2">
            Forgot password?
          </h1>
          <p className="text-muted-foreground text-sm">
            No worries, we'll send you reset instructions
          </p>
        </div>

        {/* Reset Form Card */}
        <div className="bg-card border border-border rounded-xl p-6 shadow-sm transition-shadow duration-200 hover:shadow-md">
          <form onSubmit={handleSubmit} className="space-y-4" aria-describedby={error ? 'forgot-error' : undefined}>
            {/* Error Alert */}
            {error && (
              <div
                id="forgot-error"
                role="alert"
                className="flex items-start gap-2 p-3 bg-destructive/10 border border-destructive/20 rounded-lg"
              >
                <AlertCircle className="w-4 h-4 text-destructive flex-shrink-0 mt-0.5" />
                <p className="text-sm text-destructive">{error}</p>
              </div>
            )}

            {/* Email Field */}
            <div>
              <label htmlFor="email" className="block text-sm font-medium text-foreground mb-1.5">
                Email address
              </label>
              <div className="relative">
                <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground pointer-events-none" />
                <input
                  id="email"
                  name="email"
                  type="email"
                  autoComplete="email"
                  required
                  value={email}
                  onChange={(e) => {
                    setEmail(e.target.value);
                    if (error) setError('');
                  }}
                  className="w-full pl-9 pr-3 py-2.5 bg-background border border-border rounded-lg text-sm transition-all duration-150 focus:outline-none focus:ring-2 focus:ring-primary focus:border-primary focus:ring-offset-1 focus:ring-offset-background"
                  placeholder="you@example.com"
                />
              </div>
            </div>

            {/* Submit Button */}
            <button
              type="submit"
              disabled={isLoading}
              className="w-full px-4 py-2.5 bg-primary text-primary-foreground font-medium rounded-lg hover:bg-primary/90 transition-all duration-150 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2 focus-visible:ring-offset-background disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2 shadow-sm hover:shadow-md"
            >
              {isLoading ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Sending...
                </>
              ) : (
                <>
                  Send reset link
                  <ArrowRight className="w-4 h-4" />
                </>
              )}
            </button>
          </form>

          {/* Back to Login Link */}
          <div className="mt-4 text-center">
            <Link
              href="/auth/login"
              className="inline-flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground transition-colors rounded focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2 focus-visible:ring-offset-background"
            >
              <ArrowLeft className="w-4 h-4" />
              Back to login
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
