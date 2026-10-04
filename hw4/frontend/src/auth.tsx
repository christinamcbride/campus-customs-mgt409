import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
} from 'react'
import * as api from './api'
import type { RegisterInput, User } from './types'

interface AuthState {
  user: User | null
  /** True until the initial session check finishes, so the nav can avoid flicker. */
  loading: boolean
  login: (email: string, password: string) => Promise<void>
  register: (input: RegisterInput) => Promise<void>
  logout: () => Promise<void>
}

const AuthContext = createContext<AuthState | null>(null)

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)

  // Restore the session on first load. A 401 just means "not signed in".
  useEffect(() => {
    const ctrl = new AbortController()
    api
      .fetchMe(ctrl.signal)
      .then(setUser)
      .catch(() => {
        if (!ctrl.signal.aborted) setUser(null)
      })
      .finally(() => {
        if (!ctrl.signal.aborted) setLoading(false)
      })
    return () => ctrl.abort()
  }, [])

  const login = useCallback(async (email: string, password: string) => {
    setUser(await api.login(email, password))
  }, [])

  const register = useCallback(async (input: RegisterInput) => {
    setUser(await api.register(input))
  }, [])

  const logout = useCallback(async () => {
    try {
      await api.logout()
    } finally {
      // Clear locally even if the request failed; the cookie may already be gone.
      setUser(null)
    }
  }, [])

  const value = useMemo(
    () => ({ user, loading, login, register, logout }),
    [user, loading, login, register, logout],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth(): AuthState {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used inside <AuthProvider>')
  return ctx
}
