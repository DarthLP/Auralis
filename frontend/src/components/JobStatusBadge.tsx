import { ScraperJobStatus } from '../lib/api';

interface JobStatusBadgeProps {
  status: ScraperJobStatus;
  className?: string;
}

export default function JobStatusBadge({ status, className = "" }: JobStatusBadgeProps) {
  const getStatusConfig = (status: ScraperJobStatus) => {
    switch (status) {
      case 'queued':
        return {
          label: 'Queued',
          bgColor: 'bg-gray-100',
          textColor: 'text-gray-800',
          icon: (
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          )
        };
      case 'processing':
        return {
          label: 'Processing',
          bgColor: 'bg-blue-100',
          textColor: 'text-blue-800',
          icon: (
            <svg className="w-4 h-4 animate-spin" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
          )
        };
      case 'done':
        return {
          label: 'Done',
          bgColor: 'bg-green-100',
          textColor: 'text-green-800',
          icon: (
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
            </svg>
          )
        };
      case 'error':
        return {
          label: 'Error',
          bgColor: 'bg-red-100',
          textColor: 'text-red-800',
          icon: (
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          )
        };
    }
  };

  const config = getStatusConfig(status);

  return (
    <div className={`inline-flex items-center gap-2 px-3 py-1 rounded-full text-sm font-medium ${config.bgColor} ${config.textColor} ${className}`}>
      {config.icon}
      {config.label}
    </div>
  );
}
