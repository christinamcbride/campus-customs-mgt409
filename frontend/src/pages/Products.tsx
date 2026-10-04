import { useEffect, useMemo, useRef, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import ProductCard from '../components/ProductCard'
import { ApiError, fetchCategories, fetchProducts } from '../api'
import type { CategoryList, Product } from '../types'
import './Products.css'

const PAGE_SIZE = 24

export default function Products() {
  const [params, setParams] = useSearchParams()
  const search = params.get('search') ?? ''
  const category = params.get('category') ?? 'All'
  const inStockOnly = params.get('in_stock') === '1'

  const [draft, setDraft] = useState(search)
  const [items, setItems] = useState<Product[]>([])
  const [total, setTotal] = useState(0)
  const [visible, setVisible] = useState(PAGE_SIZE)
  const [meta, setMeta] = useState<CategoryList | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const firstRender = useRef(true)

  // Keep the box in sync when the URL changes from outside (e.g. back button).
  useEffect(() => setDraft(search), [search])

  useEffect(() => {
    const ctrl = new AbortController()
    fetchCategories(ctrl.signal)
      .then(setMeta)
      .catch(() => {
        // An abort is not a failure: the next effect run will refetch.
        if (!ctrl.signal.aborted) setMeta(null)
      })
    return () => ctrl.abort()
  }, [])

  // Debounce the typed query so we are not firing a request per keystroke.
  useEffect(() => {
    if (firstRender.current) {
      firstRender.current = false
      return
    }
    const id = window.setTimeout(() => {
      const next = new URLSearchParams(params)
      if (draft.trim()) next.set('search', draft.trim())
      else next.delete('search')
      setParams(next, { replace: true })
    }, 300)
    return () => window.clearTimeout(id)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [draft])

  useEffect(() => {
    const ctrl = new AbortController()
    setLoading(true)
    setError(null)
    fetchProducts(
      { search, category, inStockOnly, limit: 120, offset: 0 },
      ctrl.signal,
    )
      .then((page) => {
        setItems(page.items)
        setTotal(page.total)
        setVisible(PAGE_SIZE)
      })
      .catch((err: unknown) => {
        if (ctrl.signal.aborted) return
        setError(
          err instanceof ApiError
            ? err.message
            : 'Something went wrong loading the catalogue.',
        )
        setItems([])
        setTotal(0)
      })
      .finally(() => {
        if (!ctrl.signal.aborted) setLoading(false)
      })
    return () => ctrl.abort()
  }, [search, category, inStockOnly])

  const shown = useMemo(() => items.slice(0, visible), [items, visible])

  function setParam(key: string, value: string | null) {
    const next = new URLSearchParams(params)
    if (value) next.set(key, value)
    else next.delete(key)
    setParams(next, { replace: true })
  }

  const filtersActive = Boolean(search) || category !== 'All' || inStockOnly

  return (
    <div className="page section">
      <header className="products-head">
        <div>
          <h1>The Collection</h1>
          <p className="muted">
            Printed and stitched in New Haven. Every price and stock count here comes
            straight from our shop inventory.
          </p>
        </div>
      </header>

      <div className="filters">
        <div className="filter-search">
          <label htmlFor="product-search" className="sr-only">Search products</label>
          <input
            id="product-search"
            type="search"
            value={draft}
            onChange={(e) => setDraft(e.target.value)}
            placeholder="Search by name, color, team, or school…"
          />
        </div>

        <div className="filter-cats" role="group" aria-label="Filter by category">
          {['All', ...(meta?.categories ?? [])].map((c) => (
            <button
              key={c}
              className={c === category ? 'chip chip-active' : 'chip'}
              aria-pressed={c === category}
              onClick={() => setParam('category', c === 'All' ? null : c)}
            >
              {c}
            </button>
          ))}
        </div>

        <label className="filter-stock">
          <input
            type="checkbox"
            checked={inStockOnly}
            onChange={(e) => setParam('in_stock', e.target.checked ? '1' : null)}
          />
          In stock only
        </label>
      </div>

      <p className="result-count" role="status" aria-live="polite">
        {loading
          ? 'Loading products…'
          : `${total} ${total === 1 ? 'product' : 'products'}${filtersActive ? ' match your filters' : ''}`}
      </p>

      {error && (
        <div className="alert alert-error" role="alert">
          {error}
        </div>
      )}

      {loading ? (
        <div className="grid">
          {Array.from({ length: 8 }, (_, i) => (
            <div key={i} className="skeleton card-skeleton" aria-hidden="true" />
          ))}
        </div>
      ) : !error && items.length === 0 ? (
        <div className="empty-state">
          <h3>No products match that search</h3>
          <p>Try a different word, or clear the filters to see everything.</p>
          {filtersActive && (
            <button className="btn btn-outline" onClick={() => setParams({}, { replace: true })}>
              Clear filters
            </button>
          )}
        </div>
      ) : (
        <>
          <div className="grid">
            {shown.map((p) => (
              <ProductCard key={p.product_id} product={p} />
            ))}
          </div>
          {visible < items.length && (
            <div className="load-more">
              <button
                className="btn btn-outline"
                onClick={() => setVisible((v) => v + PAGE_SIZE)}
              >
                Show more ({items.length - visible} remaining)
              </button>
            </div>
          )}
        </>
      )}
    </div>
  )
}
