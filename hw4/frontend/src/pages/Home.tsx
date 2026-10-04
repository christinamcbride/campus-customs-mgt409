import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import ProductCard from '../components/ProductCard'
import { fetchProducts } from '../api'
import Icon from '../components/Icon'
import type { Product } from '../types'
import './Home.css'

const PROMISES = [
  {
    title: 'Printed on Broadway',
    body:
      'Screen printing and embroidery happen in our own New Haven shop, a short walk from Old Campus. Nothing is drop-shipped from a warehouse that has never seen the Green.',
  },
  {
    title: 'Built to outlast finals',
    body:
      'Heavyweight fleece, double-stitched seams, and prints that survive a few hundred laundry cycles. The sweatshirt should still be around for your fifth reunion.',
  },
  {
    title: 'A family shop since 1973',
    body:
      'Two generations of the same family have sold Yale gear from this block. We still answer the phone, and we still remember regulars by name.',
  },
]

export default function Home() {
  const [featured, setFeatured] = useState<Product[] | null>(null)

  useEffect(() => {
    const ctrl = new AbortController()
    fetchProducts({ limit: 4, inStockOnly: true }, ctrl.signal)
      .then((page) => setFeatured(page.items))
      .catch(() => {
        // Home still reads fine without the strip; ignore aborts.
        if (!ctrl.signal.aborted) setFeatured([])
      })
    return () => ctrl.abort()
  }, [])

  return (
    <>
      <section className="hero">
        <div className="page hero-inner">
          <h1 className="ink-set">
            We print it<span className="hero-break"> </span>
            <em>here.</em>
          </h1>
          <p className="hero-lede ink-set" style={{ '--ink-delay': '110ms' } as React.CSSProperties}>
            Yale sweatshirts, tees and quarter-zips pulled on our own screens on
            Broadway — the same block, the same family, since 1973.
          </p>
          <div
            className="hero-actions ink-set"
            style={{ '--ink-delay': '200ms' } as React.CSSProperties}
          >
            <Link className="btn btn-primary" to="/products">
              Shop the collection
              <Icon name="arrow-right" size={15} strokeWidth={2} />
            </Link>
            <Link className="btn btn-outline hero-secondary" to="/about">Our story</Link>
          </div>

          <dl className="press-run ink-set" style={{ '--ink-delay': '290ms' } as React.CSSProperties}>
            <div><dt>On press since</dt><dd>1973</dd></div>
            <div><dt>Styles in the run</dt><dd>102</dd></div>
            <div><dt>Printed &amp; stitched</dt><dd>In house</dd></div>
          </dl>
        </div>
      </section>

      <section className="page section">
        <div className="section-head">
          <h2>Fresh off the press</h2>
          <Link to="/products">See everything <Icon name="arrow-right" size={13} strokeWidth={2} /></Link>
        </div>
        {featured === null ? (
          <div className="grid">
            {Array.from({ length: 4 }, (_, i) => (
              <div key={i} className="skeleton card-skeleton" aria-hidden="true" />
            ))}
            <span className="sr-only">Loading featured products…</span>
          </div>
        ) : featured.length === 0 ? (
          <p className="muted">
            Featured products are unavailable right now.{' '}
            <Link to="/products">Browse the full catalogue</Link> instead.
          </p>
        ) : (
          <div className="grid">
            {featured.map((p) => (
              <ProductCard key={p.product_id} product={p} />
            ))}
          </div>
        )}
      </section>

      <section className="promises">
        <div className="page">
          <div className="promise-sheet">
            <h2 className="promises-title">
              What you get from a shop that owns its presses
            </h2>
            <div className="promise-rows">
              {PROMISES.map((p) => (
                <div key={p.title} className="promise">
                  <h3>{p.title}</h3>
                  <p>{p.body}</p>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      <section className="page section">
        <div className="cta-band">
          <Icon name="squeegee" size={36} strokeWidth={1.3} className="cta-mark" />
          <div>
            <h2>Not sure what you are after?</h2>
            <p className="muted">
              Ask the counter, bottom right. It reads our actual stock list, so it
              will tell you what is on the shelf — and what has sold through.
            </p>
          </div>
          <Link className="btn btn-primary" to="/products">Start browsing</Link>
        </div>
      </section>
    </>
  )
}
