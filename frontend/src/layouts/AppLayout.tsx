import { Outlet, Link, useLocation } from 'react-router-dom'

export default function AppLayout() {
  const location = useLocation()

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

            {/* Right Side - Open Source Drawer Button */}
            <div className="flex items-center">
              <button
                onClick={() => {
                  // Placeholder no-op function
                  console.log('Open Source Drawer clicked')
                }}
                className="px-4 py-2 text-sm font-medium text-gray-600 bg-white border border-gray-300 rounded-md hover:bg-gray-50 hover:text-gray-900 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 transition-colors"
              >
                Open Source Drawer
              </button>
            </div>
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
    </div>
  )
}
