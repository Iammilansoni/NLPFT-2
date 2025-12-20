/**
 * Reset Password Page
 * Reset password using token from email link
 * Enterprise Calm Design - Clean, minimal, professional
 */

'use client';

import React, { useState, useEffect, Suspense } from 'react';
import Link from 'next/link';
import { useRouter, useSearchParams } from 'next/navigation';
import {
  Lock,
  ArrowLeft,
  CheckCircle,
  AlertCircle,
  Eye,
  EyeOff,
  Loader2,
  KeyRound
} from 'lucide-react';
import authService from '@/lib/auth';

function ResetPasswordForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const token = searchParams.get('token');

  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [isValidating, setIsValidating] = useState(true);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);
  const [tokenValid, setTokenValid] = useState(false);
  const [userEmail, setUserEmail] = useState('');

  // Validate token on mount
  useEffect(() => {
    async function validateToken() {
      if (!token) {
        setError('No reset token provided');
        setIsValidating(false);
        return;
      }

      try {
        const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/v1/auth/verify-reset-token?token=${token}`);
        const data = await response.json();

        if (data.valid) {
          setTokenValid(true);
          setUserEmail(data.email || '');
        } else {
          setError(data.message || 'Invalid or expired reset token');
        }
      } catch (err) {
        setError('Failed to validate reset token');
      } finally {
        setIsValidating(false);
      }
    }

    validateToken();
  }, [token]);

  const validatePassword = (pwd: string): string[] => {
    const errors: string[] = [];
    if (pwd.length < 8) errors.push('At least 8 characters');
    if (!/[A-Z]/.test(pwd)) errors.push('One uppercase letter');
    if (!/[a-z]/.test(pwd)) errors.push('One lowercase letter');
    if (!/[0-9]/.test(pwd)) errors.push('One digit');
    return errors;
  };

  const passwordErrors = validatePassword(password);
  const isPasswordValid = passwordErrors.length === 0;
  const passwordsMatch = password === confirmPassword && confirmPassword.length > 0;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    if (!isPasswordValid) {
      setError('Password does not meet requirements');
      return;
    }

    if (!passwordsMatch) {
      setError('Passwords do not match');
      return;
    }

    setIsLoading(true);

    try {
      await authService.resetPassword({
        token: token!,
        new_password: password,
        confirm_password: confirmPassword,
      });
      setSuccess(true);
    } catch (err: any) {
      const errorMessage = err.response?.data?.detail || 'Failed to reset password';
      setError(errorMessage);
    } finally {
      setIsLoading(false);
    }
  };

  // Loading state
  if (isValidating) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <div className="text-center">
          <Loader2 className="w-8 h-8 animate-spin text-primary mx-auto mb-4" />
          <p className="text-muted-foreground text-sm">Validating reset token...</p>
        </div>
      </div>
    );
  }

  // Invalid token state
  if (!tokenValid && !success) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background p-6">
        <div className="w-full max-w-md">
          <div className="bg-card border rounded-lg p-8 text-center">
            <div className="w-14 h-14 bg-red-100 dark:bg-red-900/30 rounded-full flex items-center justify-center mx-auto mb-4">
              <AlertCircle className="w-7 h-7 text-red-600 dark:text-red-400" />
            </div>
            <h2 className="text-xl font-semibold mb-2">Invalid Reset Link</h2>
            <p className="text-muted-foreground text-sm mb-6">
              {error || 'This password reset link is invalid or has expired.'}
            </p>
            <Link
              href="/auth/forgot-password"
              className="inline-flex items-center justify-center gap-2 bg-primary text-primary-foreground px-5 py-2.5 rounded-md font-medium text-sm hover:bg-primary/90 transition-colors"
            >
              Request New Link
            </Link>
            <div className="mt-4">
              <Link
                href="/auth/login"
                className="inline-flex items-center gap-2 text-muted-foreground hover:text-foreground text-sm"
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

  // Success state
  if (success) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background p-6">
        <div className="w-full max-w-md">
          <div className="bg-card border rounded-lg p-8 text-center">
            <div className="w-14 h-14 bg-green-100 dark:bg-green-900/30 rounded-full flex items-center justify-center mx-auto mb-4">
              <CheckCircle className="w-7 h-7 text-green-600 dark:text-green-400" />
            </div>
            <h2 className="text-xl font-semibold mb-2">Password Reset!</h2>
            <p className="text-muted-foreground text-sm mb-6">
              Your password has been reset successfully. You can now log in with your new password.
            </p>
            <Link
              href="/auth/login"
              className="inline-flex items-center justify-center gap-2 bg-primary text-primary-foreground px-5 py-2.5 rounded-md font-medium text-sm hover:bg-primary/90 transition-colors w-full"
            >
              Go to Login
            </Link>
          </div>
        </div>
      </div>
    );
  }

  // Reset password form
  return (
    <div className="min-h-screen flex items-center justify-center bg-background p-6">
      <div className="w-full max-w-md">
        <div className="bg-card border rounded-lg p-8">
          {/* Header */}
          <div className="text-center mb-6">
            <div className="w-12 h-12 bg-primary/10 rounded-full flex items-center justify-center mx-auto mb-4">
              <KeyRound className="w-6 h-6 text-primary" />
            </div>
            <h1 className="text-xl font-semibold mb-1">Create New Password</h1>
            {userEmail && (
              <p className="text-muted-foreground text-sm">
                For <strong>{userEmail}</strong>
              </p>
            )}
          </div>

          {/* Error message */}
          {error && (
            <div className="mb-6 p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-md flex items-start gap-2">
              <AlertCircle className="w-4 h-4 text-red-600 dark:text-red-400 flex-shrink-0 mt-0.5" />
              <p className="text-sm text-red-600 dark:text-red-400">{error}</p>
            </div>
          )}

          {/* Form */}
          <form onSubmit={handleSubmit} className="space-y-4">
            {/* New Password */}
            <div className="space-y-1.5">
              <label className="text-sm font-medium">New Password</label>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                <input
                  type={showPassword ? 'text' : 'password'}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full pl-9 pr-9 py-2.5 bg-background border border-border rounded-md focus:ring-2 focus:ring-primary/30 focus:border-primary outline-none transition-all text-sm"
                  placeholder="Enter new password"
                  required
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
                >
                  {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>

              {/* Password requirements */}
              {password && (
                <div className="mt-2 space-y-1">
                  {['At least 8 characters', 'One uppercase letter', 'One lowercase letter', 'One digit'].map((req) => {
                    const isMet = !passwordErrors.includes(req);
                    return (
                      <div key={req} className={`flex items-center gap-2 text-xs ${isMet ? 'text-green-600 dark:text-green-400' : 'text-muted-foreground'}`}>
                        <CheckCircle className={`w-3 h-3 ${isMet ? 'text-green-600 dark:text-green-400' : 'text-muted-foreground/50'}`} />
                        {req}
                      </div>
                    );
                  })}
                </div>
              )}
            </div>

            {/* Confirm Password */}
            <div className="space-y-1.5">
              <label className="text-sm font-medium">Confirm Password</label>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                <input
                  type={showConfirmPassword ? 'text' : 'password'}
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  className={`w-full pl-9 pr-9 py-2.5 bg-background border rounded-md focus:ring-2 focus:ring-primary/30 focus:border-primary outline-none transition-all text-sm ${confirmPassword && !passwordsMatch ? 'border-red-500' : 'border-border'
                    }`}
                  placeholder="Confirm new password"
                  required
                />
                <button
                  type="button"
                  onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
                >
                  {showConfirmPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
              {confirmPassword && !passwordsMatch && (
                <p className="text-xs text-red-600 dark:text-red-400 mt-1">Passwords do not match</p>
              )}
            </div>

            {/* Submit button */}
            <button
              type="submit"
              disabled={isLoading || !isPasswordValid || !passwordsMatch}
              className="w-full py-2.5 bg-primary text-primary-foreground rounded-md font-medium text-sm hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed transition-all flex items-center justify-center gap-2"
            >
              {isLoading ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Resetting Password...
                </>
              ) : (
                'Reset Password'
              )}
            </button>
          </form>

          {/* Back to login */}
          <div className="mt-6 text-center">
            <Link
              href="/auth/login"
              className="inline-flex items-center gap-2 text-muted-foreground hover:text-foreground text-sm"
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

export default function ResetPasswordPage() {
  return (
    <Suspense fallback={
      <div className="min-h-screen flex items-center justify-center bg-background">
        <div className="text-center">
          <Loader2 className="w-8 h-8 animate-spin text-primary mx-auto mb-4" />
          <p className="text-muted-foreground text-sm">Loading...</p>
        </div>
      </div>
    }>
      <ResetPasswordForm />
    </Suspense>
  );
}
