import React, { useState, useEffect, useRef, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { globalSearch, SearchResult } from '../lib/mockData';
import LoadingSpinner from './LoadingSpinner';

interface GlobalSearchModalProps {
  isOpen: boolean;
  onClose: () => void;
}

interface SearchResults {
  companies: SearchResult[];
  products: SearchResult[];
  signals: SearchResult[];
  releases: SearchResult[];
}

export default function GlobalSearchModal({ isOpen, onClose }: GlobalSearchModalProps) {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<SearchResults>({
    companies: [],
    products: [],
    signals: [],
    releases: []
  });
  const [isLoading, setIsLoading] = useState(false);
  const [selectedIndex, setSelectedIndex] = useState(0);
  const [recentSearches, setRecentSearches] = useState<string[]>([]);
  
  const inputRef = useRef<HTMLInputElement>(null);
  const navigate = useNavigate();
  
  // Load recent searches from localStorage
  useEffect(() => {
    const saved = localStorage.getItem('auralis-recent-searches');
    if (saved) {
      try {
        setRecentSearches(JSON.parse(saved));
      } catch {
        // Ignore invalid JSON
      }
    }
  }, []);
  
  // Focus input when modal opens
  useEffect(() => {
    if (isOpen && inputRef.current) {
      inputRef.current.focus();
    }
  }, [isOpen]);
  
  // Debounced search
  useEffect(() => {
    if (!query.trim()) {
      setResults({ companies: [], products: [], signals: [], releases: [] });
      setIsLoading(false);
      return;
    }
    
    setIsLoading(true);
    const timeoutId = setTimeout(async () => {
      try {
        const searchResults = await globalSearch(query);
        setResults(searchResults);
        setSelectedIndex(0);
      } catch (error) {
        console.error('Search error:', error);
        setResults({ companies: [], products: [], signals: [], releases: [] });
      } finally {
        setIsLoading(false);
      }
    }, 250);
    
    return () => clearTimeout(timeoutId);
  }, [query]);
  
  // Handle keyboard navigation
  const handleKeyDown = useCallback((e: React.KeyboardEvent) => {
    const allResults = [
      ...results.companies,
      ...results.products,
      ...results.signals,
      ...results.releases
    ];
    
    switch (e.key) {
      case 'ArrowDown':
        e.preventDefault();
        setSelectedIndex(prev => Math.min(prev + 1, allResults.length - 1));
        break;
      case 'ArrowUp':
        e.preventDefault();
        setSelectedIndex(prev => Math.max(prev - 1, 0));
        break;
      case 'Enter':
        e.preventDefault();
        if (allResults.length > 0 && selectedIndex >= 0 && selectedIndex < allResults.length) {
          handleResultClick(allResults[selectedIndex]);
        } else if (query.trim()) {
          // Navigate to search results page
          navigate(`/search?q=${encodeURIComponent(query)}`);
          onClose();
        }
        break;
      case 'Escape':
        e.preventDefault();
        onClose();
        break;
    }
  }, [results, selectedIndex, query, navigate, onClose]);
  
  // Handle result click
  const handleResultClick = useCallback((result: SearchResult) => {
    // Save to recent searches
    if (query.trim() && !recentSearches.includes(query.trim())) {
      const newRecent = [query.trim(), ...recentSearches].slice(0, 5);
      setRecentSearches(newRecent);
      localStorage.setItem('auralis-recent-searches', JSON.stringify(newRecent));
    }
    
    // Navigate based on result type
    switch (result.type) {
      case 'company':
        navigate(`/companies/${result.companyId}`);
        break;
      case 'product':
        navigate(`/companies/${result.companyId}/products/${result.productId}`);
        break;
      case 'signal':
        navigate(`/signals?highlight=${result.signalId}`);
        break;
      case 'release':
        navigate(`/companies/${result.companyId}/products/${result.productId}`);
        break;
    }
    
    onClose();
  }, [query, recentSearches, navigate, onClose]);
  
  // Handle recent search click
  const handleRecentSearchClick = useCallback((recentQuery: string) => {
    setQuery(recentQuery);
  }, []);
  
  // Get all results for keyboard navigation
  const allResults = [
    ...results.companies,
    ...results.products,
    ...results.signals,
    ...results.releases
  ];
  
  // Format date for display
  const formatDate = (dateString: string) => {
    try {
      return new Date(dateString).toLocaleDateString('en-US', {
        month: 'short',
        day: 'numeric',
        year: 'numeric'
      });
    } catch {
      return dateString;
    }
  };
  
  // Highlight matching text
  const highlightText = (text: string, query: string) => {
    if (!query.trim()) return text;
    
    const regex = new RegExp(`(${query.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')})`, 'gi');
    const parts = text.split(regex);
    
    return parts.map((part, index) => 
      regex.test(part) ? (
        <strong key={index} className="font-semibold">{part}</strong>
      ) : part
    );
  };
  
  if (!isOpen) return null;
  
  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      {/* Backdrop */}
      <div 
        className="fixed inset-0 bg-black bg-opacity-50 transition-opacity"
        onClick={onClose}
      />
      
      {/* Modal */}
      <div className="flex min-h-full items-start justify-center p-4 pt-16">
        <div className="relative w-full max-w-2xl bg-white rounded-lg shadow-xl">
          {/* Search Input */}
          <div className="p-4 border-b border-gray-200">
            <div className="relative">
              <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                <svg className="h-5 w-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                </svg>
              </div>
              <input
                ref={inputRef}
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Search companies, products, signals, releases..."
                className="block w-full pl-10 pr-3 py-3 border border-gray-300 rounded-md leading-5 bg-white placeholder-gray-500 focus:outline-none focus:placeholder-gray-400 focus:ring-1 focus:ring-blue-500 focus:border-blue-500 text-lg"
              />
              {isLoading && (
                <div className="absolute inset-y-0 right-0 pr-3 flex items-center">
                  <LoadingSpinner size="sm" />
                </div>
              )}
            </div>
          </div>
          
          {/* Results */}
          <div className="max-h-96 overflow-y-auto">
            {!query.trim() && recentSearches.length > 0 && (
              <div className="p-4 border-b border-gray-100">
                <h3 className="text-sm font-medium text-gray-500 mb-2">Recent searches</h3>
                <div className="space-y-1">
                  {recentSearches.map((recentQuery, index) => (
                    <button
                      key={index}
                      onClick={() => handleRecentSearchClick(recentQuery)}
                      className="block w-full text-left px-3 py-2 text-sm text-gray-700 hover:bg-gray-100 rounded-md"
                    >
                      {recentQuery}
                    </button>
                  ))}
                </div>
              </div>
            )}
            
            {query.trim() && !isLoading && allResults.length === 0 && (
              <div className="p-8 text-center">
                <div className="text-gray-500 mb-2">No results for "{query}"</div>
                <div className="text-sm text-gray-400">
                  Try searching with operators: <code className="bg-gray-100 px-1 rounded">company:</code>, <code className="bg-gray-100 px-1 rounded">product:</code>, <code className="bg-gray-100 px-1 rounded">signal:</code>, <code className="bg-gray-100 px-1 rounded">release:</code>
                </div>
              </div>
            )}
            
            {query.trim() && allResults.length > 0 && (
              <div className="p-4">
                {/* Companies */}
                {results.companies.length > 0 && (
                  <div className="mb-6">
                    <div className="flex items-center justify-between mb-2">
                      <h3 className="text-sm font-medium text-gray-900">Companies</h3>
                      <span className="text-xs text-gray-500">{results.companies.length} result{results.companies.length !== 1 ? 's' : ''}</span>
                    </div>
                    <div className="space-y-1">
                      {results.companies.map((result, index) => {
                        const globalIndex = index;
                        return (
                          <button
                            key={result.id}
                            onClick={() => handleResultClick(result)}
                            className={`w-full text-left p-3 rounded-md transition-colors ${
                              globalIndex === selectedIndex
                                ? 'bg-blue-50 border border-blue-200'
                                : 'hover:bg-gray-50'
                            }`}
                          >
                            <div className="flex items-start justify-between">
                              <div className="flex-1 min-w-0">
                                <div className="text-sm font-medium text-gray-900 truncate">
                                  {highlightText(result.title, query)}
                                </div>
                                {result.subtitle && (
                                  <div className="text-xs text-gray-500 truncate mt-1">
                                    {result.subtitle}
                                  </div>
                                )}
                                {result.description && (
                                  <div className="text-xs text-gray-600 mt-1 line-clamp-2">
                                    {result.description}
                                  </div>
                                )}
                              </div>
                              <div className="ml-2 flex-shrink-0">
                                <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                                  Company
                                </span>
                              </div>
                            </div>
                          </button>
                        );
                      })}
                    </div>
                  </div>
                )}
                
                {/* Products */}
                {results.products.length > 0 && (
                  <div className="mb-6">
                    <div className="flex items-center justify-between mb-2">
                      <h3 className="text-sm font-medium text-gray-900">Products</h3>
                      <span className="text-xs text-gray-500">{results.products.length} result{results.products.length !== 1 ? 's' : ''}</span>
                    </div>
                    <div className="space-y-1">
                      {results.products.map((result, index) => {
                        const globalIndex = results.companies.length + index;
                        return (
                          <button
                            key={result.id}
                            onClick={() => handleResultClick(result)}
                            className={`w-full text-left p-3 rounded-md transition-colors ${
                              globalIndex === selectedIndex
                                ? 'bg-blue-50 border border-blue-200'
                                : 'hover:bg-gray-50'
                            }`}
                          >
                            <div className="flex items-start justify-between">
                              <div className="flex-1 min-w-0">
                                <div className="text-sm font-medium text-gray-900 truncate">
                                  {highlightText(result.title, query)}
                                </div>
                                {result.subtitle && (
                                  <div className="text-xs text-gray-500 truncate mt-1">
                                    {result.subtitle}
                                  </div>
                                )}
                                {result.description && (
                                  <div className="text-xs text-gray-600 mt-1 line-clamp-2">
                                    {result.description}
                                  </div>
                                )}
                              </div>
                              <div className="ml-2 flex-shrink-0">
                                <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800">
                                  Product
                                </span>
                              </div>
                            </div>
                          </button>
                        );
                      })}
                    </div>
                  </div>
                )}
                
                {/* Signals */}
                {results.signals.length > 0 && (
                  <div className="mb-6">
                    <div className="flex items-center justify-between mb-2">
                      <h3 className="text-sm font-medium text-gray-900">Signals</h3>
                      <span className="text-xs text-gray-500">{results.signals.length} result{results.signals.length !== 1 ? 's' : ''}</span>
                    </div>
                    <div className="space-y-1">
                      {results.signals.map((result, index) => {
                        const globalIndex = results.companies.length + results.products.length + index;
                        return (
                          <button
                            key={result.id}
                            onClick={() => handleResultClick(result)}
                            className={`w-full text-left p-3 rounded-md transition-colors ${
                              globalIndex === selectedIndex
                                ? 'bg-blue-50 border border-blue-200'
                                : 'hover:bg-gray-50'
                            }`}
                          >
                            <div className="flex items-start justify-between">
                              <div className="flex-1 min-w-0">
                                <div className="text-sm font-medium text-gray-900 truncate">
                                  {highlightText(result.title, query)}
                                </div>
                                <div className="flex items-center gap-2 mt-1">
                                  {result.subtitle && (
                                    <div className="text-xs text-gray-500 truncate">
                                      {result.subtitle}
                                    </div>
                                  )}
                                  {result.date && (
                                    <div className="text-xs text-gray-400">
                                      {formatDate(result.date)}
                                    </div>
                                  )}
                                </div>
                                {result.description && (
                                  <div className="text-xs text-gray-600 mt-1 line-clamp-2">
                                    {result.description}
                                  </div>
                                )}
                              </div>
                              <div className="ml-2 flex-shrink-0">
                                <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800">
                                  Signal
                                </span>
                              </div>
                            </div>
                          </button>
                        );
                      })}
                    </div>
                  </div>
                )}
                
                {/* Releases */}
                {results.releases.length > 0 && (
                  <div className="mb-6">
                    <div className="flex items-center justify-between mb-2">
                      <h3 className="text-sm font-medium text-gray-900">Releases</h3>
                      <span className="text-xs text-gray-500">{results.releases.length} result{results.releases.length !== 1 ? 's' : ''}</span>
                    </div>
                    <div className="space-y-1">
                      {results.releases.map((result, index) => {
                        const globalIndex = results.companies.length + results.products.length + results.signals.length + index;
                        return (
                          <button
                            key={result.id}
                            onClick={() => handleResultClick(result)}
                            className={`w-full text-left p-3 rounded-md transition-colors ${
                              globalIndex === selectedIndex
                                ? 'bg-blue-50 border border-blue-200'
                                : 'hover:bg-gray-50'
                            }`}
                          >
                            <div className="flex items-start justify-between">
                              <div className="flex-1 min-w-0">
                                <div className="text-sm font-medium text-gray-900 truncate">
                                  {highlightText(result.title, query)}
                                </div>
                                <div className="flex items-center gap-2 mt-1">
                                  {result.subtitle && (
                                    <div className="text-xs text-gray-500 truncate">
                                      {result.subtitle}
                                    </div>
                                  )}
                                  {result.date && (
                                    <div className="text-xs text-gray-400">
                                      {formatDate(result.date)}
                                    </div>
                                  )}
                                </div>
                                {result.description && (
                                  <div className="text-xs text-gray-600 mt-1 line-clamp-2">
                                    {result.description}
                                  </div>
                                )}
                              </div>
                              <div className="ml-2 flex-shrink-0">
                                <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-purple-100 text-purple-800">
                                  Release
                                </span>
                              </div>
                            </div>
                          </button>
                        );
                      })}
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
          
          {/* Footer */}
          <div className="px-4 py-3 bg-gray-50 border-t border-gray-200 rounded-b-lg">
            <div className="flex items-center justify-between text-xs text-gray-500">
              <div className="flex items-center gap-4">
                <span>↑↓ Navigate</span>
                <span>↵ Select</span>
                <span>Esc Close</span>
              </div>
              <div>
                <kbd className="px-2 py-1 bg-white border border-gray-300 rounded text-xs">⌘K</kbd>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
