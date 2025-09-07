import { useState, useEffect, useCallback, useMemo } from 'react';
import { useSearchParams } from 'react-router-dom';
import { 
  signals, 
  companies as fetchCompanies, 
  productsByCompany,
  source 
} from '../lib/mockData';
import { Signal, Company, Product, Source as SourceType } from '@schema/types';
import { SignalType } from '@schema/enums';
import SourceDrawer from '../components/SourceDrawer';

interface Facets {
  types: SignalType[];
  companies: string[];
  products: string[];
  capabilities: string[];
  impactRange: [number, number];
  impactLevels: number[];
  since: string;
  page: number;
}

const DEFAULT_FACETS: Facets = {
  types: [],
  companies: [],
  products: [],
  capabilities: [],
  impactRange: [-2, 2],
  impactLevels: [],
  since: '',
  page: 1
};

const SIGNAL_TYPES: SignalType[] = ['news', 'job', 'paper', 'funding', 'release', 'social'];

const IMPACT_LABELS = {
  '-2': 'Very Low',
  '-1': 'Low',
  '0': 'Neutral',
  '1': 'Medium',
  '2': 'High'
};

const IMPACT_COLORS = {
  '-2': 'bg-red-100 text-red-800',
  '-1': 'bg-orange-100 text-orange-800',
  '0': 'bg-gray-100 text-gray-800',
  '1': 'bg-blue-100 text-blue-800',
  '2': 'bg-green-100 text-green-800'
};

// Debounce utility
function useDebounce<T>(value: T, delay: number): T {
  const [debouncedValue, setDebouncedValue] = useState<T>(value);

  useEffect(() => {
    const handler = setTimeout(() => {
      setDebouncedValue(value);
    }, delay);

    return () => {
      clearTimeout(handler);
    };
  }, [value, delay]);

  return debouncedValue;
}

// Build query string from facets
function buildQueryFromFacets(facets: Facets): string {
  const params = new URLSearchParams();
  
  if (facets.types.length > 0) {
    params.set('type', facets.types.join(','));
  }
  
  if (facets.companies.length > 0) {
    params.set('company_id', facets.companies.join(','));
  }
  
  if (facets.products.length > 0) {
    params.set('product_id', facets.products.join(','));
  }
  
  if (facets.capabilities.length > 0) {
    params.set('capability_id', facets.capabilities.join(','));
  }
  
  if (facets.impactRange[0] !== -2 || facets.impactRange[1] !== 2) {
    params.set('impact_min', facets.impactRange[0].toString());
    params.set('impact_max', facets.impactRange[1].toString());
  }
  
  if (facets.impactLevels.length > 0) {
    params.set('impact_levels', facets.impactLevels.join(','));
  }
  
  if (facets.since) {
    params.set('since', facets.since);
  }
  
  if (facets.page > 1) {
    params.set('page', facets.page.toString());
  }
  
  return params.toString() ? `?${params.toString()}` : '';
}

// Parse facets from URL
function parseFacetsFromURL(searchParams: URLSearchParams): Facets {
  return {
    types: searchParams.get('type')?.split(',').filter(t => SIGNAL_TYPES.includes(t as SignalType)) as SignalType[] || [],
    companies: searchParams.get('company_id')?.split(',') || [],
    products: searchParams.get('product_id')?.split(',') || [],
    capabilities: searchParams.get('capability_id')?.split(',') || [],
    impactRange: [
      parseInt(searchParams.get('impact_min') || '-2'),
      parseInt(searchParams.get('impact_max') || '2')
    ] as [number, number],
    impactLevels: searchParams.get('impact_levels')?.split(',').map(Number) || [],
    since: searchParams.get('since') || '',
    page: parseInt(searchParams.get('page') || '1')
  };
}

