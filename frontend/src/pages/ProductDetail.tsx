import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { ApiError, fetchProduct, formatPrice } from '../api'
import type { ProductDetail as Detail } from '../types'
import './ProductDetail.css'

export default function ProductDetail() {
  const { productId = '' } = useParams()
  const [product, setProduct] = useState<Detail | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [notFound, setNotFound] = useState(false)
  const [chosenSize, setChosenSize] = useState<string | null>(null)

  useEffect(() => {
    const ctrl = new AbortController()
    setLoading(true)
    setError(null)
    setNotFound(false)
    setChosenSize(null)
    window.scrollTo({ top: 0 })

    fetchProduct(productId, ctrl.signal)
      .then(setProduct)
      .catch((err: unknown) => {
        if (ctrl.signal.aborted) return
        if (err instanceof ApiError && err.status === 404) setNotFound(true)
        else
          setError(
            err instanceof ApiError ? err.message : 'Could not load this product.',
          )
      })
      .finally(() => {
        if (!ctrl.signal.aborted) setLoading(false)
      })
    return () => ctrl.abort()
  }, [productId])

  if (loading) {
    return (
      <div className="page section detail-grid" aria-busy="true">
        <div className="skeleton detail-media-skeleton" />
        <div>
          <div className="skeleton line line-lg" />
          <div className="skeleton line line-md" />
          <div className="skeleton line" />
          <div className="skeleton line" />
        </div>
        <span className="sr-only">Loading product…</span>
      </div>
    )
  }

  if (notFound) {
    return (
      <div className="page section empty-state">
        <h1>We couldn't find that product</h1>
        <p>It may have sold through or the link may be out of date.</p>
        <Link className="btn btn-primary" to="/products">Back to the collection</Link>
      </div>
    )
  }

  if (error || !product) {
    return (
      <div className="page section">
        <div className="alert alert-error" role="alert">{error}</div>
        <Link className="btn btn-outline" to="/products">Back to the collection</Link>
      </div>
    )
  }

  const available = product.sizes.filter((s) => s.in_stock)
  const soldOut = product.sizes.filter((s) => !s.in_stock)
  const allGone = available.length === 0

  return (
    <div className="page section">
      <nav className="crumbs" aria-label="Breadcrumb">
        <Link to="/products">Collection</Link>
        <span aria-hidden="true">/</span>
        <Link to={`/products?category=${encodeURIComponent(product.category)}`}>
          {product.category}
        </Link>
        <span aria-hidden="true">/</span>
        <span aria-current="page">{product.name}</span>
      </nav>

      <div className="detail-grid">
        <div className="detail-media">
          <img src={product.image_url} alt={product.name} width={900} height={900} />
        </div>

        <div className="detail-info">
          <span className="detail-cat">{product.category}</span>
          <h1>{product.name}</h1>
          <p className="detail-price">{formatPrice(product.price)}</p>

          <p className="detail-desc">{product.description}</p>

          <dl className="spec">
            <div>
              <dt>Garment</dt>
              <dd>{product.garment_type}</dd>
            </div>
            <div>
              <dt>Colors</dt>
              <dd>{product.colors.join(', ')}</dd>
            </div>
          </dl>

          <section className="sizes" aria-labelledby="sizes-heading">
            <div className="sizes-head">
              <h2 id="sizes-heading">Sizes</h2>
              {allGone ? (
                <span className="stock-note stock-none">Currently sold out</span>
              ) : (
                <span className="stock-note">
                  {available.length} of {product.sizes.length} sizes in stock
                </span>
              )}
            </div>

            <div className="size-row" role="group" aria-label="Choose a size">
              {product.sizes.map((s) => (
                <button
                  key={s.size}
                  className={[
                    'size-btn',
                    !s.in_stock ? 'size-out' : '',
                    chosenSize === s.size ? 'size-chosen' : '',
                  ].filter(Boolean).join(' ')}
                  disabled={!s.in_stock}
                  aria-pressed={chosenSize === s.size}
                  onClick={() => setChosenSize(s.size)}
                >
                  {s.size}
                  <span className="sr-only">
                    {s.in_stock ? `, ${s.quantity} in stock` : ', sold out'}
                  </span>
                </button>
              ))}
            </div>

            <p className="size-detail" role="status" aria-live="polite">
              {chosenSize
                ? (() => {
                    const s = product.sizes.find((x) => x.size === chosenSize)!
                    return s.quantity <= 3
                      ? `Size ${s.size} — only ${s.quantity} left.`
                      : `Size ${s.size} — ${s.quantity} in stock.`
                  })()
                : soldOut.length > 0
                  ? `Sold out in ${soldOut.map((s) => s.size).join(', ')}.`
                  : 'Every size is currently in stock.'}
            </p>

            <button className="btn btn-primary add-btn" disabled={!chosenSize}>
              {chosenSize ? `Add size ${chosenSize} to bag` : 'Select a size'}
            </button>
            <p className="checkout-note">
              Checkout isn't live in this build — sizes and stock shown above are read
              from our live inventory.
            </p>
          </section>

          {product.search_tags.length > 0 && (
            <div className="tags" aria-label="Related searches">
              {product.search_tags.slice(0, 8).map((t) => (
                <Link key={t} to={`/products?search=${encodeURIComponent(t)}`} className="tag">
                  {t}
                </Link>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
