import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { ApiError } from '../api'
import { useAuth } from '../auth'
import './Auth.css'

const MIN_PASSWORD = 8

export default function CreateAccount() {
  const { register } = useAuth()
  const navigate = useNavigate()

  const [form, setForm] = useState({
    firstName: '', lastName: '', email: '', password: '', confirm: '',
  })
  const [errors, setErrors] = useState<Record<string, string>>({})
  const [formError, setFormError] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)

  const set = (k: keyof typeof form) => (e: React.ChangeEvent<HTMLInputElement>) =>
    setForm((f) => ({ ...f, [k]: e.target.value }))

  async function submit(e: React.FormEvent) {
    e.preventDefault()
    const next: Record<string, string> = {}
    if (!form.firstName.trim()) next.firstName = 'Enter your first name.'
    if (!form.lastName.trim()) next.lastName = 'Enter your last name.'
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(form.email)) {
      next.email = 'Enter a valid email address.'
    }
    if (form.password.length < MIN_PASSWORD) {
      next.password = `Use at least ${MIN_PASSWORD} characters.`
    }
    if (form.confirm !== form.password) next.confirm = 'Both passwords must match.'
    setErrors(next)
    setFormError(null)
    if (Object.keys(next).length > 0) return

    setSubmitting(true)
    try {
      await register({
        first_name: form.firstName.trim(),
        last_name: form.lastName.trim(),
        email: form.email.trim(),
        password: form.password,
        confirm_password: form.confirm,
      })
      navigate('/', { replace: true })
    } catch (err) {
      setFormError(
        err instanceof ApiError
          ? err.message
          : 'Could not create your account just now.',
      )
      setForm((f) => ({ ...f, password: '', confirm: '' }))
    } finally {
      setSubmitting(false)
    }
  }

  const fields = [
    { k: 'firstName' as const, label: 'First name', type: 'text', ac: 'given-name' },
    { k: 'lastName' as const, label: 'Last name', type: 'text', ac: 'family-name' },
    { k: 'email' as const, label: 'Email', type: 'email', ac: 'email' },
    { k: 'password' as const, label: 'Password', type: 'password', ac: 'new-password' },
    { k: 'confirm' as const, label: 'Confirm password', type: 'password', ac: 'new-password' },
  ]

  return (
    <div className="page section auth-wrap">
      <div className="auth-card">
        <h1>Create your account</h1>
        <p className="muted">Save your favorites and keep your chat history.</p>

        {formError && (
          <div className="alert alert-error" role="alert">{formError}</div>
        )}

        <form onSubmit={submit} noValidate>
          <div className="field-row">
            {fields.slice(0, 2).map((f) => (
              <div className="field" key={f.k}>
                <label htmlFor={f.k}>{f.label}</label>
                <input
                  id={f.k} type={f.type} value={form[f.k]} autoComplete={f.ac}
                  disabled={submitting} onChange={set(f.k)}
                  aria-invalid={Boolean(errors[f.k])}
                  aria-describedby={errors[f.k] ? `${f.k}-err` : undefined}
                />
                {errors[f.k] && <p className="field-err" id={`${f.k}-err`}>{errors[f.k]}</p>}
              </div>
            ))}
          </div>

          {fields.slice(2).map((f) => (
            <div className="field" key={f.k}>
              <label htmlFor={f.k}>{f.label}</label>
              <input
                id={f.k} type={f.type} value={form[f.k]} autoComplete={f.ac}
                disabled={submitting} onChange={set(f.k)}
                aria-invalid={Boolean(errors[f.k])}
                aria-describedby={
                  errors[f.k] ? `${f.k}-err` : f.k === 'password' ? 'pw-hint' : undefined
                }
              />
              {f.k === 'password' && !errors.password && (
                <p className="hint" id="pw-hint">At least {MIN_PASSWORD} characters.</p>
              )}
              {errors[f.k] && <p className="field-err" id={`${f.k}-err`}>{errors[f.k]}</p>}
            </div>
          ))}

          <button className="btn btn-primary auth-submit" type="submit" disabled={submitting}>
            {submitting ? 'Creating account…' : 'Create account'}
          </button>
        </form>

        <p className="auth-alt">
          Already have one? <Link to="/login">Log in</Link>
        </p>
      </div>
    </div>
  )
}
