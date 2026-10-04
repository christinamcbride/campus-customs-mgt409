import { Link } from 'react-router-dom'
import { formatPrice } from '../api'
import type { Product } from '../types'
import Icon from './Icon'

/**
 * Approximate swatches for the colour names the catalogue uses.
 *
 * The names are inconsistent on purpose-built data ("navy" and "navy blue"
 * both appear, grey six ways), so matching is by substring against the
 * longest keys first.
 */
const INKS: [string, string][] = [
  ['dark heather gray', '#8a8d93'],
  ['heather charcoal gray', '#55585e'],
  ['heather gray', '#a8a9ad'],
  ['charcoal gray', '#4a4d52'],
  ['light gray', '#c9cacd'],
  ['navy blue', '#17223f'],
  ['navy', '#17223f'],
  ['maroon', '#6d2230'],
  ['crimson', '#9e2232'],
  ['orange', '#cf6a28'],
  ['purple', '#5b3a7e'],
  ['yellow', '#d6a92c'],
  ['green', '#2b6145'],
  ['black', '#1b1c1f'],
  ['white', '#fbf9f4'],
  ['cream', '#efe6d2'],
  ['blue', '#2f5490'],
  ['gray', '#9a9ca1'],
  ['grey', '#9a9ca1'],
  ['gold', '#c8a24a'],
  ['pink', '#d78aa0'],
  ['red', '#a8342c'],
  ['tan', '#c6a884'],
]

function inkFor(name: string): string | null {
  const n = name.toLowerCase()
  for (const [key, hex] of INKS) {
    if (n.includes(key)) return hex
  }
  return null
}

/** Trim a description to a card-sized teaser without cutting mid-word. */
function teaser(text: string, max = 92) {
  if (text.length <= max) return text
  const cut = text.slice(0, max)
  return `${cut.slice(0, cut.lastIndexOf(' ')).replace(/[,.;]$/, '')}…`
}

export default function ProductCard({ product }: { product: Product }) {
  const soldOut = product.total_stock === 0
  const inks = product.colors
    .map((c) => ({ name: c, hex: inkFor(c) }))
    .filter((c): c is { name: string; hex: string } => c.hex !== null)
    .slice(0, 5)

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
          {soldOut && <span className="badge badge-out">Out of run</span>}
        </div>
        <div className="card-body">
          <span className="card-cat">{product.category}</span>
          <h3 className="card-title">{product.name}</h3>

          {inks.length > 0 && (
            <div className="card-inks" aria-label={`Colours: ${product.colors.join(', ')}`}>
              {inks.map((ink) => (
                <span
                  key={ink.name}
                  className="ink-chip"
                  style={{ background: ink.hex }}
                  title={ink.name}
                />
              ))}
            </div>
          )}

          <p className="card-desc">{teaser(product.description)}</p>

          <div className="card-foot">
            <span className="card-price">{formatPrice(product.price)}</span>
            <span className="card-cta">
              Details
              <Icon name="arrow-right" size={13} strokeWidth={2} />
            </span>
          </div>
        </div>
      </Link>
    </article>
  )
}
