import { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { 
  company, 
  companySummaries, 
  productsByCompany, 
  getCompanyRecentActivity 
} from '../lib/mockData';
import { Company, CompanySummary, Product } from '@schema/types';

interface CompanyData {
  company: Company;
  summary?: CompanySummary;
  products: Product[];
  recentActivity: Array<{
    type: 'signal' | 'release';
    id: string;
    title: string;
    date: string;
    summary?: string;
    productId?: string;
    signalId?: string;
  }>;
}

export default function CompanyPage() {
  const { companyId } = useParams<{ companyId: string }>();
  const navigate = useNavigate();
  const [data, setData] = useState<CompanyData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!companyId) return;

    const fetchData = async () => {
      try {
        setLoading(true);
        setError(null);

        const [companyData, summaries, products, recentActivity] = await Promise.all([
          company(companyId),
          companySummaries(companyId),
          productsByCompany(companyId),
          getCompanyRecentActivity(companyId)
        ]);

        setData({
          company: companyData,
          summary: summaries[0], // Take first summary if available
          products,
          recentActivity
        });
      } catch (err) {
        console.error('Failed to fetch company data:', err);
        setError('Couldn\'t load company data. Try again.');
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [companyId]);

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      timeZone: 'Europe/Berlin',
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    });
  };

  const handleActivityClick = (item: CompanyData['recentActivity'][0]) => {
    if (item.type === 'signal') {
      navigate(`/signals?company_id=${companyId}&highlight=${item.signalId}`);
    } else if (item.type === 'release' && item.productId) {
      navigate(`/companies/${companyId}/products/${item.productId}`);
    }
  };

  const handleProductClick = (productId: string) => {
    navigate(`/companies/${companyId}/products/${productId}`);
  };

  if (loading) {
    return (
      <div className="container">
        {/* Header Skeleton */}
        <div className="mb-8">
          <div className="h-8 bg-gray-200 rounded w-1/3 mb-4 animate-pulse"></div>
          <div className="h-4 bg-gray-200 rounded w-2/3 mb-2 animate-pulse"></div>
          <div className="h-4 bg-gray-200 rounded w-1/2 mb-4 animate-pulse"></div>
          <div className="h-10 bg-gray-200 rounded w-24 animate-pulse"></div>
        </div>

        {/* Products Grid Skeleton */}
        <div className="mb-8">
          <div className="h-6 bg-gray-200 rounded w-1/4 mb-4 animate-pulse"></div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {[1, 2, 3].map((i) => (
              <div key={i} className="bg-white rounded-lg border border-gray-200 p-6">
                <div className="h-5 bg-gray-200 rounded w-3/4 mb-2 animate-pulse"></div>
                <div className="h-4 bg-gray-200 rounded w-full mb-2 animate-pulse"></div>
                <div className="h-4 bg-gray-200 rounded w-2/3 mb-4 animate-pulse"></div>
                <div className="flex gap-2">
                  <div className="h-6 bg-gray-200 rounded-full w-16 animate-pulse"></div>
                  <div className="h-6 bg-gray-200 rounded-full w-20 animate-pulse"></div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Recent Activity Skeleton */}
        <div>
          <div className="h-6 bg-gray-200 rounded w-1/4 mb-4 animate-pulse"></div>
          <div className="space-y-3">
            {[1, 2, 3, 4].map((i) => (
              <div key={i} className="flex items-start space-x-3 p-4 bg-white rounded-lg border border-gray-200">
                <div className="h-5 bg-gray-200 rounded w-16 animate-pulse"></div>
                <div className="flex-1">
                  <div className="h-4 bg-gray-200 rounded w-3/4 mb-2 animate-pulse"></div>
                  <div className="h-3 bg-gray-200 rounded w-1/4 animate-pulse"></div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="container">
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
          <p className="text-red-800">{error}</p>
        </div>
        <Link 
          to="/companies" 
          className="text-blue-600 hover:text-blue-800 underline"
        >
          ← Back to Companies
        </Link>
      </div>
    );
  }

  if (!data) {
    return (
      <div className="container">
        <div className="text-center py-12">
          <h1 className="text-2xl font-bold text-gray-900 mb-4">Company not found</h1>
          <p className="text-gray-600 mb-6">The company you're looking for doesn't exist.</p>
          <Link 
            to="/companies" 
            className="inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            ← Back to Companies
          </Link>
        </div>
      </div>
    );
  }

  const { company: companyData, summary, products, recentActivity } = data;

  return (
    <div className="container">
      {/* Error Banner */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
          <p className="text-red-800">{error}</p>
        </div>
      )}

      {/* Company Header */}
      <div className="mb-8">
        <div className="flex flex-col lg:flex-row lg:items-start lg:justify-between gap-4">
          <div className="flex-1">
            <h1 className="text-3xl font-bold text-gray-900 mb-2">
              {companyData.name}
            </h1>
            
            {summary?.one_liner && (
              <p className="text-lg text-gray-700 mb-4">
                {summary.one_liner}
              </p>
            )}

            <div className="flex flex-wrap gap-4 text-sm text-gray-600">
              {summary?.founded_year && (
                <span>Founded {summary.founded_year}</span>
              )}
              {summary?.hq_city && companyData.hq_country && (
                <span>HQ: {summary.hq_city}, {companyData.hq_country}</span>
              )}
              {!summary?.hq_city && companyData.hq_country && (
                <span>HQ: {companyData.hq_country}</span>
              )}
              {summary?.employees && (
                <span>{summary.employees} employees</span>
              )}
            </div>
          </div>

          {companyData.website && (
            <a
              href={companyData.website}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
            >
              Website
              <span className="ml-1">↗</span>
            </a>
          )}
        </div>
      </div>

      {/* Products Grid */}
      <div className="mb-12">
        <h2 className="text-2xl font-bold text-gray-900 mb-6">Products</h2>
        
        {products.length === 0 ? (
          <div className="bg-gray-50 rounded-lg p-8 text-center">
            <p className="text-gray-500 text-lg">No products yet.</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
            {products.map((product) => (
              <div
                key={product.id}
                onClick={() => handleProductClick(product.id)}
                className="bg-white rounded-lg border border-gray-200 p-6 hover:shadow-md hover:border-blue-300 cursor-pointer transition-all duration-200"
              >
                <h3 className="text-lg font-semibold text-gray-900 mb-2">
                  {product.name}
                </h3>
                
                {product.short_desc && (
                  <p className="text-sm text-gray-700 mb-4 line-clamp-2">
                    {product.short_desc}
                  </p>
                )}

                <div className="mb-3">
                  <span className="inline-block px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded-full mr-2">
                    {product.category}
                  </span>
                  {product.markets.slice(0, 2).map((market) => (
                    <span
                      key={market}
                      className="inline-block px-2 py-1 bg-gray-100 text-gray-600 text-xs rounded-full mr-2"
                    >
                      {market}
                    </span>
                  ))}
                  {product.markets.length > 2 && (
                    <span className="inline-block px-2 py-1 bg-gray-100 text-gray-600 text-xs rounded-full">
                      +{product.markets.length - 2}
                    </span>
                  )}
                </div>

                {product.tags.length > 0 && (
                  <div className="flex flex-wrap gap-1">
                    {product.tags.slice(0, 3).map((tag) => (
                      <span
                        key={tag}
                        className="px-1.5 py-0.5 bg-gray-50 text-gray-500 text-xs rounded"
                      >
                        {tag}
                      </span>
                    ))}
                    {product.tags.length > 3 && (
                      <span className="px-1.5 py-0.5 bg-gray-50 text-gray-500 text-xs rounded">
                        +{product.tags.length - 3}
                      </span>
                    )}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Recent Activity */}
      <div>
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-2xl font-bold text-gray-900">Recent Activity</h2>
          <Link
            to={`/signals?company_id=${companyId}`}
            className="text-blue-600 hover:text-blue-800 text-sm font-medium"
          >
            View all signals →
          </Link>
        </div>

        {recentActivity.length === 0 ? (
          <div className="bg-gray-50 rounded-lg p-8 text-center">
            <p className="text-gray-500 text-lg">No recent activity in the last 60 days.</p>
          </div>
        ) : (
          <div className="space-y-3">
            {recentActivity.map((item) => (
              <div
                key={`${item.type}-${item.id}`}
                onClick={() => handleActivityClick(item)}
                className="flex items-start space-x-3 p-4 bg-white rounded-lg border border-gray-200 hover:shadow-sm hover:border-blue-300 cursor-pointer transition-all duration-200"
              >
                <span className={`inline-block px-2 py-1 text-xs rounded-full ${
                  item.type === 'signal' 
                    ? 'bg-green-100 text-green-800' 
                    : 'bg-blue-100 text-blue-800'
                }`}>
                  {item.type === 'signal' ? 'Signal' : 'Release'}
                </span>
                
                <div className="flex-1 min-w-0">
                  <h3 className="text-sm font-medium text-gray-900 mb-1 line-clamp-1">
                    {item.title}
                  </h3>
                  {item.summary && (
                    <p className="text-xs text-gray-600 line-clamp-1 mb-1">
                      {item.summary}
                    </p>
                  )}
                  <p className="text-xs text-gray-500">
                    {formatDate(item.date)}
                  </p>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
