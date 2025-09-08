import { useState, useEffect, useCallback } from 'react';
import { validateAndNormalizeUrl, ValidationResult } from '../utils/urlValidation';

interface UrlInputWithValidateProps {
  value: string;
  onChange: (value: string) => void;
  onValidationChange?: (result: ValidationResult) => void;
  placeholder?: string;
  className?: string;
  showETLD1?: boolean;
}

export default function UrlInputWithValidate({ 
  value, 
  onChange, 
  onValidationChange,
  placeholder = "https://example.com",
  className = "",
  showETLD1: _showETLD1 = true
}: UrlInputWithValidateProps) {
  const [validationResult, setValidationResult] = useState<ValidationResult | null>(null);
  const [isValidating, setIsValidating] = useState(false);

  // Debounced validation
  const debouncedValidation = useCallback(
    (() => {
      let timeoutId: number;
      return (inputValue: string) => {
        clearTimeout(timeoutId);
        timeoutId = setTimeout(() => {
          if (!inputValue.trim()) {
            setValidationResult(null);
            onValidationChange?.(null as any);
            return;
          }

          setIsValidating(true);
          const result = validateAndNormalizeUrl(inputValue);
          setValidationResult(result);
          onValidationChange?.(result);
          setIsValidating(false);
        }, 250);
      };
    })(),
    [onValidationChange]
  );

  useEffect(() => {
    debouncedValidation(value);
  }, [value, debouncedValidation]);

  const getInputStyles = () => {
    if (isValidating) {
      return 'border-blue-300 bg-blue-50';
    }
    if (validationResult === null) {
      return 'border-gray-300';
    }
    return validationResult.ok 
      ? 'border-green-300 bg-green-50' 
      : 'border-red-300 bg-red-50';
  };

  const getStatusIcon = () => {
    if (isValidating) {
      return (
        <svg className="w-5 h-5 text-blue-500 animate-spin" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
        </svg>
      );
    }
    if (validationResult === null) {
      return null;
    }
    return validationResult.ok ? (
      <svg className="w-5 h-5 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
      </svg>
    ) : (
      <svg className="w-5 h-5 text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
      </svg>
    );
  };

  return (
    <div className={`space-y-2 ${className}`}>
      <div className="relative">
        <input
          type="url"
          value={value}
          onChange={(e) => onChange(e.target.value)}
          placeholder={placeholder}
          className={`w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent ${getInputStyles()}`}
        />
        <div className="absolute right-3 top-1/2 transform -translate-y-1/2">
          {getStatusIcon()}
        </div>
      </div>

      {/* Validation feedback */}
      {validationResult && !validationResult.ok && (
        <p className="text-sm text-red-600">{validationResult.reason}</p>
      )}
      
      {validationResult?.ok && validationResult.original_path && (
        <div className="flex items-center gap-2 text-xs text-gray-500">
          <span>Will analyze:</span>
          <code className="bg-gray-100 px-1 rounded">{validationResult.normalized_origin}</code>
        </div>
      )}
    </div>
  );
}
