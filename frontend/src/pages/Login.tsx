import { useState } from 'react'
import { Link } from 'react-router-dom'
import './Auth.css'

/**
 * Sign-in form. Accounts are wired to the backend in a later problem; for now the
 * form validates locally and explains that it is not yet connected.
 */
export default function Login() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [errors, setErrors] = useState<Record<string, string>>({})
  const [notice, setNotice] = useState<string | null>(null)

  function submit(e: React.FormEvent) {
    e.preventDefault()
    const next: Record<string, string> = {}
    if (!email.trim()) next.email = 'Enter the email on your account.'
    else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) next.email = 'That email address does not look right.'
    if (!password) next.password = 'Enter your password.'
    setErrors(next)
    setNotice(
      Object.keys(next).length === 0
        ? 'Accounts are not connected yet — sign-in arrives in the next build.'
        : null,
    )
  }

  return (
    <div className="page section auth-wrap">
      <div className="auth-card">
        <h1>Welcome back</h1>
        <p className="muted">Sign in to pick up where you left off.</p>

        {notice && <div className="alert alert-info" role="status">{notice}</div>}

        <form onSubmit={submit} noValidate>
          <div className="field">
            <label htmlFor="email">Email</label>
            <input
              id="email" type="email" value={email} autoComplete="email"
              onChange={(e) => setEmail(e.target.value)}
              aria-invalid={Boolean(errors.email)}
              aria-describedby={errors.email ? 'email-err' : undefined}
            />
            {errors.email && <p className="field-err" id="email-err">{errors.email}</p>}
          </div>

          <div className="field">
            <label htmlFor="password">Password</label>
            <input
              id="password" type="password" value={password} autoComplete="current-password"
              onChange={(e) => setPassword(e.target.value)}
              aria-invalid={Boolean(errors.password)}
              aria-describedby={errors.password ? 'pw-err' : undefined}
            />
            {errors.password && <p className="field-err" id="pw-err">{errors.password}</p>}
          </div>

          <button className="btn btn-primary auth-submit" type="submit">Log in</button>
        </form>

        <p className="auth-alt">
          New here? <Link to="/create-account">Create an account</Link>
        </p>
      </div>
    </div>
  )
}
