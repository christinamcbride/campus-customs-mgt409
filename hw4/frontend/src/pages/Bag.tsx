import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { fetchProduct, formatPrice } from '../api'
import { useBag } from '../bag'
import Icon from '../components/Icon'
import './Bag.css'

/** How many of each bagged size the database still has. */
type StockMap = Record<string, number>

const key = (productId: string, size: string) => `${productId}::${size}`

export default function Bag() {
  const { lines, count, subtotal, setQuantity, remove, clear } = useBag()
  const [stock, setStock] = useState<StockMap | null>(null)

  // Re-check stock whenever the bag changes. A size can sell through after it
  // was bagged, and the shop should say so rather than quietly accept an
  // order it cannot fill.
  useEffect(() => {
    if (lines.length === 0) {
      setStock({})
      return
    }
    const ctrl = new AbortController()
    const ids = [...new Set(lines.map((l) => l.product_id))]
    Promise.all(
      ids.map((id) =>
        fetchProduct(id, ctrl.signal)
          .then((p) => [id, p] as const)
          .catch(() => null),
      ),
    )
      .then((results) => {
        if (ctrl.signal.aborted) return
        const map: StockMap = {}
        for (const entry of results) {
          if (!entry) continue
          const [id, product] = entry
          for (const s of product.sizes) map[key(id, s.size)] = s.quantity
        }
        setStock(map)
      })
      .catch(() => {
        if (!ctrl.signal.aborted) setStock(null)
      })
    return () => ctrl.abort()
  }, [lines])

  if (lines.length === 0) {
    return (
      <div className="page section empty-state">
        <h1>Your bag is empty</h1>
        <p>Nothing bagged yet. The whole collection is a click away.</p>
        <Link className="btn btn-primary" to="/products">
          Browse the collection
          <Icon name="arrow-right" size={15} strokeWidth={2} />
        </Link>
      </div>
    )
  }

  return (
    <div className="page section">
      <header className="bag-head">
        <h1>Your bag</h1>
        <p className="muted">
          {count} {count === 1 ? 'item' : 'items'} held for you. Stock is
          re-checked against the shop every time you open this page.
        </p>
      </header>

      <ul className="bag-lines">
        {lines.map((line) => {
          const available = stock?.[key(line.product_id, line.size)]
          const soldOut = available === 0
          const short = available !== undefined && available > 0 && available < line.quantity

          return (
            <li key={key(line.product_id, line.size)} className="bag-line">
              <Link to={`/products/${line.product_id}`} className="bag-thumb">
                <img src={line.image_url} alt="" width={96} height={96} loading="lazy" />
              </Link>

              <div className="bag-detail">
                <Link to={`/products/${line.product_id}`} className="bag-name">
                  {line.name}
                </Link>
                <p className="bag-meta">
                  Size {line.size} · {formatPrice(line.price)} each
                </p>

                {soldOut && (
                  <p className="bag-warn" role="status">
                    This size has sold out since you bagged it. Remove it to check out
                    the rest.
                  </p>
                )}
                {short && (
                  <p className="bag-warn" role="status">
                    Only {available} left in {line.size} — reduce the quantity to
                    continue.
                  </p>
                )}
              </div>

              <div className="bag-qty">
                <label htmlFor={`qty-${key(line.product_id, line.size)}`}>
                  Qty
                </label>
                <input
                  id={`qty-${key(line.product_id, line.size)}`}
                  type="number"
                  min={1}
                  max={available && available > 0 ? available : undefined}
                  value={line.quantity}
                  onChange={(e) =>
                    setQuantity(
                      line.product_id,
                      line.size,
                      Math.max(1, Number(e.target.value) || 1),
                    )
                  }
                />
              </div>

              <div className="bag-line-total tabular">
                {formatPrice(line.price * line.quantity)}
              </div>

              <button
                className="bag-remove"
                onClick={() => remove(line.product_id, line.size)}
              >
                <Icon name="close" size={15} strokeWidth={1.9} />
                <span className="sr-only">
                  Remove {line.name}, size {line.size}
                </span>
              </button>
            </li>
          )
        })}
      </ul>

      <div className="bag-foot">
        <button className="btn btn-ghost" onClick={clear}>
          Empty the bag
        </button>

        <div className="bag-summary">
          <div className="bag-subtotal">
            <span>Subtotal</span>
            <strong className="tabular">{formatPrice(subtotal)}</strong>
          </div>
          <p className="bag-note">
            Checkout is not part of this build, so nothing here is reserved or
            charged. Come by the shop on Broadway, and these sizes and prices
            will be what we have on the shelf.
          </p>
          <Link className="btn btn-outline" to="/products">
            Keep browsing
          </Link>
        </div>
      </div>
    </div>
  )
}
