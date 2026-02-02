import { useState, useCallback, useEffect, useRef, FormEvent } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import { useAuth } from '@/stores'

export function LoginPage() {
  const navigate = useNavigate()
  const location = useLocation()
  const { login, isAuthenticated, isLoading: authLoading } = useAuth()

  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [isSubmitting, setIsSubmitting] = useState(false)

  const emailInputRef = useRef<HTMLInputElement>(null)

  // Focus email input on mount
  useEffect(() => {
    emailInputRef.current?.focus()
  }, [])

  // Redirect if already authenticated
  useEffect(() => {
    if (isAuthenticated && !authLoading) {
      const from = (location.state as { from?: string })?.from || '/discovery'
      navigate(from, { replace: true })
    }
  }, [isAuthenticated, authLoading, navigate, location.state])

  const handleSubmit = useCallback(
    async (e: FormEvent) => {
      e.preventDefault()
      setError(null)

      if (!email.trim()) {
        setError('Email is required')
        return
      }

      if (!email.includes('@')) {
        setError('Please enter a valid email address')
        return
      }

      if (!password) {
        setError('Password is required')
        return
      }

      setIsSubmitting(true)

      try {
        const success = await login(email, password)
        if (success) {
          const from = (location.state as { from?: string })?.from || '/discovery'
          navigate(from, { replace: true })
        } else {
          setError('Invalid email or password')
        }
      } catch {
        setError('An error occurred. Please try again.')
      } finally {
        setIsSubmitting(false)
      }
    },
    [email, password, login, navigate, location.state]
  )

  if (authLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background-subtle">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
      </div>
    )
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-background-subtle py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8">
        <div>
          <h1 className="text-center text-3xl font-bold text-foreground">
            Discovery
          </h1>
          <h2 className="mt-2 text-center text-xl text-foreground-muted">
            AI Opportunity Discovery Platform
          </h2>
          <p className="mt-4 text-center text-sm text-foreground-subtle">
            Sign in to start discovering AI automation opportunities
          </p>
        </div>

        <form className="mt-8 space-y-6" onSubmit={handleSubmit}>
          {error && (
            <div
              className="bg-destructive/10 border border-destructive/20 text-destructive px-4 py-3 rounded-md text-sm"
              role="alert"
              aria-live="assertive"
            >
              {error}
            </div>
          )}

          <div className="space-y-4">
            <div>
              <label htmlFor="email" className="block text-sm font-medium text-foreground">
                Email address
              </label>
              <input
                ref={emailInputRef}
                id="email"
                name="email"
                type="email"
                autoComplete="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="input mt-1 w-full"
                placeholder="you@company.com"
                disabled={isSubmitting}
              />
            </div>

            <div>
              <label htmlFor="password" className="block text-sm font-medium text-foreground">
                Password
              </label>
              <input
                id="password"
                name="password"
                type="password"
                autoComplete="current-password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="input mt-1 w-full"
                placeholder="Enter your password"
                disabled={isSubmitting}
              />
            </div>
          </div>

          <div>
            <button
              type="submit"
              disabled={isSubmitting}
              className="w-full btn-primary btn-md rounded-md disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isSubmitting ? (
                <>
                  <span className="animate-spin rounded-full h-4 w-4 border-b-2 border-primary-foreground mr-2"></span>
                  Signing in...
                </>
              ) : (
                'Sign in'
              )}
            </button>
          </div>

          <div className="text-center text-sm text-foreground-subtle">
            <p>Demo mode: Enter any email and password to continue</p>
          </div>
        </form>
      </div>
    </div>
  )
}
