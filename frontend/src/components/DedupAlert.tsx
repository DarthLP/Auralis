import { Link } from 'react-router-dom';

interface DedupAlertProps {
  existingCompanyId: string;
  existingCompanyName: string;
  className?: string;
}

export default function DedupAlert({ 
  existingCompanyId, 
  existingCompanyName, 
  className = "" 
}: DedupAlertProps) {
  return (
    <div className={`bg-yellow-50 border border-yellow-200 rounded-lg p-4 ${className}`}>
      <div className="flex items-start">
        <div className="flex-shrink-0">
          <svg className="w-5 h-5 text-yellow-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
          </svg>
        </div>
        <div className="ml-3 flex-1">
          <h3 className="text-sm font-medium text-yellow-800">
            Duplicate Company Detected
          </h3>
          <div className="mt-2 text-sm text-yellow-700">
            <p>
              Looks like this company already exists — <strong>{existingCompanyName}</strong>
            </p>
            <p className="mt-1">
              You can either edit the existing company or continue with creating a new one.
            </p>
          </div>
          <div className="mt-3">
            <Link
              to={`/companies/${existingCompanyId}`}
              className="inline-flex items-center px-3 py-2 border border-transparent text-sm font-medium rounded-md text-yellow-800 bg-yellow-100 hover:bg-yellow-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-yellow-500 transition-colors"
            >
              Go to existing company
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
