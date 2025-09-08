import { useEffect, useRef } from 'react';
import { Source } from '@schema/types';

interface SourceDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  source?: Source;
  signalUrl?: string;
}

export default function SourceDrawer({ isOpen, onClose, source, signalUrl }: SourceDrawerProps) {
  const drawerRef = useRef<HTMLDivElement>(null);

  // Focus trap and escape key handling
  useEffect(() => {
    if (!isOpen) return;

    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        onClose();
      }
    };

    const handleFocus = (e: FocusEvent) => {
      if (drawerRef.current && !drawerRef.current.contains(e.target as Node)) {
        drawerRef.current.focus();
      }
    };

    document.addEventListener('keydown', handleEscape);
    document.addEventListener('focusin', handleFocus);
    
    // Focus the drawer when it opens
    if (drawerRef.current) {
      drawerRef.current.focus();
    }

    return () => {
      document.removeEventListener('keydown', handleEscape);
      document.removeEventListener('focusin', handleFocus);
    };
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  const getCredibilityColor = (credibility?: string) => {
    switch (credibility) {
      case 'high': return 'bg-green-100 text-green-800';
      case 'medium': return 'bg-yellow-100 text-yellow-800';
      case 'low': return 'bg-red-100 text-red-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const getCredibilityLabel = (credibility?: string) => {
    switch (credibility) {
      case 'high': return 'High';
      case 'medium': return 'Medium';
      case 'low': return 'Low';
      default: return 'Unknown';
    }
  };

  const formatDate = (dateString?: string) => {
    if (!dateString) return 'Unknown';
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const getDomain = (url: string) => {
    try {
      return new URL(url).hostname;
    } catch {
      return url;
    }
  };

  return (
    <>
      {/* Backdrop */}
      <div 
        className="fixed inset-0 bg-black bg-opacity-50 z-40"
        onClick={onClose}
        aria-hidden="true"
      />
      
      {/* Drawer */}
      <div
        ref={drawerRef}
        className="fixed right-0 top-0 h-full w-full max-w-md bg-white shadow-xl z-50 transform transition-transform duration-300 ease-in-out"
        tabIndex={-1}
        role="dialog"
        aria-modal="true"
        aria-labelledby="source-drawer-title"
      >
        <div className="flex flex-col h-full">
          {/* Header */}
          <div className="flex items-center justify-between p-6 border-b border-gray-200">
            <h2 id="source-drawer-title" className="text-lg font-semibold text-gray-900">
              Source Information
            </h2>
            <button
              onClick={onClose}
              className="p-2 text-gray-400 hover:text-gray-600 transition-colors"
              aria-label="Close drawer"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>

          {/* Content */}
          <div className="flex-1 p-6 overflow-y-auto">
            {source ? (
              <div className="space-y-6">
                {/* Origin */}
                <div>
                  <h3 className="text-sm font-medium text-gray-600 mb-2">Origin</h3>
                  <p className="text-gray-900">{getDomain(source.origin)}</p>
                  <p className="text-sm text-gray-500 mt-1">{source.origin}</p>
                </div>

                {/* Author */}
                {source.author && (
                  <div>
                    <h3 className="text-sm font-medium text-gray-600 mb-2">Author</h3>
                    <p className="text-gray-900">{source.author}</p>
                  </div>
                )}

                {/* Retrieved At */}
                {source.retrieved_at && (
                  <div>
                    <h3 className="text-sm font-medium text-gray-600 mb-2">Retrieved</h3>
                    <p className="text-gray-900">{formatDate(source.retrieved_at)}</p>
                  </div>
                )}

                {/* Credibility */}
                {source.credibility && (
                  <div>
                    <h3 className="text-sm font-medium text-gray-600 mb-2">Credibility</h3>
                    <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${getCredibilityColor(source.credibility)}`}>
                      {getCredibilityLabel(source.credibility)}
                    </span>
                  </div>
                )}
              </div>
            ) : (
              <div className="text-center py-8">
                <p className="text-gray-500">No source information available</p>
              </div>
            )}
          </div>

          {/* Footer */}
          <div className="p-6 border-t border-gray-200">
            {signalUrl && (
              <a
                href={signalUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="w-full inline-flex items-center justify-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
              >
                Open source
                <span className="ml-1">↗</span>
              </a>
            )}
          </div>
        </div>
      </div>
    </>
  );
}
