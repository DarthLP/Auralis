import React, { Suspense } from 'react'
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import AppLayout from './layouts/AppLayout'

// Lazy load pages for better performance
const Overview = React.lazy(() => import('./pages/Overview'))
const CompaniesIndex = React.lazy(() => import('./pages/CompaniesIndex'))
const CompanyPage = React.lazy(() => import('./pages/CompanyPage'))
const ProductPage = React.lazy(() => import('./pages/ProductPage'))
const SignalsPage = React.lazy(() => import('./pages/SignalsPage'))
const ReleasesPage = React.lazy(() => import('./pages/ReleasesPage'))

// Loading component
function LoadingFallback() {
  return (
    <div className="flex items-center justify-center min-h-64">
      <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      <span className="ml-2 text-gray-600">Loading...</span>
    </div>
  )
}

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<AppLayout />}>
          <Route
            index
            element={
              <Suspense fallback={<LoadingFallback />}>
                <Overview />
              </Suspense>
            }
          />
          <Route
            path="companies"
            element={
              <Suspense fallback={<LoadingFallback />}>
                <CompaniesIndex />
              </Suspense>
            }
          />
          <Route
            path="companies/:companyId"
            element={
              <Suspense fallback={<LoadingFallback />}>
                <CompanyPage />
              </Suspense>
            }
          />
          <Route
            path="companies/:companyId/products/:productId"
            element={
              <Suspense fallback={<LoadingFallback />}>
                <ProductPage />
              </Suspense>
            }
          />
          <Route
            path="signals"
            element={
              <Suspense fallback={<LoadingFallback />}>
                <SignalsPage />
              </Suspense>
            }
          />
          <Route
            path="releases"
            element={
              <Suspense fallback={<LoadingFallback />}>
                <ReleasesPage />
              </Suspense>
            }
          />
        </Route>
      </Routes>
    </Router>
  )
}

export default App