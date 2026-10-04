import { Link } from 'react-router-dom'
import './About.css'

const FACTS = [
  { label: 'On Broadway since', value: '1973' },
  { label: 'Family-run generations', value: 'Two' },
  { label: 'Printed & stitched', value: 'In house' },
]

export default function About() {
  return (
    <>
      <section className="about-hero">
        <div className="page">
          <h1>Half a century of outfitting the Elm City.</h1>
          <p className="about-lede">
            Campus Customs has sold Yale gear from the same New Haven block since 1973.
            We started as a small memorabilia counter and grew into a full print shop —
            but the counter is still there, and so are we.
          </p>
        </div>
      </section>

      <section className="page about-body">
        <div className="about-main">
          <h2>What we actually do</h2>
          <p>
            Most of what you see here is made in our own facility: screen printing,
            embroidery, and graphic design under one roof. That means we control the
            garment, the ink, and the stitch count, and it means a rush order for a
            team or a reunion does not have to cross the country twice before it
            reaches you.
          </p>
          <p>
            We stock the classics — heavyweight crewnecks, pullover hoodies,
            quarter-zips, and cotton tees — in the colors people on this campus
            actually wear. Residential colleges, graduate and professional schools,
            varsity teams, and the family lineup of Yale Mom, Dad, Grandpa, and Aunt
            shirts are all part of the regular run.
          </p>

          <h2>How we think about quality</h2>
          <p>
            A sweatshirt bought during someone's first year should still be wearable at
            their fifth reunion. We choose garments for weight and durability rather
            than for the lowest unit cost, and we would rather tell you a size is out
            of stock than send you something that does not fit the way it should.
          </p>

          <h2>Straight answers</h2>
          <p>
            That honesty applies to our shopping assistant too. It reads from our live
            stock list, so when it says a size is gone, it is gone — and when we do not
            carry something, it will say so instead of guessing. We would rather point
            you somewhere useful than make a sale that comes back in the mail.
          </p>

          <p className="about-close">
            Stop by the shop on Broadway, or{' '}
            <Link to="/products">browse the collection</Link> from wherever you are.
          </p>
        </div>

        <aside className="about-aside" aria-label="At a glance">
          <h2 className="aside-title">At a glance</h2>
          <dl className="facts">
            {FACTS.map((f) => (
              <div key={f.label} className="fact">
                <dt>{f.label}</dt>
                <dd>{f.value}</dd>
              </div>
            ))}
          </dl>
          <div className="visit">
            <h3>Visit the shop</h3>
            <p>
              Broadway, New Haven, Connecticut<br />
              A short walk from Old Campus.
            </p>
          </div>
        </aside>
      </section>
    </>
  )
}
