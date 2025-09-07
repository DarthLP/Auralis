import React from 'react'
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import Navigation from './components/Navigation'
import Overview from './pages/Overview'
import CompaniesIndex from './pages/CompaniesIndex'
import CompanyPage from './pages/CompanyPage'
import ProductPage from './pages/ProductPage'
import SignalsPage from './pages/SignalsPage'
import ReleasesPage from './pages/ReleasesPage'

function App() {
  return (
    <Router>
      <div className="App">
        <Navigation />
        <main style={{ padding: '0 2rem' }}>
          <Routes>
            <Route path="/" element={<Overview />} />
            <Route path="/companies" element={<CompaniesIndex />} />
            <Route path="/companies/:companyId" element={<CompanyPage />} />
            <Route path="/companies/:companyId/products/:productId" element={<ProductPage />} />
            <Route path="/signals" element={<SignalsPage />} />
            <Route path="/releases" element={<ReleasesPage />} />
          </Routes>
        </main>
      </div>
    </Router>
  )
}

export default App
