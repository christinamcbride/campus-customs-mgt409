import type { CategoryList, ProductDetail, ProductPage } from './types'

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
    res = await fetch(path, init)
  } catch {
    throw new ApiError(
      "Can't reach the Campus Customs server. Is the backend running?",
      0,
    )
  }
  if (!res.ok) {
    let detail = `Request failed (${res.status})`
    try {
      const body = (await res.json()) as { detail?: unknown }
      if (typeof body.detail === 'string') detail = body.detail
    } catch {
      /* response had no JSON body; keep the status-based message */
    }
    throw new ApiError(detail, res.status)
  }
  return (await res.json()) as T
}

export interface ProductQuery {
  search?: string
  category?: string
  minPrice?: number
  maxPrice?: number
  inStockOnly?: boolean
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
