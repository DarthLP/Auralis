import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { companies } from '../lib/mockData';
import { Company, CompanySummary } from '@schema/types';
import LoadingSkeleton from '../components/LoadingSkeleton';
import EmptyState from '../components/EmptyState';

interface CompanyWithSummary extends Company {
  summary?: CompanySummary;
}

export default function CompaniesIndex() {
  const [companiesData, setCompaniesData] = useState<CompanyWithSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    const fetchCompanies = async () => {
      try {
        setLoading(true);
        const companiesList = await companies();
        
        // For now, we'll just use the companies data without summaries
        // In a real implementation, you'd fetch summaries separately
        setCompaniesData(companiesList);
      } catch (error) {
        console.error('Failed to fetch companies:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchCompanies();
  }, []);

  const handleCompanyClick = (companyId: string) => {
    navigate(`/companies/${companyId}`);
  };

  const getWebsiteDomain = (website?: string) => {
    if (!website) return null;
    try {
      const url = new URL(website);
      return url.hostname.replace('www.', '');
    } catch {
      return website;
    }
  };

  const getCompanyInitials = (name: string) => {
    return name
      .split(' ')
      .map(word => word.charAt(0))
      .join('')
      .toUpperCase()
      .slice(0, 2);
  };

  if (loading) {
    return (
      <div className="container">
        <LoadingSkeleton type="grid" count={6} />
      </div>
    );
  }

  return (
    <div className="container">
      {/* Companies Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {companiesData.map((company) => (
          <div
            key={company.id}
            onClick={() => handleCompanyClick(company.id)}
            className="bg-white rounded-lg border border-gray-200 p-6 hover:shadow-md hover:border-blue-300 cursor-pointer transition-all duration-200"
          >
            <div className="mb-4">
              <div className="flex items-start space-x-3 mb-3">
                {/* Company Logo */}
                <div className="flex-shrink-0">
                  {company.logoUrl ? (
                    <img
                      src={company.logoUrl}
                      alt={`${company.name} logo`}
                      className="w-12 h-12 rounded-full object-cover border border-gray-200"
                    />
                  ) : (
                    <div className="w-12 h-12 rounded-full bg-gray-200 flex items-center justify-center text-gray-600 font-semibold text-sm">
                      {getCompanyInitials(company.name)}
                    </div>
                  )}
                </div>
                
                {/* Company Name and Badge */}
                <div className="flex-1 min-w-0">
                  <div className="flex items-center space-x-2 mb-1">
                    <h3 className="text-xl font-semibold text-gray-900 truncate">
                      {company.name}
                    </h3>
                    {company.isSelf && (
                      <span className="px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded-full font-medium flex-shrink-0">
                        Your Company
                      </span>
                    )}
                  </div>
                  
                  {company.website && (
                    <p className="text-sm text-blue-600 mb-1">
                      {getWebsiteDomain(company.website)}
                    </p>
                  )}
                  
                  {company.hq_country && (
                    <p className="text-sm text-gray-600">
                      HQ: {company.hq_country}
                    </p>
                  )}
                </div>
              </div>
            </div>
            
            {company.summary?.one_liner && (
              <p className="text-sm text-gray-700 line-clamp-2">
                {company.summary.one_liner}
              </p>
            )}
            
            <div className="mt-4 flex flex-wrap gap-1">
              {company.tags.slice(0, 3).map((tag) => (
                <span
                  key={tag}
                  className="px-2 py-1 bg-gray-100 text-gray-600 text-xs rounded-full"
                >
                  {tag}
                </span>
              ))}
              {company.tags.length > 3 && (
                <span className="px-2 py-1 bg-gray-100 text-gray-600 text-xs rounded-full">
                  +{company.tags.length - 3} more
                </span>
              )}
            </div>
          </div>
        ))}

        {/* Add Competitor Card */}
        <div
          onClick={() => navigate('/competitors/new')}
          className="bg-white rounded-lg border-2 border-dashed border-gray-300 p-6 hover:border-blue-400 hover:bg-blue-50 cursor-pointer transition-all duration-200 flex flex-col items-center justify-center min-h-[200px] text-center"
        >
          <div className="mb-4">
            <svg className="w-12 h-12 text-gray-400 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
            </svg>
          </div>
          <h3 className="text-lg font-semibold text-gray-700 mb-2">
            Add Competitor
          </h3>
          <p className="text-sm text-gray-500">
            Click to add a new competitor by pasting their website URL
          </p>
        </div>
      </div>

      {companiesData.length === 0 && !loading && (
        <EmptyState
          icon={
            <svg className="w-12 h-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
            </svg>
          }
          title="No companies available"
          description="No companies have been added to the system yet."
          action={{
            label: 'Add Your First Competitor',
            onClick: () => navigate('/competitors/new'),
            variant: 'primary' as const
          }}
        />
      )}
    </div>
  );
}
