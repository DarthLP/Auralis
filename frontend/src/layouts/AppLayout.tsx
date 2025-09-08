import { Outlet, Link, useLocation, useNavigate } from 'react-router-dom'
import GlobalSearchModal from '../components/GlobalSearchModal'
import { useGlobalSearch } from '../hooks/useGlobalSearch'

export default function AppLayout() {
  const location = useLocation()
  const navigate = useNavigate()
  const { isModalOpen, openModal, closeModal } = useGlobalSearch()

  const navItems = [
    { path: '/', label: 'Overview' },
    { path: '/companies', label: 'Companies' },
    { path: '/signals', label: 'Signals' },
    { path: '/releases', label: 'Releases' },
  ]

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b border-gray-200">
        <div className="container">
          <div className="flex items-center justify-between h-16">
            {/* App Name */}
            <div className="flex items-center">
              <h1 className="text-2xl font-bold text-gray-900">AURALIS</h1>
            </div>

            {/* Navigation Links */}
            <nav className="hidden md:flex items-center space-x-8">
              {navItems.map((item) => (
                <Link
                  key={item.path}
                  to={item.path}
                  className={`px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                    location.pathname === item.path
                      ? 'bg-blue-100 text-blue-700'
                      : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
                  }`}
                >
                  {item.label}
                </Link>
              ))}
            </nav>

            {/* Search Button */}
            <button
              onClick={openModal}
              className="flex items-center gap-2 px-3 py-2 text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-md transition-colors"
              title="Search (⌘K)"
            >
              <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
              <span className="hidden sm:inline text-sm">Search</span>
              <kbd className="hidden lg:inline-flex items-center px-1.5 py-0.5 bg-gray-100 border border-gray-300 rounded text-xs font-mono">
                ⌘K
              </kbd>
            </button>

          </div>

          {/* Mobile Navigation */}
          <div className="md:hidden">
            <div className="px-2 pt-2 pb-3 space-y-1 sm:px-3">
              {navItems.map((item) => (
                <Link
                  key={item.path}
                  to={item.path}
                  className={`block px-3 py-2 rounded-md text-base font-medium transition-colors ${
                    location.pathname === item.path
                      ? 'bg-blue-100 text-blue-700'
                      : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
                  }`}
                >
                  {item.label}
                </Link>
              ))}
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="container">
        <Outlet />
      </main>

      {/* Floating Add Competitor Button */}
      <button
        onClick={() => navigate('/competitors/new')}
        className="fixed bottom-6 right-6 bg-blue-600 text-white px-4 py-3 rounded-full shadow-lg hover:bg-blue-700 transition-colors z-50 flex items-center gap-2"
        title="Add Competitor"
      >
        <span className="text-sm font-medium">Add competitor</span>
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
        </svg>
      </button>

      {/* Global Search Modal */}
      <GlobalSearchModal isOpen={isModalOpen} onClose={closeModal} />
    </div>
  )
}
