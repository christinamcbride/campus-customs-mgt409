import { useEffect, useRef } from 'react'
import { useChatResults } from '../chatResults'
import ProductCard from './ProductCard'
import './ChatResults.css'

/**
 * Products the assistant found, rendered on the page as full product cards.
 *
 * Uses the same ProductCard as the catalogue grid, so a card that arrived
 * through chat behaves exactly like one the shopper browsed to: same image,
 * name, price and short description, and the same link to the detail page.
 */
export default function ChatResults() {
  const { products, matchedFor, clear } = useChatResults()
  const regionRef = useRef<HTMLElement>(null)
  const previousCount = useRef(0)

  // Bring new results into view, but never yank the page on first paint.
  useEffect(() => {
    if (products.length > 0 && previousCount.current !== products.length) {
      regionRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' })
    }
    previousCount.current = products.length
  }, [products])

  if (products.length === 0) return null

  return (
    <section ref={regionRef} className="chat-results" aria-labelledby="chat-results-heading">
      <div className="page">
        <div className="chat-results-head">
          <div>
            <h2 id="chat-results-heading">
              {matchedFor ? <>Pulled for “{matchedFor}”</> : 'Pulled from the counter'}
            </h2>
            <p className="muted chat-results-count" role="status" aria-live="polite">
              {products.length} {products.length === 1 ? 'product' : 'products'} the
              assistant looked up. Select one to see full details.
            </p>
          </div>
          <button className="btn btn-outline" onClick={clear}>
            Clear results
          </button>
        </div>

        <div className="grid">
          {products.map((p) => (
            <ProductCard key={p.product_id} product={p} />
          ))}
        </div>
      </div>
    </section>
  )
}
