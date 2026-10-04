import { Link } from 'react-router-dom'

export default function NotFound() {
  return (
    <div className="page section empty-state">
      <h1>Page not found</h1>
      <p>That link doesn't lead anywhere on our shop.</p>
      <Link className="btn btn-primary" to="/">Back to the shop</Link>
    </div>
  )
}
