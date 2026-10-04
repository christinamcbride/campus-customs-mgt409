import { Link } from 'react-router-dom'
import './Footer.css'

export default function Footer() {
  return (
    <footer className="footer">
      <div className="page footer-inner">
        <div>
          <strong className="footer-brand">Campus Customs</strong>
          <p>
            Yale gear printed and stitched in New Haven since 1973.
          </p>
        </div>
        <nav aria-label="Footer">
          <ul>
            <li><Link to="/products">Products</Link></li>
            <li><Link to="/about">About Us</Link></li>
            <li><Link to="/login">Log In</Link></li>
            <li><Link to="/create-account">Create Account</Link></li>
          </ul>
        </nav>
      </div>
      <div className="page footer-note">
        <p>
          A student project for Yale SOM MGT 409. Not affiliated with Yale University.
        </p>
      </div>
    </footer>
  )
}
