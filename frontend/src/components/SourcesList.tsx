interface Source {
  origin: string;
  author?: string;
  retrieved_at: string;
}

interface SourcesListProps {
  sources: Source[];
  className?: string;
}

export default function SourcesList({ sources, className = "" }: SourcesListProps) {
  const getDomain = (url: string) => {
    try {
      return new URL(url).hostname;
    } catch {
      return url;
    }
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  return (
    <div className={`space-y-2 ${className}`}>
      <h3 className="text-sm font-medium text-gray-900">Sources</h3>
      
      {sources.length === 0 ? (
        <p className="text-sm text-gray-500">No sources available</p>
      ) : (
        <div className="space-y-2">
          {sources.map((source, index) => (
            <div key={index} className="p-3 bg-gray-50 border border-gray-200 rounded-lg">
              <div className="flex items-start justify-between">
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-gray-900 truncate">
                    {getDomain(source.origin)}
                  </p>
                  <p className="text-xs text-gray-500 truncate">
                    {source.origin}
                  </p>
                  {source.author && (
                    <p className="text-xs text-gray-600 mt-1">
                      Author: {source.author}
                    </p>
                  )}
                  <p className="text-xs text-gray-500 mt-1">
                    Retrieved: {formatDate(source.retrieved_at)}
                  </p>
                </div>
                <a
                  href={source.origin}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="ml-2 text-blue-600 hover:text-blue-800 text-xs"
                >
                  ↗
                </a>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
