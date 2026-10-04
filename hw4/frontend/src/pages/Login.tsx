import { useState } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import { ApiError } from '../api'
import { useAuth } from '../auth'
import './Auth.css'

export default function Login() {
  const { login } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const from = (location.state as { from?: string } | null)?.from ?? '/'

  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [errors, setErrors] = useState<Record<string, string>>({})
  const [formError, setFormError] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)

  async function submit(e: React.FormEvent) {
    e.preventDefault()
    const next: Record<string, string> = {}
    if (!email.trim()) next.email = 'Enter the email on your account.'
    else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
      next.email = 'That email address does not look right.'
    }
    if (!password) next.password = 'Enter your password.'
    setErrors(next)
    setFormError(null)
    if (Object.keys(next).length > 0) return

    setSubmitting(true)
    try {
      await login(email.trim(), password)
      navigate(from, { replace: true })
    } catch (err) {
      setFormError(
        err instanceof ApiError ? err.message : 'Could not sign you in just now.',
      )
      setPassword('')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="page section auth-wrap">
      <div className="auth-card">
        <h1>Welcome back</h1>
        <p className="muted">Sign in to pick up where you left off.</p>

        {formError && (
          <div className="alert alert-error" role="alert">{formError}</div>
        )}

        <form onSubmit={submit} noValidate>
          <div className="field">
            <label htmlFor="email">Email</label>
            <input
              id="email" type="email" value={email} autoComplete="email"
              disabled={submitting}
              onChange={(e) => setEmail(e.target.value)}
              aria-invalid={Boolean(errors.email)}
              aria-describedby={errors.email ? 'email-err' : undefined}
            />
            {errors.email && <p className="field-err" id="email-err">{errors.email}</p>}
          </div>

          <div className="field">
            <label htmlFor="password">Password</label>
            <input
              id="password" type="password" value={password}
              autoComplete="current-password" disabled={submitting}
              onChange={(e) => setPassword(e.target.value)}
              aria-invalid={Boolean(errors.password)}
              aria-describedby={errors.password ? 'pw-err' : undefined}
            />
            {errors.password && <p className="field-err" id="pw-err">{errors.password}</p>}
          </div>

          <button className="btn btn-primary auth-submit" type="submit" disabled={submitting}>
            {submitting ? 'Signing in…' : 'Log in'}
          </button>
        </form>

        <p className="auth-alt">
          New here? <Link to="/create-account">Create an account</Link>
        </p>
      </div>
    </div>
  )
}
