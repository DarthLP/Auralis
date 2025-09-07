import { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { 
  product, 
  productCapabilities as fetchProductCapabilities, 
  capabilities,
  company 
} from '../lib/mockData';
import { Product, ProductCapability, Capability, Company } from '@schema/types';

// Extended maturity type to handle seed data
type ExtendedMaturity = 'basic' | 'intermediate' | 'advanced' | 'expert' | 'ga' | 'alpha' | 'beta';

interface ProductData {
  product: Product;
  company: Company;
  productCapabilities: ProductCapability[];
  capabilities: Capability[];
}

const maturityColors: Record<ExtendedMaturity, string> = {
  basic: 'bg-gray-100 text-gray-800',
  intermediate: 'bg-yellow-100 text-yellow-800',
  advanced: 'bg-blue-100 text-blue-800',
  expert: 'bg-green-100 text-green-800',
  ga: 'bg-green-100 text-green-800', // Handle seed data maturity values
  alpha: 'bg-red-100 text-red-800',
  beta: 'bg-yellow-100 text-yellow-800'
};

const maturityLabels: Record<ExtendedMaturity, string> = {
  basic: 'Basic',
  intermediate: 'Intermediate', 
  advanced: 'Advanced',
  expert: 'Expert',
  ga: 'GA', // Handle seed data maturity values
  alpha: 'Alpha',
  beta: 'Beta'
};

export default function ProductPage() {
  const { companyId, productId } = useParams<{ companyId: string; productId: string }>();
  const [data, setData] = useState<ProductData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [notFound, setNotFound] = useState(false);

  useEffect(() => {
    if (!companyId || !productId) return;

    const fetchData = async () => {
      try {
        setLoading(true);
        setError(null);
        setNotFound(false);

        // Fetch product first to validate company_id
        let productData;
        try {
          productData = await product(productId);
        } catch (err) {
          console.error('Error fetching product:', err);
          throw new Error(`Failed to fetch product: ${err instanceof Error ? err.message : String(err)}`);
        }
        
        // Check if product belongs to the specified company
        if (productData.company_id !== companyId) {
          setNotFound(true);
          setLoading(false);
          return;
        }

        // Fetch all related data in parallel
        let companyData, productCaps, allCapabilities;
        try {
          [companyData, productCaps, allCapabilities] = await Promise.all([
            company(companyId),
            fetchProductCapabilities(productId),
            capabilities()
          ]);
        } catch (err) {
          console.error('Error fetching related data:', err);
          throw new Error(`Failed to fetch related data: ${err instanceof Error ? err.message : String(err)}`);
        }

        setData({
          product: productData,
          company: companyData,
          productCapabilities: productCaps,
          capabilities: allCapabilities
        });
      } catch (err) {
        console.error('Failed to fetch product data:', err);
        setError('Couldn\'t load product data. Try again.');
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [companyId, productId]);

  const getCapabilityName = (capabilityId: string): string => {
    const capability = data?.capabilities.find(c => c.id === capabilityId);
    return capability?.name || 'Unknown Capability';
  };

  const handleSourceClick = (sourceId?: string) => {
    // TODO: Implement Source Drawer
    console.log('Source clicked:', sourceId);
  };

  if (loading) {
    return (
      <div className="container">
        {/* Hero Skeleton */}
        <div className="mb-8">
          <div className="h-8 bg-gray-200 rounded w-1/3 mb-4 animate-pulse"></div>
          <div className="h-4 bg-gray-200 rounded w-2/3 mb-2 animate-pulse"></div>
          <div className="h-4 bg-gray-200 rounded w-1/2 mb-4 animate-pulse"></div>
          <div className="flex gap-2">
            <div className="h-8 bg-gray-200 rounded w-24 animate-pulse"></div>
            <div className="h-8 bg-gray-200 rounded w-32 animate-pulse"></div>
          </div>
        </div>

        {/* Capabilities Skeleton */}
        <div>
          <div className="h-6 bg-gray-200 rounded w-1/4 mb-4 animate-pulse"></div>
          <div className="space-y-3">
            {[1, 2, 3, 4].map((i) => (
              <div key={i} className="flex items-center space-x-3 p-4 bg-white rounded-lg border border-gray-200">
                <div className="h-4 bg-gray-200 rounded w-1/3 animate-pulse"></div>
                <div className="h-6 bg-gray-200 rounded-full w-20 animate-pulse"></div>
                <div className="h-4 bg-gray-200 rounded w-1/2 animate-pulse"></div>
                <div className="h-4 bg-gray-200 rounded w-4 animate-pulse"></div>
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
          to={`/companies/${companyId}`} 
          className="text-blue-600 hover:text-blue-800 underline"
        >
          ← Back to Company
        </Link>
      </div>
    );
  }

  if (notFound) {
    return (
      <div className="container">
        <div className="text-center py-12">
          <h1 className="text-2xl font-bold text-gray-900 mb-4">Product not found for this company</h1>
          <p className="text-gray-600 mb-6">The product you're looking for doesn't exist for this company.</p>
          <Link 
            to={`/companies/${companyId}`} 
            className="inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            ← Back to Company
          </Link>
        </div>
      </div>
    );
  }

  if (!data) {
    return (
      <div className="container">
        <div className="text-center py-12">
          <h1 className="text-2xl font-bold text-gray-900 mb-4">Product not found</h1>
          <p className="text-gray-600 mb-6">The product you're looking for doesn't exist.</p>
          <Link 
            to={`/companies/${companyId}`} 
            className="inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            ← Back to Company
          </Link>
        </div>
      </div>
    );
  }

  const { product: productData, company: companyData, productCapabilities } = data;

  return (
    <div className="container">
      {/* Hero Section */}
      <div className="mb-8">
        <div className="flex flex-col lg:flex-row lg:items-start lg:justify-between gap-4">
          <div className="flex-1">
            <h1 className="text-3xl font-bold text-gray-900 mb-2">
              {productData.name}
            </h1>
            
            {productData.short_desc && (
              <p className="text-lg text-gray-700 mb-4">
                {productData.short_desc}
              </p>
            )}

            {/* Company Chip */}
            <div className="mb-4">
              <Link
                to={`/companies/${companyId}`}
                className="inline-flex items-center px-3 py-1 bg-blue-100 text-blue-800 text-sm rounded-full hover:bg-blue-200 transition-colors"
              >
                {companyData.name}
              </Link>
            </div>

            {/* Category, Markets, Tags */}
            <div className="flex flex-wrap gap-2 mb-4">
              <span className="inline-block px-2 py-1 bg-blue-100 text-blue-800 text-sm rounded-full">
                {productData.category}
              </span>
              {productData.markets.map((market) => (
                <span
                  key={market}
                  className="inline-block px-2 py-1 bg-gray-100 text-gray-600 text-sm rounded-full"
                >
                  {market}
                </span>
              ))}
              {productData.tags.map((tag) => (
                <span
                  key={tag}
                  className="inline-block px-2 py-1 bg-gray-50 text-gray-500 text-sm rounded"
                >
                  {tag}
                </span>
              ))}
            </div>
          </div>

          {/* Action Buttons */}
          <div className="flex flex-col sm:flex-row gap-2">
            {productData.product_url && (
              <a
                href={productData.product_url}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
              >
                Product Page
                <span className="ml-1">↗</span>
              </a>
            )}
            {productData.docs_url && (
              <a
                href={productData.docs_url}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 transition-colors"
              >
                Documentation
                <span className="ml-1">↗</span>
              </a>
            )}
          </div>
        </div>
      </div>

      {/* Capabilities Section */}
      <div>
        <h2 className="text-2xl font-bold text-gray-900 mb-6">Capabilities</h2>
        
        {productCapabilities.length === 0 ? (
          <div className="bg-gray-50 rounded-lg p-8 text-center">
            <p className="text-gray-500 text-lg">No capabilities documented yet.</p>
          </div>
        ) : (
          <div className="space-y-3">
            {productCapabilities.map((productCap) => (
              <div
                key={productCap.id}
                className="flex items-center space-x-4 p-4 bg-white rounded-lg border border-gray-200 hover:shadow-sm transition-all duration-200"
              >
                {/* Capability Name */}
                <div className="flex-1 min-w-0">
                  <h3 className="text-sm font-medium text-gray-900">
                    {getCapabilityName(productCap.capability_id)}
                  </h3>
                </div>

                {/* Maturity Pill */}
                <span className={`inline-block px-2 py-1 text-xs rounded-full ${maturityColors[productCap.maturity as ExtendedMaturity] || 'bg-gray-100 text-gray-800'}`}>
                  {maturityLabels[productCap.maturity as ExtendedMaturity] || productCap.maturity}
                </span>

                {/* Details */}
                {productCap.details && (
                  <p className="text-sm text-gray-600 flex-1 min-w-0">
                    {productCap.details}
                  </p>
                )}

                {/* Source Icon */}
                {productCap.source_id && (
                  <button
                    onClick={() => handleSourceClick(productCap.source_id)}
                    className="p-1 text-gray-400 hover:text-gray-600 transition-colors"
                    title="View source"
                  >
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                    </svg>
                  </button>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