// Date preset helpers
function getDatePreset(preset: string): string {
  const now = new Date();
  const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
  
  switch (preset) {
    case '7d':
      const weekAgo = new Date(today);
      weekAgo.setDate(today.getDate() - 6); // 7 days inclusive
      return weekAgo.toISOString().split('T')[0];
    case '30d':
      const monthAgo = new Date(today);
      monthAgo.setDate(today.getDate() - 29); // 30 days inclusive
      return monthAgo.toISOString().split('T')[0];
    case 'ytd':
      return new Date(now.getFullYear(), 0, 1).toISOString().split('T')[0];
    default:
      return '';
  }
}

export default function SignalsPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const [facets, setFacets] = useState<Facets>(() => parseFacetsFromURL(searchParams));
  const [signalsData, setSignalsData] = useState<Signal[]>([]);
  const [companiesData, setCompaniesData] = useState<Company[]>([]);
  const [availableProducts, setAvailableProducts] = useState<Product[]>([]);
  const [allProducts, setAllProducts] = useState<Product[]>([]);
  const [loading, setLoading] = useState(true);
  const [, setError] = useState<string | null>(null);
  const [sourceDrawer, setSourceDrawer] = useState<{ isOpen: boolean; source?: SourceType; signalUrl?: string }>({
    isOpen: false
  });
  const [onlyProductsWithResults, setOnlyProductsWithResults] = useState(false);

  // Debounce facets for URL updates
  const debouncedFacets = useDebounce(facets, 250);

  // Update URL when facets change
  useEffect(() => {
    const queryString = buildQueryFromFacets(debouncedFacets);
    setSearchParams(queryString, { replace: true });
  }, [debouncedFacets, setSearchParams]);

  // Load initial data
  useEffect(() => {
    const loadInitialData = async () => {
      try {
        setLoading(true);
        const companies = await fetchCompanies();
        setCompaniesData(companies);
        
        // Load all products for display names
        const allProductsData = await Promise.all(
          companies.map(c => productsByCompany(c.id))
        ).then(arrays => arrays.flat());
        setAllProducts(allProductsData);
      } catch (err) {
        console.error('Failed to load initial data:', err);
        setError('Failed to load data');
      } finally {
        setLoading(false);
      }
    };

    loadInitialData();
  }, []);

  // Load products when companies change
  useEffect(() => {
    const loadProducts = async () => {
      if (facets.companies.length === 0) {
        setAvailableProducts([]);
        return;
      }

      try {
        const productPromises = facets.companies.map(companyId => 
          productsByCompany(companyId)
        );
        const productArrays = await Promise.all(productPromises);
        const allProducts = productArrays.flat();
        setAvailableProducts(allProducts);
      } catch (err) {
        console.error('Failed to load products:', err);
      }
    };

    loadProducts();
  }, [facets.companies]);

  // Load and filter signals when facets change
  useEffect(() => {
    const loadAndFilterSignals = async () => {
      try {
        setLoading(true);
        const allSignals = await signals();
        
        // Apply filters
        let filteredSignals = allSignals;
        
        // Filter by type
        if (facets.types.length > 0) {
          filteredSignals = filteredSignals.filter(signal => 
            facets.types.includes(signal.type)
          );
        }
        
        // Filter by companies
        if (facets.companies.length > 0) {
          filteredSignals = filteredSignals.filter(signal => 
            signal.company_ids.some(companyId => facets.companies.includes(companyId))
          );
        }
        
        // Filter by products
        if (facets.products.length > 0) {
          filteredSignals = filteredSignals.filter(signal => 
            signal.product_ids.some(productId => facets.products.includes(productId))
          );
        }
        
        // Filter by capabilities
        if (facets.capabilities.length > 0) {
          filteredSignals = filteredSignals.filter(signal => 
            signal.capability_ids.some(capabilityId => facets.capabilities.includes(capabilityId))
          );
        }
        
        // Filter by impact levels
        if (facets.impactLevels.length > 0) {
          filteredSignals = filteredSignals.filter(signal => {
            const impact = parseInt(signal.impact);
            return facets.impactLevels.includes(impact);
          });
        } else {
          // Fallback to impact range if no specific levels selected
          filteredSignals = filteredSignals.filter(signal => {
            const impact = parseInt(signal.impact);
            return impact >= facets.impactRange[0] && impact <= facets.impactRange[1];
          });
        }
        
        // Filter by date
        if (facets.since) {
          const sinceDate = new Date(facets.since);
          filteredSignals = filteredSignals.filter(signal => {
            const signalDate = new Date(signal.published_at);
            return signalDate >= sinceDate;
          });
        }
        
        setSignalsData(filteredSignals);
      } catch (err) {
        console.error('Failed to load signals:', err);
        setError('Failed to load signals');
      } finally {
        setLoading(false);
      }
    };

    loadAndFilterSignals();
  }, [facets]);

  // Update facet
  const updateFacet = useCallback((key: keyof Facets, value: any) => {
    setFacets(prev => ({
      ...prev,
      [key]: value,
      page: 1 // Reset to first page when filters change
    }));
  }, []);

  // Handle date preset
  const handleDatePreset = useCallback((preset: string) => {
    const date = getDatePreset(preset);
    updateFacet('since', date);
  }, [updateFacet]);

  // Handle source drawer
  const handleSourceClick = useCallback(async (signal: Signal) => {
    if (signal.source_id) {
      try {
        const sourceData = await source(signal.source_id);
        setSourceDrawer({
          isOpen: true,
          source: sourceData,
          signalUrl: signal.url
        });
      } catch (err) {
        console.error('Failed to load source:', err);
        // Fallback to direct URL
        window.open(signal.url, '_blank');
      }
    } else {
      // No source_id, open URL directly
      window.open(signal.url, '_blank');
    }
  }, []);

  // Pagination
  const ITEMS_PER_PAGE = 25;
  const totalPages = Math.ceil(signalsData.length / ITEMS_PER_PAGE);
  const currentPageData = signalsData.slice(
    (facets.page - 1) * ITEMS_PER_PAGE,
    facets.page * ITEMS_PER_PAGE
  );

  // Clear all filters
  const clearFilters = useCallback(() => {
    setFacets(DEFAULT_FACETS);
  }, []);

  // Get filtered products (if toggle is on)
  const filteredProducts = useMemo(() => {
    if (!onlyProductsWithResults) return availableProducts;
    
    // Filter to products that have signals
    const productsWithSignals = new Set(
      signalsData.flatMap(signal => signal.product_ids)
    );
    
    return availableProducts.filter(product => 
      productsWithSignals.has(product.id)
    );
  }, [availableProducts, signalsData, onlyProductsWithResults]);

  return (
    <div className="container mx-auto px-4">
      <div className="flex flex-col lg:flex-row gap-6">
        {/* Left Facet Panel */}
        <div className="w-full lg:w-64 flex-shrink-0">
          <div className="bg-white rounded-lg border border-gray-200 p-4 sticky top-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Filters</h2>
            
            <div className="space-y-4">
              {/* Type Multiselect */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Type
                </label>
                <div className="space-y-2">
                  {SIGNAL_TYPES.map(type => (
                    <label key={type} className="flex items-center">
                      <input
                        type="checkbox"
                        checked={facets.types.includes(type)}
                        onChange={(e) => {
                          if (e.target.checked) {
                            updateFacet('types', [...facets.types, type]);
                          } else {
                            updateFacet('types', facets.types.filter(t => t !== type));
                          }
                        }}
                        className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                      />
                      <span className="ml-2 text-sm text-gray-700 capitalize">{type}</span>
                    </label>
                  ))}
                </div>
              </div>

              {/* Company Multiselect */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Company
                </label>
                <div className="space-y-2 max-h-40 overflow-y-auto">
                  {companiesData.map(company => (
                    <label key={company.id} className="flex items-center">
                      <input
                        type="checkbox"
                        checked={facets.companies.includes(company.id)}
                        onChange={(e) => {
                          if (e.target.checked) {
                            updateFacet('companies', [...facets.companies, company.id]);
                          } else {
                            updateFacet('companies', facets.companies.filter(c => c !== company.id));
                          }
                        }}
                        className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                      />
                      <span className="ml-2 text-sm text-gray-700">{company.name}</span>
                    </label>
                  ))}
                </div>
              </div>

              {/* Product Multiselect */}
              <div>
                <div className="flex items-center justify-between mb-2">
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Product
                  </label>
                  <label className="flex items-center text-xs text-gray-500">
                    <input
                      type="checkbox"
                      checked={onlyProductsWithResults}
                      onChange={(e) => setOnlyProductsWithResults(e.target.checked)}
                      className="rounded border-gray-300 text-blue-600 focus:ring-blue-500 mr-1"
                    />
                    Only with results
                  </label>
                </div>
                <div className="space-y-2 max-h-40 overflow-y-auto">
                  {filteredProducts.map(product => (
                    <label key={product.id} className="flex items-center">
                      <input
                        type="checkbox"
                        checked={facets.products.includes(product.id)}
                        onChange={(e) => {
                          if (e.target.checked) {
                            updateFacet('products', [...facets.products, product.id]);
                          } else {
                            updateFacet('products', facets.products.filter(p => p !== product.id));
                          }
                        }}
                        className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                      />
                      <span className="ml-2 text-sm text-gray-700">{product.name}</span>
                    </label>
                  ))}
                </div>
              </div>


              {/* Impact Selection */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Impact
                </label>
                <div className="flex gap-2 flex-wrap">
                  <button
                    onClick={() => updateFacet('impactLevels', [])}
                    className={`px-3 py-1 text-xs rounded ${
                      facets.impactLevels.length === 0
                        ? 'bg-blue-100 text-blue-800 border border-blue-300'
                        : 'bg-gray-100 hover:bg-gray-200'
                    }`}
                  >
                    All
                  </button>
                  <button
                    onClick={() => {
                      if (facets.impactLevels.includes(2)) {
                        updateFacet('impactLevels', facets.impactLevels.filter(level => level !== 2));
                      } else {
                        updateFacet('impactLevels', [...facets.impactLevels, 2]);
                      }
                    }}
                    className={`px-3 py-1 text-xs rounded ${
                      facets.impactLevels.includes(2)
                        ? 'bg-blue-100 text-blue-800 border border-blue-300'
                        : 'bg-gray-100 hover:bg-gray-200'
                    }`}
                  >
                    High
                  </button>
                  <button
                    onClick={() => {
                      if (facets.impactLevels.includes(1)) {
                        updateFacet('impactLevels', facets.impactLevels.filter(level => level !== 1));
                      } else {
                        updateFacet('impactLevels', [...facets.impactLevels, 1]);
                      }
                    }}
                    className={`px-3 py-1 text-xs rounded ${
                      facets.impactLevels.includes(1)
                        ? 'bg-blue-100 text-blue-800 border border-blue-300'
                        : 'bg-gray-100 hover:bg-gray-200'
                    }`}
                  >
                    Medium
                  </button>
                  <button
                    onClick={() => {
                      if (facets.impactLevels.includes(0)) {
                        updateFacet('impactLevels', facets.impactLevels.filter(level => level !== 0));
                      } else {
                        updateFacet('impactLevels', [...facets.impactLevels, 0]);
                      }
                    }}
                    className={`px-3 py-1 text-xs rounded ${
                      facets.impactLevels.includes(0)
                        ? 'bg-blue-100 text-blue-800 border border-blue-300'
                        : 'bg-gray-100 hover:bg-gray-200'
                    }`}
                  >
                    Neutral
                  </button>
                  <button
                    onClick={() => {
                      if (facets.impactLevels.includes(-1)) {
                        updateFacet('impactLevels', facets.impactLevels.filter(level => level !== -1));
                      } else {
                        updateFacet('impactLevels', [...facets.impactLevels, -1]);
                      }
                    }}
                    className={`px-3 py-1 text-xs rounded ${
                      facets.impactLevels.includes(-1)
                        ? 'bg-blue-100 text-blue-800 border border-blue-300'
                        : 'bg-gray-100 hover:bg-gray-200'
                    }`}
                  >
                    Low
                  </button>
                  <button
                    onClick={() => {
                      if (facets.impactLevels.includes(-2)) {
                        updateFacet('impactLevels', facets.impactLevels.filter(level => level !== -2));
                      } else {
                        updateFacet('impactLevels', [...facets.impactLevels, -2]);
                      }
                    }}
                    className={`px-3 py-1 text-xs rounded ${
                      facets.impactLevels.includes(-2)
                        ? 'bg-blue-100 text-blue-800 border border-blue-300'
                        : 'bg-gray-100 hover:bg-gray-200'
                    }`}
                  >
                    Very Low
                  </button>
                </div>
              </div>

              {/* Date Range */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Since: {facets.since ? new Date(facets.since).toLocaleDateString() : 'All time'}
                </label>
                <div className="space-y-2">
                  <div className="flex gap-2">
                    <button
                      onClick={() => handleDatePreset('7d')}
                      className={`px-3 py-1 text-xs rounded ${
                        facets.since === getDatePreset('7d') 
                          ? 'bg-blue-100 text-blue-800 border border-blue-300' 
                          : 'bg-gray-100 hover:bg-gray-200'
                      }`}
                    >
                      7d
                    </button>
                    <button
                      onClick={() => handleDatePreset('30d')}
                      className={`px-3 py-1 text-xs rounded ${
                        facets.since === getDatePreset('30d') 
                          ? 'bg-blue-100 text-blue-800 border border-blue-300' 
                          : 'bg-gray-100 hover:bg-gray-200'
                      }`}
                    >
                      30d
                    </button>
                    <button
                      onClick={() => handleDatePreset('ytd')}
                      className={`px-3 py-1 text-xs rounded ${
                        facets.since === getDatePreset('ytd') 
                          ? 'bg-blue-100 text-blue-800 border border-blue-300' 
                          : 'bg-gray-100 hover:bg-gray-200'
                      }`}
                    >
                      YTD
                    </button>
                    <button
                      onClick={() => updateFacet('since', '')}
                      className={`px-3 py-1 text-xs rounded ${
                        !facets.since 
                          ? 'bg-blue-100 text-blue-800 border border-blue-300' 
                          : 'bg-gray-100 hover:bg-gray-200'
                      }`}
                    >
                      All
                    </button>
                  </div>
                </div>
              </div>

              {/* Clear Filters */}
              <button
                onClick={clearFilters}
                className="w-full px-4 py-2 text-sm text-gray-600 hover:text-gray-800 border border-gray-300 rounded-md hover:bg-gray-50"
              >
                Clear all filters
              </button>
            </div>
          </div>
        </div>

        {/* Main Content */}
        <div className="flex-1 min-w-0">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between mb-6 gap-4">
            <h1 className="text-3xl font-bold text-gray-900">Signals</h1>
            <div className="text-sm text-gray-500">
              {signalsData.length} signals found
            </div>
          </div>

          {/* Signals Table */}
          <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
            {loading ? (
              <div className="p-8">
                <div className="space-y-4">
                  {[...Array(5)].map((_, i) => (
                    <div key={i} className="flex space-x-4">
                      <div className="h-4 bg-gray-200 rounded w-20 animate-pulse"></div>
                      <div className="h-4 bg-gray-200 rounded flex-1 animate-pulse"></div>
                      <div className="h-4 bg-gray-200 rounded w-16 animate-pulse"></div>
                    </div>
                  ))}
                </div>
              </div>
            ) : signalsData.length === 0 ? (
              <div className="p-8 text-center">
                <p className="text-gray-500 text-lg mb-4">No signals found</p>
                <button
                  onClick={clearFilters}
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
                >
                  Clear filters
                </button>
              </div>
            ) : (
              <>
                <div className="overflow-x-auto">
                  <table className="w-full min-w-[900px]">
                    <thead className="bg-gray-50">
                      <tr>
                        <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider w-20">
                          Date
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider w-80">
                          Headline
                        </th>
                        <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider w-20">
                          Impact
                        </th>
                        <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider w-20">
                          Type
                        </th>
                        <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider w-28">
                          Companies
                        </th>
                        <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider w-28">
                          Products
                        </th>
                      </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-200">
                      {currentPageData.map((signal) => (
                        <tr key={signal.id} className="hover:bg-gray-50">
                          <td className="px-3 py-4 whitespace-nowrap text-sm text-gray-900">
                            {new Date(signal.published_at).toLocaleDateString()}
                          </td>
                          <td className="px-6 py-4 text-sm">
                            <button
                              onClick={() => handleSourceClick(signal)}
                              className="text-blue-600 hover:text-blue-800 hover:underline text-left"
                            >
                              {signal.headline}
                            </button>
                          </td>
                          <td className="px-3 py-4 whitespace-nowrap">
                            <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${IMPACT_COLORS[signal.impact]}`}>
                              {IMPACT_LABELS[signal.impact]}
                            </span>
                          </td>
                          <td className="px-3 py-4 whitespace-nowrap">
                            <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-gray-100 text-gray-800 capitalize">
                              {signal.type}
                            </span>
                          </td>
                          <td className="px-3 py-4 text-sm">
                            <div className="flex flex-wrap gap-1">
                              {signal.company_ids.slice(0, 2).map(companyId => {
                                const company = companiesData.find(c => c.id === companyId);
                                return (
                                  <button
                                    key={companyId}
                                    onClick={() => updateFacet('companies', [companyId])}
                                    className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800 hover:bg-blue-200"
                                  >
                                    {company?.name || companyId}
                                  </button>
                                );
                              })}
                              {signal.company_ids.length > 2 && (
                                <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-gray-100 text-gray-600">
                                  +{signal.company_ids.length - 2}
                                </span>
                              )}
                            </div>
                          </td>
                          <td className="px-3 py-4 text-sm">
                            <div className="flex flex-wrap gap-1">
                              {signal.product_ids.slice(0, 2).map(productId => {
                                const product = allProducts.find(p => p.id === productId);
                                return (
                                  <button
                                    key={productId}
                                    onClick={() => updateFacet('products', [productId])}
                                    className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800 hover:bg-green-200"
                                  >
                                    {product?.name || productId}
                                  </button>
                                );
                              })}
                              {signal.product_ids.length > 2 && (
                                <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-gray-100 text-gray-600">
                                  +{signal.product_ids.length - 2}
                                </span>
                              )}
                            </div>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>

                {/* Pagination */}
                {totalPages > 1 && (
                  <div className="px-6 py-3 border-t border-gray-200 flex items-center justify-between">
                    <div className="text-sm text-gray-700">
                      Showing {((facets.page - 1) * ITEMS_PER_PAGE) + 1} to {Math.min(facets.page * ITEMS_PER_PAGE, signalsData.length)} of {signalsData.length} results
                    </div>
                    <div className="flex space-x-2">
                      <button
                        onClick={() => updateFacet('page', Math.max(1, facets.page - 1))}
                        disabled={facets.page === 1}
                        className="px-3 py-1 text-sm border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                      >
                        Previous
                      </button>
                      <span className="px-3 py-1 text-sm text-gray-700">
                        Page {facets.page} of {totalPages}
                      </span>
                      <button
                        onClick={() => updateFacet('page', Math.min(totalPages, facets.page + 1))}
                        disabled={facets.page === totalPages}
                        className="px-3 py-1 text-sm border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                      >
                        Next
                      </button>
                    </div>
                  </div>
                )}
              </>
            )}
          </div>
        </div>
      </div>

      {/* Source Drawer */}
      <SourceDrawer
        isOpen={sourceDrawer.isOpen}
        onClose={() => setSourceDrawer({ isOpen: false })}
        source={sourceDrawer.source}
        signalUrl={sourceDrawer.signalUrl}
      />
    </div>
  );
}
