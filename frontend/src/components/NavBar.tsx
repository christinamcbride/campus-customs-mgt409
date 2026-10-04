import { useEffect, useRef, useState } from 'react'
import { NavLink } from 'react-router-dom'
import './NavBar.css'

const LINKS = [
  { to: '/', label: 'Home', end: true },
  { to: '/products', label: 'Products' },
  { to: '/about', label: 'About Us' },
]

const ACCOUNT_LINKS = [
  { to: '/login', label: 'Log In' },
  { to: '/create-account', label: 'Create Account' },
]

export default function NavBar() {
  const [open, setOpen] = useState(false)
  const toggleRef = useRef<HTMLButtonElement>(null)

  // Escape closes the menu and returns focus to the control that opened it.
  useEffect(() => {
    if (!open) return
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        setOpen(false)
        toggleRef.current?.focus()
      }
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [open])

  return (
    <header className="nav">
      <div className="nav-inner page">
        <NavLink to="/" className="brand" aria-label="Campus Customs — home">
          <span className="brand-mark" aria-hidden="true">CC</span>
          <span className="brand-text">
            <strong>Campus Customs</strong>
            <small>New Haven, est. 1973</small>
          </span>
        </NavLink>

        <button
          ref={toggleRef}
          className="nav-toggle"
          aria-expanded={open}
          aria-controls="primary-navigation"
          onClick={() => setOpen((v) => !v)}
        >
          <span aria-hidden="true">{open ? '✕' : '☰'}</span>
          <span className="sr-only">{open ? 'Close menu' : 'Open menu'}</span>
        </button>

        <nav
          id="primary-navigation"
          className={open ? 'nav-links open' : 'nav-links'}
          aria-label="Primary"
        >
          <ul className="nav-primary">
            {LINKS.map((l) => (
              <li key={l.to}>
                <NavLink to={l.to} end={l.end} onClick={() => setOpen(false)}>
                  {l.label}
                </NavLink>
              </li>
            ))}
          </ul>
          <ul className="nav-account">
            {ACCOUNT_LINKS.map((l, i) => (
              <li key={l.to}>
                <NavLink
                  to={l.to}
                  className={i === 1 ? 'cta' : undefined}
                  onClick={() => setOpen(false)}
                >
                  {l.label}
                </NavLink>
              </li>
            ))}
          </ul>
        </nav>
      </div>
    </header>
  )
}
