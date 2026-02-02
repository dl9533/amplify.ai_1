import { useState, FormEvent } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../../stores/auth'
import { Button } from '../../components/ui/Button'
import { IconTarget, IconArrowRight, IconAlertCircle } from '../../components/ui/Icons'

export function LoginPage() {
  const navigate = useNavigate()
  const { login, isLoading } = useAuth()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string | null>(null)

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()
    setError(null)

    if (!email || !password) {
      setError('Please enter both email and password')
      return
    }

    const success = await login(email, password)
    if (success) {
      navigate('/discovery')
    } else {
      setError('Invalid email or password')
    }
  }

  return (
    <div className="min-h-screen bg-base flex flex-col">
      {/* Background decoration */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-0 left-1/4 w-96 h-96 bg-accent/5 rounded-full blur-3xl" />
        <div className="absolute bottom-0 right-1/4 w-96 h-96 bg-accent/3 rounded-full blur-3xl" />
      </div>

      {/* Content */}
      <div className="relative flex-1 flex flex-col items-center justify-center px-4">
        {/* Logo */}
        <div className="mb-8 flex items-center gap-3">
          <div className="w-12 h-12 rounded-xl bg-gradient-accent flex items-center justify-center">
            <IconTarget size={24} className="text-white" />
          </div>
          <div>
            <h1 className="text-2xl font-display font-bold text-default tracking-tight">
              Discovery
            </h1>
            <p className="text-sm text-muted">AI Opportunity Finder</p>
          </div>
        </div>

        {/* Login card */}
        <div className="w-full max-w-sm">
          <div className="surface-elevated p-8 animate-scale-in">
            <h2 className="text-lg font-display font-semibold text-default text-center mb-6">
              Welcome back
            </h2>

            <form onSubmit={handleSubmit} className="space-y-4">
              {/* Email field */}
              <div>
                <label
                  htmlFor="email"
                  className="block text-sm font-medium text-default mb-1.5"
                >
                  Email
                </label>
                <input
                  id="email"
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="you@company.com"
                  className="input"
                  autoComplete="email"
                  autoFocus
                />
              </div>

              {/* Password field */}
              <div>
                <label
                  htmlFor="password"
                  className="block text-sm font-medium text-default mb-1.5"
                >
                  Password
                </label>
                <input
                  id="password"
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="Enter your password"
                  className="input"
                  autoComplete="current-password"
                />
              </div>

              {/* Error message */}
              {error && (
                <div className="flex items-start gap-2 p-3 bg-destructive/10 border border-destructive/20 rounded-lg">
                  <IconAlertCircle size={16} className="text-destructive shrink-0 mt-0.5" />
                  <p className="text-sm text-destructive">{error}</p>
                </div>
              )}

              {/* Submit button */}
              <Button
                type="submit"
                variant="primary"
                size="lg"
                className="w-full"
                loading={isLoading}
                icon={<IconArrowRight size={18} />}
                iconPosition="right"
              >
                Sign in
              </Button>
            </form>
          </div>

          {/* Dev mode hint */}
          <p className="mt-4 text-xs text-center text-subtle">
            Development mode: any email/password works
          </p>
        </div>
      </div>

      {/* Footer */}
      <div className="relative py-4 text-center">
        <p className="text-xs text-faint">
          Discovery Module &middot; AI Workforce Automation
        </p>
      </div>
    </div>
  )
}
