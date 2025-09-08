import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { getThisWeekSignals, getRecentReleases, source, getYourCompany, getYourCompanyStats } from '../lib/mockData';
import type { Signal, Release, Source as SourceType, Company } from '@schema/types';
import SourceDrawer from '../components/SourceDrawer';
import { useDateFormat } from '../hooks/useDateFormat';

// Get impact color class
function getImpactColor(impact: string): string {
  const impactNum = parseInt(impact);
  if (impactNum >= 2) return 'text-green-600 bg-green-50';
  if (impactNum === 1) return 'text-blue-600 bg-blue-50';
  if (impactNum === 0) return 'text-gray-600 bg-gray-50';
  if (impactNum === -1) return 'text-orange-600 bg-orange-50';
  return 'text-red-600 bg-red-50';
}

// Get impact label
function getImpactLabel(impact: string): string {
  const impactNum = parseInt(impact);
  if (impactNum >= 2) return 'High';
  if (impactNum === 1) return 'Medium';
  if (impactNum === 0) return 'Neutral';
  if (impactNum === -1) return 'Low';
  return 'Very Low';
}

export default function Overview() {
  console.log('Overview: Component rendering...');
  const [signals, setSignals] = useState<Signal[]>([]);
  const [releases, setReleases] = useState<Release[]>([]);
  const [yourCompany, setYourCompany] = useState<Company | null>(null);
  const [yourCompanyStats, setYourCompanyStats] = useState<{ products: number; capabilities: number; recentSignals: number } | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [sourceDrawer, setSourceDrawer] = useState<{ isOpen: boolean; source?: SourceType; signalUrl?: string }>({
    isOpen: false
  });
  const { formatDate } = useDateFormat();

  useEffect(() => {
    async function loadData() {
      try {
        console.log('Overview: Starting data load...');
        setLoading(true);
        const [signalsData, releasesData, yourCompanyData, yourCompanyStatsData] = await Promise.all([
          getThisWeekSignals(),
          getRecentReleases(),
          getYourCompany(),
          getYourCompanyStats()
        ]);
        console.log('Overview: Data loaded successfully', { 
          signals: signalsData.length, 
          releases: releasesData.length,
          yourCompany: yourCompanyData?.name,
          yourCompanyStats: yourCompanyStatsData
        });
        setSignals(signalsData);
        setReleases(releasesData);
        setYourCompany(yourCompanyData);
        setYourCompanyStats(yourCompanyStatsData);
      } catch (err) {
        console.error('Overview: Error loading data', err);
        setError(err instanceof Error ? err.message : 'Failed to load data');
      } finally {
        setLoading(false);
      }
    }

    loadData();
  }, []);

  const handleSourceClick = async (sourceId: string, signalUrl: string) => {
    try {
      const sourceData = await source(sourceId);
      setSourceDrawer({
        isOpen: true,
        source: sourceData,
        signalUrl: signalUrl
      });
    } catch (error) {
      console.error('Failed to fetch source:', error);
    }
  };

  if (loading) {
    return (
      <div className="container">
        <div className="space-y-8">
          {/* Loading skeleton for signals */}
          <div>
            <div className="h-6 bg-gray-200 rounded w-48 mb-4 animate-pulse"></div>
            <div className="space-y-3">
              {[...Array(3)].map((_, i) => (
                <div key={i} className="h-16 bg-gray-100 rounded-lg animate-pulse"></div>
              ))}
            </div>
          </div>
          {/* Loading skeleton for releases */}
          <div>
            <div className="h-6 bg-gray-200 rounded w-48 mb-4 animate-pulse"></div>
            <div className="space-y-3">
              {[...Array(4)].map((_, i) => (
                <div key={i} className="h-12 bg-gray-100 rounded-lg animate-pulse"></div>
              ))}
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="container">
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <p className="text-red-800">Error loading data: {error}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="container">
      {/* Your Company Section */}
      {yourCompany && yourCompanyStats && (
        <div className="mb-8">
          <div className="bg-white rounded-lg border border-gray-200 p-6">
            <div className="flex items-start justify-between">
              <div className="flex items-start space-x-4">
                {/* Company Logo */}
                <div className="flex-shrink-0">
                  {yourCompany.logoUrl ? (
                    <img
                      src={yourCompany.logoUrl}
                      alt={`${yourCompany.name} logo`}
                      className="w-16 h-16 rounded-full object-cover border-2 border-gray-200 shadow-sm"
                    />
                  ) : (
                    <div className="w-16 h-16 rounded-full bg-gray-600 flex items-center justify-center text-white font-bold text-xl">
                      {yourCompany.name.charAt(0)}
                    </div>
                  )}
                </div>
                
                {/* Company Info */}
                <div className="flex-1 min-w-0">
                  <div className="flex items-center space-x-2 mb-2">
                    <h3 className="text-xl font-semibold text-gray-900">{yourCompany.name}</h3>
                    <span className="px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded-full font-medium">
                      Your Company
                    </span>
                  </div>
                  
                  <p className="text-gray-700 mb-4">
                    Leading provider of AI-powered robotics solutions for industrial automation.
                  </p>
                  
                  {/* Stats */}
                  <div className="flex space-x-6 text-sm">
                    <div className="flex items-center space-x-1">
                      <span className="font-medium text-gray-900">{yourCompanyStats.products}</span>
                      <span className="text-gray-600">products</span>
                    </div>
                    <div className="flex items-center space-x-1">
                      <span className="font-medium text-gray-900">{yourCompanyStats.capabilities}</span>
                      <span className="text-gray-600">capabilities</span>
                    </div>
                    <div className="flex items-center space-x-1">
                      <span className="font-medium text-gray-900">{yourCompanyStats.recentSignals}</span>
                      <span className="text-gray-600">recent signals (60d)</span>
                    </div>
                  </div>
                </div>
              </div>
              
              {/* View Profile Button */}
              <Link
                to={`/companies/${yourCompany.id}`}
                className="inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
              >
                View profile
                <svg className="w-4 h-4 ml-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                </svg>
              </Link>
            </div>
          </div>
        </div>
      )}

      <div className="grid gap-8 lg:grid-cols-2">
        {/* This Week Signals */}
        <div>
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-semibold text-gray-900">This Week Signals</h2>
            <span className="text-sm text-gray-500">{signals.length} signals</span>
          </div>
          
          {signals.length === 0 ? (
            <div className="bg-gray-50 rounded-lg p-6 text-center">
              <p className="text-gray-500">No signals from the past week</p>
            </div>
          ) : (
            <div className="space-y-3">
              {signals.map((signal) => (
                <div
                  key={signal.id}
                  onClick={() => {
                    if (signal.source_id) {
                      handleSourceClick(signal.source_id, signal.url);
                    }
                  }}
                  className={`p-4 bg-white border border-gray-200 rounded-lg hover:border-blue-300 hover:shadow-sm transition-all duration-200 ${
                    signal.source_id ? 'cursor-pointer' : 'cursor-default'
                  }`}
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1 min-w-0">
                      <h3 className="text-sm font-medium text-gray-900 line-clamp-2 mb-1">
                        {signal.headline}
                      </h3>
                      <p className="text-xs text-gray-500">{formatDate(signal.published_at)}</p>
                    </div>
                    <div className={`ml-3 px-2 py-1 rounded-full text-xs font-medium ${getImpactColor(signal.impact)}`}>
                      {getImpactLabel(signal.impact)}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Recent Releases */}
        <div>
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-semibold text-gray-900">Recent Releases</h2>
            <span className="text-sm text-gray-500">{releases.length} releases</span>
          </div>
          
          {releases.length === 0 ? (
            <div className="bg-gray-50 rounded-lg p-6 text-center">
              <p className="text-gray-500">No releases from the past 90 days</p>
            </div>
          ) : (
            <div className="space-y-3">
              {releases.map((release) => (
                <Link
                  key={release.id}
                  to={`/companies/${release.company_id}/products/${release.product_id}`}
                  className="block p-4 bg-white border border-gray-200 rounded-lg hover:border-blue-300 hover:shadow-sm transition-all duration-200"
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1 min-w-0">
                      <h3 className="text-sm font-medium text-gray-900 mb-1">
                        {release.version ? `${release.version} - ` : ''}Product Release
                      </h3>
                      <p className="text-xs text-gray-500">{formatDate(release.released_at)}</p>
                      {release.notes && (
                        <p className="text-xs text-gray-600 mt-1 line-clamp-2">{release.notes}</p>
                      )}
                    </div>
                    <div className="ml-3 text-blue-600">
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                      </svg>
                    </div>
                  </div>
                </Link>
              ))}
            </div>
          )}
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
