import React from 'react'
import { Link, useLocation } from 'react-router-dom'

export default function Navigation() {
  const location = useLocation()

  const navItems = [
    { path: '/', label: 'Overview' },
    { path: '/companies', label: 'Companies' },
    { path: '/signals', label: 'Signals' },
    { path: '/releases', label: 'Releases' },
  ]

  return (
    <nav style={{ 
      borderBottom: '1px solid #ccc', 
      padding: '1rem',
      marginBottom: '2rem',
      backgroundColor: '#f8f9fa'
    }}>
      <div style={{ display: 'flex', gap: '2rem', alignItems: 'center' }}>
        <h2 style={{ margin: 0, color: '#333' }}>Auralis</h2>
        <div style={{ display: 'flex', gap: '1rem' }}>
          {navItems.map((item) => (
            <Link
              key={item.path}
              to={item.path}
              style={{
                textDecoration: 'none',
                color: location.pathname === item.path ? '#007bff' : '#666',
                fontWeight: location.pathname === item.path ? 'bold' : 'normal',
                padding: '0.5rem 1rem',
                borderRadius: '4px',
                transition: 'background-color 0.2s',
              }}
              onMouseEnter={(e) => {
                if (location.pathname !== item.path) {
                  e.currentTarget.style.backgroundColor = '#e9ecef'
                }
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.backgroundColor = 'transparent'
              }}
            >
              {item.label}
            </Link>
          ))}
        </div>
      </div>
    </nav>
  )
}
