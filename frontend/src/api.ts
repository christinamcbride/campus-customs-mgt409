import type {
  CategoryList,
  ChatHistoryMessage,
  ChatReply,
  PageContext,
  ProductDetail,
  ProductPage,
  RegisterInput,
  User,
} from './types'

/** Thrown for any non-2xx response so callers can show a real message. */
export class ApiError extends Error {
  readonly status: number

  constructor(message: string, status: number) {
    super(message)
    this.name = 'ApiError'
    this.status = status
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let res: Response
  try {
    res = await fetch(path, { credentials: 'same-origin', ...init })
  } catch {
    throw new ApiError(
      "Can't reach the Campus Customs server. Is the backend running?",
      0,
    )
  }
  if (!res.ok) {
    throw new ApiError(await readError(res), res.status)
  }
  if (res.status === 204) return undefined as T
  return (await res.json()) as T
}

export interface ProductQuery {
  search?: string
  category?: string
  minPrice?: number
  maxPrice?: number
  inStockOnly?: boolean
  sort?: string
  limit?: number
  offset?: number
}

export function fetchProducts(q: ProductQuery = {}, signal?: AbortSignal) {
  const p = new URLSearchParams()
  if (q.search) p.set('search', q.search)
  if (q.category && q.category !== 'All') p.set('category', q.category)
  if (q.minPrice != null) p.set('min_price', String(q.minPrice))
  if (q.maxPrice != null) p.set('max_price', String(q.maxPrice))
  if (q.inStockOnly) p.set('in_stock_only', 'true')
  if (q.sort && q.sort !== 'name') p.set('sort', q.sort)
  p.set('limit', String(q.limit ?? 48))
  p.set('offset', String(q.offset ?? 0))
  return request<ProductPage>(`/api/products?${p}`, { signal })
}

export function fetchProduct(id: string, signal?: AbortSignal) {
  return request<ProductDetail>(`/api/products/${encodeURIComponent(id)}`, { signal })
}

export function fetchCategories(signal?: AbortSignal) {
  return request<CategoryList>('/api/categories', { signal })
}

export const formatPrice = (value: number) =>
  value.toLocaleString('en-US', { style: 'currency', currency: 'USD' })


/**
 * Turn an error response into one readable sentence.
 *
 * FastAPI returns `detail` as a string for our own HTTPExceptions, but as a
 * list of field errors for validation failures, so both shapes are handled.
 */
async function readError(res: Response): Promise<string> {
  try {
    const body = (await res.json()) as { detail?: unknown }
    const { detail } = body
    if (typeof detail === 'string') return detail
    if (Array.isArray(detail)) {
      const messages = detail
        .map((d) => {
          const item = d as { loc?: unknown[]; msg?: string }
          const field = Array.isArray(item.loc) ? String(item.loc.at(-1)) : ''
          const label = FIELD_LABELS[field] ?? field
          const msg = item.msg?.replace(/^Value error, /, '') ?? 'is invalid'
          return label ? `${label}: ${msg}` : msg
        })
        .filter(Boolean)
      if (messages.length) return messages.join('. ')
    }
  } catch {
    /* no JSON body; fall through to the status-based message */
  }
  if (res.status === 401) return 'Incorrect email or password.'
  return `Request failed (${res.status})`
}

const FIELD_LABELS: Record<string, string> = {
  first_name: 'First name',
  last_name: 'Last name',
  email: 'Email',
  password: 'Password',
  confirm_password: 'Password confirmation',
}

// ---- Accounts ----

export function register(input: RegisterInput) {
  return request<User>('/api/auth/register', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(input),
  })
}

export function login(email: string, password: string) {
  return request<User>('/api/auth/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password }),
  })
}

export function logout() {
  return request<void>('/api/auth/logout', { method: 'POST' })
}

export function fetchMe(signal?: AbortSignal) {
  return request<User>('/api/auth/me', { signal })
}

// ---- Shopping assistant ----

export function sendChatMessage(
  message: string,
  pageContext?: PageContext,
  signal?: AbortSignal,
) {
  return request<ChatReply>('/api/chat', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message, page_context: pageContext ?? null }),
    signal,
  })
}

export function fetchChatHistory(signal?: AbortSignal) {
  return request<ChatHistoryMessage[]>('/api/chat/history', { signal })
}
