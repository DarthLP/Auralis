import { useState, useEffect, useCallback } from 'react';
import { Link } from 'react-router-dom';
import { releases, companies as fetchCompanies, productsByCompany, source } from '../lib/mockData';
import { Release, Company, Product, Source as SourceType } from '@schema/types';
import SourceDrawer from '../components/SourceDrawer';
import LoadingSkeleton from '../components/LoadingSkeleton';
import EmptyState from '../components/EmptyState';
import { useDateFormat } from '../hooks/useDateFormat';

interface Facets {
  companies: string[];
  since: string;
  page: number;
}

const DEFAULT_FACETS: Facets = {
  companies: [],
  since: '',
  page: 1
};

const ITEMS_PER_PAGE = 25;

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

export default function ReleasesPage() {
  const [facets, setFacets] = useState<Facets>(DEFAULT_FACETS);
  const [companiesData, setCompaniesData] = useState<Company[]>([]);
  const [allProducts, setAllProducts] = useState<Product[]>([]);
  const [filteredReleases, setFilteredReleases] = useState<Release[]>([]);
  const [loading, setLoading] = useState(true);
  const { formatDate } = useDateFormat();
  const [, setError] = useState<string | null>(null);
  
  // Source drawer state
  const [sourceDrawer, setSourceDrawer] = useState<{ isOpen: boolean; source?: SourceType; signalUrl?: string }>({
    isOpen: false
  });

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


  // Load and filter releases when facets change
  useEffect(() => {
    const loadAndFilterReleases = async () => {
      try {
        setLoading(true);
        const allReleasesData = await releases();
        
        // Apply filters
        let filtered = allReleasesData;
        
        // Filter by companies
        if (facets.companies.length > 0) {
          filtered = filtered.filter(release => 
            facets.companies.includes(release.company_id)
          );
        }
        
        
        // Filter by date
        if (facets.since) {
          const sinceDate = new Date(facets.since);
          filtered = filtered.filter(release => {
            const releaseDate = new Date(release.released_at);
            return releaseDate >= sinceDate;
          });
        }
        
        // Sort chronologically (newest first)
        filtered.sort((a, b) => {
          return new Date(b.released_at).getTime() - new Date(a.released_at).getTime();
        });
        
        setFilteredReleases(filtered);
      } catch (err) {
        console.error('Failed to load releases:', err);
        setError('Failed to load releases');
      } finally {
        setLoading(false);
      }
    };

    loadAndFilterReleases();
  }, [facets]);

  // Update facet
  const updateFacet = useCallback((key: keyof Facets, value: any) => {
    setFacets(prev => ({
      ...prev,
      [key]: value,
      page: 1 // Reset to first page when filters change
    }));
  }, []);

  // Clear all filters
  const clearFilters = useCallback(() => {
    setFacets(DEFAULT_FACETS);
  }, []);

  // Handle date preset
  const handleDatePreset = useCallback((preset: string) => {
    const date = getDatePreset(preset);
    updateFacet('since', date);
  }, [updateFacet]);

  // Handle source click
  const handleSourceClick = async (release: Release) => {
    if (!release.source_id) return;
    
    try {
      const sourceData = await source(release.source_id);
      setSourceDrawer({
        isOpen: true,
        source: sourceData,
        signalUrl: sourceData.origin
      });
    } catch (error) {
      console.error('Error loading source:', error);
    }
  };

  // Computed values

  const totalPages = Math.ceil(filteredReleases.length / ITEMS_PER_PAGE);
  const currentPageData = filteredReleases.slice(
    (facets.page - 1) * ITEMS_PER_PAGE,
    facets.page * ITEMS_PER_PAGE
  );


  const getProductName = (productId: string) => {
    const product = allProducts.find(p => p.id === productId);
    return product?.name || 'Unknown Product';
  };

  const getCompanyName = (companyId: string) => {
    const company = companiesData.find(c => c.id === companyId);
    return company?.name || 'Unknown Company';
  };

  return (
    <div className="container mx-auto px-4">
      <div className="flex flex-col lg:flex-row gap-6">
        {/* Left Facet Panel */}
        <div className="w-full lg:w-64 flex-shrink-0">
          <div className="bg-white rounded-lg border border-gray-200 p-4 sticky top-20">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Filters</h2>
            
            <div className="space-y-4">
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


              {/* Date Range */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Since: {facets.since ? formatDate(facets.since) : 'All time'}
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
            <div className="text-sm text-gray-500">
              {filteredReleases.length} releases found
            </div>
          </div>

          {/* Releases Table */}
          <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
            {loading ? (
              <div className="p-8">
                <LoadingSkeleton type="table" count={5} />
              </div>
            ) : filteredReleases.length === 0 ? (
              <div className="p-8">
                <EmptyState
                  icon={
                    <svg className="w-12 h-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M7 4V2a1 1 0 011-1h8a1 1 0 011 1v2m-9 0h10m-10 0a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V6a2 2 0 00-2-2M9 10h6m-6 4h6" />
                    </svg>
                  }
                  title="No releases found"
                  description="Try adjusting your filters or date range to find more releases."
                  action={{
                    label: "Clear filters",
                    onClick: clearFilters,
                    variant: "primary"
                  }}
                />
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
                          Product & Version
                        </th>
                        <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider w-28">
                          Company
                        </th>
                        <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider w-32">
                          Notes
                        </th>
                        <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider w-16">
                          Source
                        </th>
                      </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-200">
                      {currentPageData.map((release) => (
                        <tr key={release.id} className="hover:bg-gray-50">
                          <td className="px-3 py-4 whitespace-nowrap text-sm text-gray-900">
                            {formatDate(release.released_at)}
                          </td>
                          <td className="px-6 py-4 text-sm">
                            <Link
                              to={`/companies/${release.company_id}/products/${release.product_id}`}
                              className="text-blue-600 hover:text-blue-800 hover:underline"
                            >
                              {getProductName(release.product_id)}
                            </Link>
                            {release.version && (
                              <span className="ml-2 text-gray-600">
                                — {release.version}
                              </span>
                            )}
                          </td>
                          <td className="px-3 py-4 whitespace-nowrap">
                            <button
                              onClick={() => updateFacet('companies', [release.company_id])}
                              className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800 hover:bg-blue-200"
                            >
                              {getCompanyName(release.company_id)}
                            </button>
                          </td>
                          <td className="px-3 py-4 text-sm text-gray-700">
                            {release.notes || '-'}
                          </td>
                          <td className="px-3 py-4 whitespace-nowrap">
                            {release.source_id && (
                              <button
                                onClick={() => handleSourceClick(release)}
                                className="p-1 text-gray-400 hover:text-gray-600 transition-colors"
                                title="View source"
                              >
                                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />
                                </svg>
                              </button>
                            )}
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
                      Showing {((facets.page - 1) * ITEMS_PER_PAGE) + 1} to {Math.min(facets.page * ITEMS_PER_PAGE, filteredReleases.length)} of {filteredReleases.length} results
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
