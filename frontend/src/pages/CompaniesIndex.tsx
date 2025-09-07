import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { companies } from '../lib/mockData';
import { Company, CompanySummary } from '@schema/types';

interface CompanyWithSummary extends Company {
  summary?: CompanySummary;
}

export default function CompaniesIndex() {
  const [companiesData, setCompaniesData] = useState<CompanyWithSummary[]>([]);
  const [filteredCompanies, setFilteredCompanies] = useState<CompanyWithSummary[]>([]);
  const [searchTerm, setSearchTerm] = useState('');
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
        setFilteredCompanies(companiesList);
      } catch (error) {
        console.error('Failed to fetch companies:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchCompanies();
  }, []);

  useEffect(() => {
    if (!searchTerm.trim()) {
      setFilteredCompanies(companiesData);
      return;
    }

    const filtered = companiesData.filter(company => {
      const searchLower = searchTerm.toLowerCase();
      return (
        company.name.toLowerCase().includes(searchLower) ||
        company.aliases.some(alias => alias.toLowerCase().includes(searchLower))
      );
    });

    setFilteredCompanies(filtered);
  }, [searchTerm, companiesData]);

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

  if (loading) {
    return (
      <div className="container">
        <div className="flex items-center justify-center min-h-64">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
          <span className="ml-2 text-gray-600">Loading companies...</span>
        </div>
      </div>
    );
  }

  return (
    <div className="container">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Companies</h1>
        <p className="text-gray-600 mb-6">Browse and manage tracked companies</p>
        
        {/* Search Input */}
        <div className="max-w-md">
          <input
            type="text"
            placeholder="Search companies by name or alias..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
        </div>
      </div>

      {/* Companies Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {filteredCompanies.map((company) => (
          <div
            key={company.id}
            onClick={() => handleCompanyClick(company.id)}
            className="bg-white rounded-lg border border-gray-200 p-6 hover:shadow-md hover:border-blue-300 cursor-pointer transition-all duration-200"
          >
            <div className="mb-4">
              <h3 className="text-xl font-semibold text-gray-900 mb-2">
                {company.name}
              </h3>
              
              {company.website && (
                <p className="text-sm text-blue-600 mb-2">
                  {getWebsiteDomain(company.website)}
                </p>
              )}
              
              {company.hq_country && (
                <p className="text-sm text-gray-600 mb-2">
                  HQ: {company.hq_country}
                </p>
              )}
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
      </div>

      {filteredCompanies.length === 0 && !loading && (
        <div className="text-center py-12">
          <p className="text-gray-500 text-lg">
            {searchTerm ? 'No companies found matching your search.' : 'No companies available.'}
          </p>
        </div>
      )}
    </div>
  );
}
