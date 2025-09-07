import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { getThisWeekSignals, getRecentReleases } from '@/lib/mockData';
import type { Signal, Release } from '@schema/types';

// Format date to "MMM d, yyyy" format
function formatDate(dateString: string): string {
  const date = new Date(dateString);
  return date.toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric'
  });
}

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
  const [signals, setSignals] = useState<Signal[]>([]);
  const [releases, setReleases] = useState<Release[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadData() {
      try {
        setLoading(true);
        const [signalsData, releasesData] = await Promise.all([
          getThisWeekSignals(),
          getRecentReleases()
        ]);
        setSignals(signalsData);
        setReleases(releasesData);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load data');
      } finally {
        setLoading(false);
      }
    }

    loadData();
  }, []);

  if (loading) {
    return (
      <div className="container">
        <h1 className="text-3xl font-bold text-gray-900 mb-8">Overview</h1>
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
        <h1 className="text-3xl font-bold text-gray-900 mb-8">Overview</h1>
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <p className="text-red-800">Error loading data: {error}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="container">
      <h1 className="text-3xl font-bold text-gray-900 mb-8">Overview</h1>
      
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
                <Link
                  key={signal.id}
                  to={`/signals?highlight=${signal.id}`}
                  className="block p-4 bg-white border border-gray-200 rounded-lg hover:border-blue-300 hover:shadow-sm transition-all duration-200"
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
                </Link>
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
    </div>
  );
}
