/**
 * Register Page
 * Enterprise-grade registration with accessibility and polish
 */

'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { Mail, Lock, User, ArrowRight, Zap, AlertCircle, Eye, EyeOff, CheckCircle2, XCircle, Loader2, Home } from 'lucide-react';
import { useAuth } from '@/contexts/AuthContext';

interface PasswordStrength {
  score: number;
  label: string;
  color: string;
}

export default function RegisterPage() {
  const router = useRouter();
  const { register } = useAuth();

  const [formData, setFormData] = useState({
    email: '',
    username: '',
    password: '',
    confirm_password: '',
  });
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value,
    });
    if (error) setError('');
  };

  const getPasswordStrength = (password: string): PasswordStrength => {
    let score = 0;
    if (password.length >= 8) score++;
    if (password.length >= 12) score++;
    if (/[a-z]/.test(password) && /[A-Z]/.test(password)) score++;
    if (/\d/.test(password)) score++;
    if (/[^a-zA-Z\d]/.test(password)) score++;

    if (score <= 2) return { score, label: 'Weak', color: 'text-destructive' };
    if (score === 3) return { score, label: 'Fair', color: 'text-amber-500' };
    if (score === 4) return { score, label: 'Good', color: 'text-green-500' };
    return { score, label: 'Strong', color: 'text-green-500' };
  };

  const passwordStrength = formData.password ? getPasswordStrength(formData.password) : null;

  const passwordRequirements = [
    { met: formData.password.length >= 8, text: 'At least 8 characters' },
    { met: /[A-Z]/.test(formData.password), text: 'One uppercase letter' },
    { met: /[a-z]/.test(formData.password), text: 'One lowercase letter' },
    { met: /\d/.test(formData.password), text: 'One number' },
  ];

  const passwordsMatch = formData.password === formData.confirm_password;
  const showPasswordMismatch = formData.confirm_password && !passwordsMatch;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    if (!passwordsMatch) {
      setError('Passwords do not match');
      return;
    }

    if (formData.username.length < 3) {
      setError('Username must be at least 3 characters');
      return;
    }

    setIsLoading(true);

    try {
      await register(formData);
      router.push(`/auth/verify-email?email=${encodeURIComponent(formData.email)}`);
    } catch (err: any) {
      const errorMessage = err.response?.data?.detail ||
        (Array.isArray(err.response?.data) ? err.response.data[0]?.msg : null) ||
        'Registration failed. Please try again.';
      setError(errorMessage);
    } finally {
      setIsLoading(false);
    }
  };

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
            Create an account
          </h1>
          <p className="text-muted-foreground text-sm">
            Start your journey with intelligent API testing
          </p>
        </div>

        {/* Back to Home Button */}
        <Link
          href="/"
          className="inline-flex items-center justify-center gap-2 w-full mb-4 px-4 py-2.5 bg-muted text-foreground font-medium rounded-lg hover:bg-muted/80 transition-all duration-150 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2 focus-visible:ring-offset-background"
        >
          <Home className="w-4 h-4" />
          Back to Home
        </Link>

        {/* Register Form Card */}
        <div className="bg-card border border-border rounded-xl p-6 shadow-sm transition-shadow duration-200 hover:shadow-md">
          <form onSubmit={handleSubmit} className="space-y-4" aria-describedby={error ? 'register-error' : undefined}>
            {/* Error Alert */}
            {error && (
              <div
                id="register-error"
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
                  value={formData.email}
                  onChange={handleChange}
                  className="w-full pl-9 pr-3 py-2.5 bg-background border border-border rounded-lg text-sm text-foreground placeholder:text-muted-foreground/50 transition-all duration-150 focus:outline-none focus:ring-2 focus:ring-primary focus:border-primary focus:ring-offset-1 focus:ring-offset-background"
                  placeholder="you@example.com"
                />
              </div>
            </div>

            {/* Username Field */}
            <div>
              <label htmlFor="username" className="block text-sm font-medium text-foreground mb-1.5">
                Username
              </label>
              <div className="relative">
                <User className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground pointer-events-none" />
                <input
                  id="username"
                  name="username"
                  type="text"
                  autoComplete="username"
                  required
                  minLength={3}
                  value={formData.username}
                  onChange={handleChange}
                  className="w-full pl-9 pr-3 py-2.5 bg-background border border-border rounded-lg text-sm text-foreground placeholder:text-muted-foreground/50 transition-all duration-150 focus:outline-none focus:ring-2 focus:ring-primary focus:border-primary focus:ring-offset-1 focus:ring-offset-background"
                  placeholder="johndoe"
                  aria-describedby="username-hint"
                />
              </div>
              <p id="username-hint" className="text-xs text-muted-foreground mt-1">Minimum 3 characters</p>
            </div>

            {/* Password Field */}
            <div>
              <label htmlFor="password" className="block text-sm font-medium text-foreground mb-1.5">
                Password
              </label>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground pointer-events-none" />
                <input
                  id="password"
                  name="password"
                  type={showPassword ? 'text' : 'password'}
                  autoComplete="new-password"
                  required
                  minLength={8}
                  value={formData.password}
                  onChange={handleChange}
                  className="w-full pl-9 pr-10 py-2.5 bg-background border border-border rounded-lg text-sm text-foreground placeholder:text-muted-foreground/50 transition-all duration-150 focus:outline-none focus:ring-2 focus:ring-primary focus:border-primary focus:ring-offset-1 focus:ring-offset-background"
                  placeholder="••••••••"
                  aria-describedby="password-requirements"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground transition-colors p-0.5 rounded focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary"
                  aria-label={showPassword ? 'Hide password' : 'Show password'}
                >
                  {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>

              {/* Password Strength Indicator */}
              {formData.password && (
                <div id="password-requirements" className="mt-3 space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-xs text-muted-foreground">Strength:</span>
                    <span className={`text-xs font-medium ${passwordStrength?.color}`}>
                      {passwordStrength?.label}
                    </span>
                  </div>
                  <div className="flex gap-1" aria-hidden="true">
                    {[...Array(5)].map((_, i) => (
                      <div
                        key={i}
                        className={`h-1 flex-1 rounded-full transition-colors duration-200 ${i < (passwordStrength?.score || 0)
                          ? passwordStrength?.score && passwordStrength.score >= 4
                            ? 'bg-green-500'
                            : passwordStrength?.score === 3
                              ? 'bg-amber-500'
                              : 'bg-destructive'
                          : 'bg-border'
                          }`}
                      />
                    ))}
                  </div>

                  {/* Password Requirements */}
                  <ul className="space-y-1" role="list">
                    {passwordRequirements.map((req, index) => (
                      <li key={index} className="flex items-center gap-2 text-xs">
                        {req.met ? (
                          <CheckCircle2 className="w-3.5 h-3.5 text-green-500 flex-shrink-0" aria-hidden="true" />
                        ) : (
                          <XCircle className="w-3.5 h-3.5 text-muted-foreground flex-shrink-0" aria-hidden="true" />
                        )}
                        <span className={req.met ? 'text-green-600 dark:text-green-400' : 'text-muted-foreground'}>
                          {req.text}
                        </span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>

            {/* Confirm Password Field */}
            <div>
              <label htmlFor="confirm_password" className="block text-sm font-medium text-foreground mb-1.5">
                Confirm password
              </label>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground pointer-events-none" />
                <input
                  id="confirm_password"
                  name="confirm_password"
                  type={showConfirmPassword ? 'text' : 'password'}
                  autoComplete="new-password"
                  required
                  value={formData.confirm_password}
                  onChange={handleChange}
                  className={`w-full pl-9 pr-10 py-2.5 bg-background border rounded-lg text-sm text-foreground placeholder:text-muted-foreground/50 transition-all duration-150 focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-1 focus:ring-offset-background ${showPasswordMismatch ? 'border-destructive focus:border-destructive' : 'border-border focus:border-primary'
                    }`}
                  placeholder="••••••••"
                  aria-describedby={showPasswordMismatch ? 'confirm-password-error' : undefined}
                />
                <button
                  type="button"
                  onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground transition-colors p-0.5 rounded focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary"
                  aria-label={showConfirmPassword ? 'Hide password' : 'Show password'}
                >
                  {showConfirmPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
              {showPasswordMismatch && (
                <p id="confirm-password-error" className="text-xs text-destructive mt-1" role="alert">
                  Passwords do not match
                </p>
              )}
            </div>

            {/* Terms and Privacy */}
            <p className="text-xs text-muted-foreground">
              By signing up, you agree to our{' '}
              <Link href="/terms" className="text-primary hover:underline rounded focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary">
                Terms of Service
              </Link>{' '}
              and{' '}
              <Link href="/privacy" className="text-primary hover:underline rounded focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary">
                Privacy Policy
              </Link>
            </p>

            {/* Submit Button */}
            <button
              type="submit"
              disabled={isLoading}
              className="w-full px-4 py-2.5 bg-primary text-primary-foreground font-medium rounded-lg hover:bg-primary/90 transition-all duration-150 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2 focus-visible:ring-offset-background disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2 shadow-sm hover:shadow-md"
            >
              {isLoading ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Creating account...
                </>
              ) : (
                <>
                  Create account
                  <ArrowRight className="w-4 h-4" />
                </>
              )}
            </button>
          </form>
        </div>

        {/* Sign In Link */}
        <p className="text-center mt-6 text-sm text-muted-foreground">
          Already have an account?{' '}
          <Link
            href="/auth/login"
            className="text-primary hover:underline font-medium rounded focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2 focus-visible:ring-offset-background"
          >
            Sign in
          </Link>
        </p>
      </div>
    </div>
  );
}
