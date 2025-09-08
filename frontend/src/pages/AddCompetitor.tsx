import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  startScraperJob, 
  getScraperJob, 
  saveCompetitor, 
  ScraperJob, 
  ScraperResult,
  companies
} from '../lib/mockData';
import { 
  ValidationResult, 
  checkReachability, 
  checkDeduplication 
} from '../utils/urlValidation';
import UrlInputWithValidate from '../components/UrlInputWithValidate';
import JobStatusBadge from '../components/JobStatusBadge';
import EditableTagInput from '../components/EditableTagInput';
import ProductsEditor from '../components/ProductsEditor';
import SourcesList from '../components/SourcesList';
import DedupAlert from '../components/DedupAlert';

export default function AddCompetitor() {
  const navigate = useNavigate();
  const [url, setUrl] = useState('');
  const [validationResult, setValidationResult] = useState<ValidationResult | null>(null);
  const [currentJob, setCurrentJob] = useState<ScraperJob | null>(null);
  const [previewData, setPreviewData] = useState<ScraperResult | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [existingCompanies, setExistingCompanies] = useState<Array<{ id: string; name: string; website?: string | null }>>([]);

  // Load existing companies for deduplication
  useEffect(() => {
    const loadCompanies = async () => {
      try {
        const companiesList = await companies();
        setExistingCompanies(companiesList);
      } catch (error) {
        console.error('Failed to load companies for deduplication:', error);
      }
    };
    loadCompanies();
  }, []);

  // Poll job status when job is active
  useEffect(() => {
    if (!currentJob || currentJob.status === 'done' || currentJob.status === 'error') {
      return;
    }

    const interval = setInterval(async () => {
      const updatedJob = await getScraperJob(currentJob.id);
      if (updatedJob) {
        setCurrentJob(updatedJob);
        if (updatedJob.status === 'done' && updatedJob.result) {
          setPreviewData(updatedJob.result);
          setIsAnalyzing(false);
        } else if (updatedJob.status === 'error') {
          setIsAnalyzing(false);
        }
      }
    }, 500);

    return () => clearInterval(interval);
  }, [currentJob]);

  const handleAnalyze = async () => {
    if (!validationResult?.ok) return;

    setIsAnalyzing(true);
    setErrors({});
    setPreviewData(null);

    try {
      // First check reachability
      const reachabilityResult = await checkReachability(validationResult.normalized_origin);
      
      if (!reachabilityResult.ok) {
        setErrors({ url: reachabilityResult.reason || 'Website is not reachable' });
        setIsAnalyzing(false);
        return;
      }

      // Check for duplicates
      const dedupeResult = checkDeduplication(
        validationResult.eTLD1,
        validationResult.eTLD1.replace(/[^a-z0-9]/g, ' ').replace(/\s+/g, ' ').trim(),
        existingCompanies
      );

      if (dedupeResult.isDuplicate) {
        setErrors({ 
          dedupe: `Company already exists: ${dedupeResult.existing_company_name}`,
          existing_company_id: dedupeResult.existing_company_id || '',
          existing_company_name: dedupeResult.existing_company_name || ''
        });
        setIsAnalyzing(false);
        return;
      }

      // Start scraper job with normalized URL
      const job = await startScraperJob(validationResult.normalized_origin);
      setCurrentJob(job);
    } catch (error) {
      console.error('Failed to start scraper job:', error);
      setIsAnalyzing(false);
      setErrors({ general: 'Failed to start analysis. Please try again.' });
    }
  };

  const handleSave = async () => {
    if (!previewData) return;

    // Validation
    const newErrors: Record<string, string> = {};
    
    if (!previewData.company.name.trim()) {
      newErrors.companyName = 'Company name is required';
    }
    
    if (!previewData.company.website.trim()) {
      newErrors.website = 'Website is required';
    }
    
    if (previewData.products.length === 0 && !previewData.summary.one_liner.trim()) {
      newErrors.content = 'At least one product or company description is required';
    }

    // Validate products
    previewData.products.forEach((product, index) => {
      if (!product.name.trim()) {
        newErrors[`product_${index}_name`] = 'Product name is required';
      }
    });

    if (Object.keys(newErrors).length > 0) {
      setErrors(newErrors);
      return;
    }

    setIsSaving(true);
    setErrors({});

    try {
      const result = await saveCompetitor(previewData);
      navigate(`/companies/${result.company_id}`, { 
        state: { message: 'Company created successfully!' }
      });
    } catch (error) {
      console.error('Failed to save competitor:', error);
      setErrors({ general: 'Failed to save company. Please try again.' });
    } finally {
      setIsSaving(false);
    }
  };

  const handleCancel = () => {
    navigate('/companies');
  };

  const updatePreviewData = (updates: Partial<ScraperResult>) => {
    if (previewData) {
      setPreviewData({ ...previewData, ...updates });
    }
  };

  const updateCompany = (updates: Partial<ScraperResult['company']>) => {
    if (previewData) {
      updatePreviewData({
        company: { ...previewData.company, ...updates }
      });
    }
  };

  const updateSummary = (updates: Partial<ScraperResult['summary']>) => {
    if (previewData) {
      updatePreviewData({
        summary: { ...previewData.summary, ...updates }
      });
    }
  };

  const isUrlValid = validationResult?.ok || false;

  const canSave = previewData && 
    currentJob?.status === 'done' && 
    !isSaving &&
    !previewData.dedupe;

  return (
    <div className="container max-w-4xl">
      {/* General Error */}
      {errors.general && (
        <div className="mb-6 bg-red-50 border border-red-200 rounded-lg p-4">
          <p className="text-red-800">{errors.general}</p>
        </div>
      )}

      {/* URL Input Card */}
      <div className="bg-white rounded-lg border border-gray-200 p-6 mb-6">
        <div className="mb-6">
          <h1 className="text-2xl font-bold text-gray-900 mb-3">Add New Competitor</h1>
          <p className="text-gray-600 mb-4">
            Enter a competitor's website URL below. Our system will automatically analyze their website to extract company information, products, and key details. This helps you quickly add new competitors to your tracking database without manual data entry.
          </p>
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <div className="flex items-start">
              <svg className="w-5 h-5 text-blue-600 mt-0.5 mr-3 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <div>
                <h3 className="text-sm font-medium text-blue-800 mb-1">How it works:</h3>
                <ul className="text-sm text-blue-700 space-y-1">
                  <li>• Paste any company website URL (e.g., https://example.com)</li>
                  <li>• We'll validate the URL and check if the company already exists</li>
                  <li>• Our scraper extracts company name, description, products, and tags</li>
                  <li>• Review and edit the extracted data before saving</li>
                </ul>
              </div>
            </div>
          </div>
        </div>
        
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Website URL *
            </label>
            <UrlInputWithValidate
              value={url}
              onChange={setUrl}
              onValidationChange={setValidationResult}
              placeholder="https://example.com"
            />
            {errors.url && (
              <p className="mt-1 text-sm text-red-600">{errors.url}</p>
            )}
            {errors.dedupe && (
              <div className="mt-2">
                <DedupAlert
                  existingCompanyId={errors.existing_company_id || ''}
                  existingCompanyName={errors.existing_company_name || ''}
                />
              </div>
            )}
          </div>

          <div className="flex justify-end">
            <button
              onClick={handleAnalyze}
              disabled={!isUrlValid || isAnalyzing}
              className="inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
            >
              {isAnalyzing ? (
                <>
                  <svg className="w-4 h-4 mr-2 animate-spin" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                  </svg>
                  Analyzing...
                </>
              ) : (
                'Start Analyzing'
              )}
            </button>
          </div>
        </div>
      </div>

      {/* Status Row */}
      {currentJob && (
        <div className="bg-white rounded-lg border border-gray-200 p-4 mb-6">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-sm font-medium text-gray-900">Analysis Status</h3>
              <p className="text-sm text-gray-600 mt-1">
                {currentJob.status === 'queued' && 'Job queued for processing...'}
                {currentJob.status === 'processing' && 'Extracting company information...'}
                {currentJob.status === 'done' && 'Analysis complete!'}
                {currentJob.status === 'error' && 'Analysis failed. Please try again.'}
              </p>
            </div>
            <JobStatusBadge status={currentJob.status} />
          </div>
        </div>
      )}

      {/* Preview Form */}
      {previewData && currentJob?.status === 'done' && (
        <div className="bg-white rounded-lg border border-gray-200 p-6 mb-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-6">Preview & Edit</h2>

          {/* Dedupe Alert */}
          {previewData.dedupe && (
            <DedupAlert
              existingCompanyId={previewData.dedupe.existing_company_id}
              existingCompanyName={previewData.dedupe.existing_company_name}
              className="mb-6"
            />
          )}

          <div className="space-y-6">
            {/* Company Information */}
            <div>
              <h3 className="text-sm font-medium text-gray-900 mb-4">Company Information</h3>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Company Name *
                  </label>
                  <input
                    type="text"
                    value={previewData.company.name}
                    onChange={(e) => updateCompany({ name: e.target.value })}
                    className={`w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent ${
                      errors.companyName ? 'border-red-300' : 'border-gray-300'
                    }`}
                  />
                  {errors.companyName && (
                    <p className="mt-1 text-sm text-red-600">{errors.companyName}</p>
                  )}
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Website
                  </label>
                  <input
                    type="url"
                    value={previewData.company.website}
                    readOnly
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg bg-gray-50 text-gray-500"
                  />
                </div>
              </div>

              <div className="mt-4">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  HQ Country
                </label>
                <input
                  type="text"
                  value={previewData.company.hq_country || ''}
                  onChange={(e) => updateCompany({ hq_country: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="e.g., United States, Germany, etc."
                />
              </div>

              <div className="mt-4">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Tags
                </label>
                <EditableTagInput
                  tags={previewData.company.tags}
                  onChange={(tags) => updateCompany({ tags })}
                  maxTags={8}
                />
              </div>

              <div className="mt-4">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  One-liner
                </label>
                <textarea
                  value={previewData.summary.one_liner}
                  onChange={(e) => updateSummary({ one_liner: e.target.value })}
                  rows={3}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="Brief description of the company"
                />
                {errors.content && (
                  <p className="mt-1 text-sm text-red-600">{errors.content}</p>
                )}
              </div>
            </div>

            {/* Products */}
            <ProductsEditor
              products={previewData.products}
              onChange={(products) => updatePreviewData({ products })}
            />

            {/* Sources */}
            <SourcesList sources={previewData.sources} />
          </div>
        </div>
      )}

      {/* Actions */}
      {previewData && currentJob?.status === 'done' && (
        <div className="flex items-center justify-between">
          <button
            onClick={handleCancel}
            className="px-4 py-2 text-gray-600 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
          >
            Cancel
          </button>

          <button
            onClick={handleSave}
            disabled={!canSave}
            className="inline-flex items-center px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
          >
            {isSaving ? (
              <>
                <svg className="w-4 h-4 mr-2 animate-spin" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                </svg>
                Saving...
              </>
            ) : (
              'Save & Add'
            )}
          </button>
        </div>
      )}
    </div>
  );
}
