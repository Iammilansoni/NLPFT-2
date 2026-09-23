/**
 * Login Page - Premium SaaS Design
 * Clean form with Google OAuth option
 */

'use client';

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import { AlertCircle, Eye, EyeOff, Loader2, Sparkles } from 'lucide-react';
import { useAuth } from '@/contexts/AuthContext';
import GoogleSignInButton from '@/components/auth/GoogleSignInButton';
import { DEMO_MODE, DEMO_CREDENTIALS } from '@/lib/constants';

export default function LoginPage() {
  const { login } = useAuth();

  const [formData, setFormData] = useState({
    email: '',
    password: '',
    rememberMe: false,
  });
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.type === 'checkbox' ? e.target.checked : e.target.value;
    setFormData({
      ...formData,
      [e.target.name]: value,
    });
    if (error) setError('');
  };

  const performLogin = async (credentials: { email: string; password: string; rememberMe: boolean }) => {
    setError('');
    setIsLoading(true);

    try {
      const response = await login(credentials);

      // Check for redirect URL in query params
      const searchParams = new URLSearchParams(window.location.search);
      const from = searchParams.get('from');
      const redirectPath = from || '/dashboard';

      // Session is confirmed by the server having set HttpOnly cookies.
      // We verify via the user object returned in the response body.
      if (!response?.user) {
        setError('Login succeeded but session could not be established. Please try again.');
        setIsLoading(false);
        return;
      }

      window.location.href = redirectPath;
    } catch (err: any) {
      const errorMessage = err.response?.data?.detail || 'Invalid email or password';
      setError(errorMessage);
      setIsLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    await performLogin(formData);
  };

  const handleDemoLogin = async () => {
    setFormData((prev) => ({ ...prev, email: DEMO_CREDENTIALS.email, password: DEMO_CREDENTIALS.password }));
    await performLogin({ email: DEMO_CREDENTIALS.email, password: DEMO_CREDENTIALS.password, rememberMe: false });
  };

  // Arriving from the demo banner's "Try it with the demo login" link
  // (/auth/login?demo=1) pre-fills the fields but still requires a click —
  // avoids a surprise auto-login for anyone who lands here via that link
  // without meaning to.
  useEffect(() => {
    if (!DEMO_MODE) return;
    const params = new URLSearchParams(window.location.search);
    if (params.get('demo') === '1') {
      setFormData((prev) => ({ ...prev, email: DEMO_CREDENTIALS.email, password: DEMO_CREDENTIALS.password }));
    }
  }, []);

  return (
    <div className="w-full">
      {/* Header */}
      <div className="mb-8">
        <Link
          href="/"
          className="inline-flex items-center text-sm text-primary hover:text-primary/80 transition-colors mb-4"
        >
          ← Back to home
        </Link>
        <h1 className="text-3xl font-bold text-foreground mb-2">
          Sign in
        </h1>
        <p className="text-muted-foreground">
          Welcome back. Sign in to route requests against your API catalogue.
        </p>
      </div>

      {/* Error Alert */}
      {error && (
        <div
          role="alert"
          className="flex items-start gap-3 p-4 mb-6 bg-destructive/10 border border-destructive/20 rounded-lg"
        >
          <AlertCircle className="w-5 h-5 text-destructive flex-shrink-0 mt-0.5" />
          <p className="text-sm text-destructive">{error}</p>
        </div>
      )}

      {/* Demo Login — recruiter shortcut, only rendered on demo deployments */}
      {DEMO_MODE && (
        <button
          type="button"
          onClick={handleDemoLogin}
          disabled={isLoading}
          className="mb-6 flex w-full items-center justify-center gap-2 rounded-lg border border-primary/30 bg-primary/10 px-6 py-3 font-semibold text-primary transition-all duration-200 hover:bg-primary/20 disabled:cursor-not-allowed disabled:opacity-50"
        >
          {isLoading ? <Loader2 className="h-5 w-5 animate-spin" /> : <Sparkles className="h-5 w-5" />}
          Explore the live demo — no sign-up
        </button>
      )}

      {/* Login Form */}
      <form onSubmit={handleSubmit} className="space-y-5">
        {/* Email Field */}
        <div>
          <label htmlFor="email" className="block text-sm font-medium text-foreground mb-2">
            Email address
          </label>
          <input
            id="email"
            name="email"
            type="email"
            autoComplete="email"
            required
            value={formData.email}
            onChange={handleChange}
            className="w-full px-4 py-3 bg-background border border-border rounded-lg text-foreground placeholder:text-muted-foreground transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-primary focus:border-primary"
            placeholder="name@mail.com"
          />
        </div>

        {/* Password Field */}
        <div>
          <div className="flex items-center justify-between mb-2">
            <label htmlFor="password" className="block text-sm font-medium text-foreground">
              Password
            </label>
            <Link
              href="/auth/forgot-password"
              className="text-sm text-primary hover:text-primary/80 transition-colors"
            >
              Forgot password?
            </Link>
          </div>
          <div className="relative">
            <input
              id="password"
              name="password"
              type={showPassword ? 'text' : 'password'}
              autoComplete="current-password"
              required
              value={formData.password}
              onChange={handleChange}
              className="w-full px-4 py-3 pr-12 bg-background border border-border rounded-lg text-foreground placeholder:text-muted-foreground transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-primary focus:border-primary"
              placeholder="••••••••"
            />
            <button
              type="button"
              onClick={() => setShowPassword(!showPassword)}
              className="absolute right-4 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground transition-colors"
              aria-label={showPassword ? 'Hide password' : 'Show password'}
            >
              {showPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
            </button>
          </div>
        </div>

        {/* Remember Me Checkbox */}
        <div className="flex items-center gap-2">
          <input
            id="rememberMe"
            name="rememberMe"
            type="checkbox"
            checked={formData.rememberMe}
            onChange={handleChange}
            className="w-4 h-4 text-primary border-border rounded focus:ring-primary focus:ring-2"
          />
          <label htmlFor="rememberMe" className="text-sm text-muted-foreground">
            Remember me
          </label>
        </div>

        {/* Submit Button */}
        <button
          type="submit"
          disabled={isLoading}
          className="w-full px-6 py-3.5 bg-primary text-primary-foreground font-semibold rounded-lg hover:bg-primary/90 transition-all duration-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2 shadow-sm"
        >
          {isLoading ? (
            <>
              <Loader2 className="w-5 h-5 animate-spin" />
              Signing in...
            </>
          ) : (
            'Sign in'
          )}
        </button>
      </form>

      {/* Sign Up Link */}
      <p className="mt-6 text-center text-muted-foreground">
        Don&apos;t have an account?{' '}
        <Link
          href="/auth/register"
          className="text-primary hover:text-primary/80 font-medium transition-colors"
        >
          Sign up
        </Link>
      </p>

      {/* Divider */}
      <div className="relative my-8">
        <div className="absolute inset-0 flex items-center">
          <div className="w-full border-t border-border" />
        </div>
        <div className="relative flex justify-center text-sm">
          <span className="px-4 bg-background text-muted-foreground">or</span>
        </div>
      </div>

      {/* Google Sign-In */}
      <GoogleSignInButton onError={setError} />
    </div>
  );
}
