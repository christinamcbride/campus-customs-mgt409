import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import ProductCard from '../components/ProductCard'
import { fetchProducts } from '../api'
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
          <p className="eyebrow">New Haven · Est. 1973</p>
          <h1>Yale gear, made a few blocks from the Green.</h1>
          <p className="hero-lede">
            Sweatshirts, tees, and quarter-zips for students, families, and alumni who
            want the real thing — pressed and stitched in our own shop on Broadway,
            not ordered from a catalogue.
          </p>
          <div className="hero-actions">
            <Link className="btn btn-primary" to="/products">Shop the collection</Link>
            <Link className="btn btn-outline hero-secondary" to="/about">Our story</Link>
          </div>
        </div>
      </section>

      <section className="page section">
        <div className="section-head">
          <h2>Fresh off the press</h2>
          <Link to="/products">See everything →</Link>
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
          <h2 className="promises-title">Why shop with us</h2>
          <div className="promise-grid">
            {PROMISES.map((p) => (
              <div key={p.title} className="promise">
                <h3>{p.title}</h3>
                <p>{p.body}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="page section cta-band">
        <div>
          <h2>Not sure what you want?</h2>
          <p className="muted">
            Ask our shopping assistant, bottom right. It reads straight from our stock
            list, so it will tell you what is actually on the shelf — and what is not.
          </p>
        </div>
        <Link className="btn btn-primary" to="/products">Start browsing</Link>
      </section>
    </>
  )
}
