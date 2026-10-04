import { Link } from 'react-router-dom'
import { formatPrice } from '../api'
import type { Product } from '../types'

/** Trim a description to a card-sized teaser without cutting mid-word. */
function teaser(text: string, max = 96) {
  if (text.length <= max) return text
  const cut = text.slice(0, max)
  return `${cut.slice(0, cut.lastIndexOf(' ')).replace(/[,.;]$/, '')}…`
}

export default function ProductCard({ product }: { product: Product }) {
  const soldOut = product.total_stock === 0

  return (
    <article className="card">
      <Link to={`/products/${product.product_id}`} className="card-link">
        <div className="card-media">
          <img
            src={product.image_url}
            alt={product.name}
            loading="lazy"
            width={600}
            height={600}
          />
          {soldOut && <span className="badge badge-out">Sold out</span>}
        </div>
        <div className="card-body">
          <span className="card-cat">{product.category}</span>
          <h3 className="card-title">{product.name}</h3>
          <p className="card-desc">{teaser(product.description)}</p>
          <div className="card-foot">
            <span className="card-price">{formatPrice(product.price)}</span>
            <span className="card-cta" aria-hidden="true">View details →</span>
          </div>
        </div>
      </Link>
    </article>
  )
}
