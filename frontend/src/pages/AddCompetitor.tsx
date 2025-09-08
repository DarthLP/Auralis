import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  startCrawlDiscovery,
  startFingerprinting,
  startExtraction,
  ExtractionProgressTracker,
  companies
} from '../lib/api';
import { 
  ValidationResult, 
  checkReachability, 
  checkDeduplication 
} from '../utils/urlValidation';
import UrlInputWithValidate from '../components/UrlInputWithValidate';
import DedupAlert from '../components/DedupAlert';

interface ProcessingState {
  phase: 'idle' | 'discovering' | 'fingerprinting' | 'extracting' | 'completed' | 'error';
  crawlSessionId: number | null;
  fingerprintSessionId: number | null;
  extractionSessionId: number | null;
  
  // Progress tracking
  progress: {
    discoveredPages: number;
    processedPages: number;
    extractedPages: number;
    totalPages: number;
    entitiesFound: {
      companies: number;
      products: number;
      capabilities: number;
      releases: number;
      documents: number;
      signals: number;
    };
  };
  
  // Real-time metrics
  metrics: {
    qps: number;
    etaSeconds: number | null;
    cacheHits: number;
    retries: number;
  };
  
  error: string | null;
  competitorName: string | null;
}

export default function AddCompetitor() {
  const navigate = useNavigate();
  const [url, setUrl] = useState('');
  const [validationResult, setValidationResult] = useState<ValidationResult | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [existingCompanies, setExistingCompanies] = useState<Array<{ id: string; name: string; website?: string | null }>>([]);
  const [processingState, setProcessingState] = useState<ProcessingState>({
    phase: 'idle',
    crawlSessionId: null,
    fingerprintSessionId: null,
    extractionSessionId: null,
    progress: {
      discoveredPages: 0,
      processedPages: 0,
      extractedPages: 0,
      totalPages: 0,
      entitiesFound: { companies: 0, products: 0, capabilities: 0, releases: 0, documents: 0, signals: 0 }
    },
    metrics: { qps: 0, etaSeconds: null, cacheHits: 0, retries: 0 },
    error: null,
    competitorName: null
  });
  const [progressTracker, setProgressTracker] = useState<ExtractionProgressTracker | null>(null);

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

  // Cleanup progress tracker on unmount
  useEffect(() => {
    return () => {
      if (progressTracker) {
        progressTracker.close();
      }
    };
  }, [progressTracker]);

  const extractCompetitorNameFromDomain = (domain: string): string => {
    return domain
      .replace('www.', '')
      .split('.')[0]
      .replace(/[-_]/g, ' ')
      .replace(/\b\w/g, l => l.toUpperCase());
  };

  const startProgressTracking = (extractionSessionId: number) => {
    const tracker = new ExtractionProgressTracker();
    
    tracker.on('metrics', (data: any) => {
      setProcessingState(prev => ({
        ...prev,
        metrics: {
          qps: data.qps || 0,
          etaSeconds: data.eta_seconds || null,
          cacheHits: data.cache_hits || 0,
          retries: data.retries || 0
        }
      }));
    });
    
    tracker.on('page_extracted', (_data: any) => {
      setProcessingState(prev => ({
        ...prev,
        progress: {
          ...prev.progress,
          extractedPages: prev.progress.extractedPages + 1
        }
      }));
    });
    
    tracker.on('session_completed', async (data: any) => {
      setProcessingState(prev => ({
        ...prev,
        phase: 'completed',
        progress: {
          ...prev.progress,
          entitiesFound: {
            companies: data.stats?.companies_found || 0,
            products: data.stats?.products_found || 0,
            capabilities: data.stats?.capabilities_found || 0,
            releases: data.stats?.releases_found || 0,
            documents: data.stats?.documents_found || 0,
            signals: data.stats?.signals_found || 0
          }
        }
      }));
      
      // Auto-redirect to companies page with success message
      setTimeout(() => {
        navigate('/companies', { 
          state: { 
            message: `Successfully analyzed and added ${processingState.competitorName}! Found ${data.stats?.companies_found || 0} companies, ${data.stats?.products_found || 0} products, and ${data.stats?.capabilities_found || 0} capabilities.`
          }
        });
      }, 3000);
    });
    
    tracker.on('error', (data: any) => {
      setProcessingState(prev => ({
        ...prev,
        phase: 'error',
        error: data.message || 'Extraction failed'
      }));
      setIsAnalyzing(false);
    });
    
    tracker.subscribe(extractionSessionId);
    setProgressTracker(tracker);
  };

  const handleAnalyze = async () => {
    if (!validationResult?.ok) return;

    setIsAnalyzing(true);
    setErrors({});
    setProcessingState(prev => ({ ...prev, phase: 'discovering', error: null }));

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

      // Extract competitor name
      const competitorName = extractCompetitorNameFromDomain(validationResult.eTLD1);
      setProcessingState(prev => ({ ...prev, competitorName }));

      // Phase 1: Discovery
      const crawlResult = await startCrawlDiscovery(validationResult.normalized_origin);
      
      setProcessingState(prev => ({
        ...prev,
        phase: 'fingerprinting',
        crawlSessionId: crawlResult.crawl_session_id,
        progress: {
          ...prev.progress,
          discoveredPages: crawlResult.pages.length,
          totalPages: crawlResult.pages.length
        }
      }));

      // Phase 2: Fingerprinting
      const fingerprintResult = await startFingerprinting(
        crawlResult.crawl_session_id, 
        competitorName
      );
      
      setProcessingState(prev => ({
        ...prev,
        phase: 'extracting',
        fingerprintSessionId: fingerprintResult.fingerprint_session_id,
        progress: {
          ...prev.progress,
          processedPages: fingerprintResult.total_processed
        }
      }));

      // Phase 3: Extraction
      const extractionResult = await startExtraction({
        fingerprint_session_id: fingerprintResult.fingerprint_session_id,
        competitor: competitorName,
        schema_version: 'v1'
      });
      
      setProcessingState(prev => ({
        ...prev,
        extractionSessionId: extractionResult.extraction_session_id
      }));

      // Start real-time progress tracking
      startProgressTracking(extractionResult.extraction_session_id);
      
    } catch (error) {
      console.error('Analysis failed:', error);
      setProcessingState(prev => ({
        ...prev,
        phase: 'error',
        error: error instanceof Error ? error.message : 'Analysis failed'
      }));
      setErrors({ general: 'Failed to analyze website. Please try again.' });
      setIsAnalyzing(false);
    }
  };

  const handleCancel = () => {
    if (progressTracker) {
      progressTracker.close();
    }
    navigate('/companies');
  };

  const isUrlValid = validationResult?.ok || false;

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

      {/* Progress Tracking */}
      {processingState.phase !== 'idle' && (
        <div className="bg-white rounded-lg border border-gray-200 p-6 mb-6">
          <div className="mb-4">
            <h3 className="text-lg font-semibold text-gray-900">Analysis Progress</h3>
            <div className="mt-2 flex items-center space-x-4">
              <div className={`flex items-center ${processingState.phase === 'discovering' ? 'text-blue-600' : processingState.phase === 'completed' ? 'text-green-600' : 'text-gray-400'}`}>
                <div className={`w-3 h-3 rounded-full mr-2 ${processingState.phase === 'discovering' ? 'bg-blue-600 animate-pulse' : processingState.phase === 'completed' ? 'bg-green-600' : 'bg-gray-300'}`} />
                <span className="text-sm font-medium">Discovery</span>
              </div>
              <div className={`flex items-center ${processingState.phase === 'fingerprinting' ? 'text-blue-600' : processingState.phase === 'completed' ? 'text-green-600' : 'text-gray-400'}`}>
                <div className={`w-3 h-3 rounded-full mr-2 ${processingState.phase === 'fingerprinting' ? 'bg-blue-600 animate-pulse' : processingState.phase === 'completed' ? 'bg-green-600' : 'bg-gray-300'}`} />
                <span className="text-sm font-medium">Fingerprinting</span>
              </div>
              <div className={`flex items-center ${processingState.phase === 'extracting' ? 'text-blue-600' : processingState.phase === 'completed' ? 'text-green-600' : 'text-gray-400'}`}>
                <div className={`w-3 h-3 rounded-full mr-2 ${processingState.phase === 'extracting' ? 'bg-blue-600 animate-pulse' : processingState.phase === 'completed' ? 'bg-green-600' : 'bg-gray-300'}`} />
                <span className="text-sm font-medium">Extraction</span>
              </div>
              <div className={`flex items-center ${processingState.phase === 'completed' ? 'text-green-600' : 'text-gray-400'}`}>
                <div className={`w-3 h-3 rounded-full mr-2 ${processingState.phase === 'completed' ? 'bg-green-600' : 'bg-gray-300'}`} />
                <span className="text-sm font-medium">Complete</span>
              </div>
            </div>
          </div>

          {/* Progress Bars */}
          <div className="space-y-3">
            <div>
              <div className="flex justify-between text-sm text-gray-600 mb-1">
                <span>Pages Discovered</span>
                <span>{processingState.progress.discoveredPages}</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div 
                  className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                  style={{ width: '100%' }}
                />
              </div>
            </div>

            <div>
              <div className="flex justify-between text-sm text-gray-600 mb-1">
                <span>Pages Processed</span>
                <span>{processingState.progress.processedPages}/{processingState.progress.totalPages}</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div 
                  className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                  style={{ 
                    width: `${(processingState.progress.processedPages / Math.max(processingState.progress.totalPages, 1)) * 100}%` 
                  }}
                />
              </div>
            </div>

            {processingState.phase === 'extracting' && (
              <div>
                <div className="flex justify-between text-sm text-gray-600 mb-1">
                  <span>Pages Extracted</span>
                  <span>{processingState.progress.extractedPages}/{processingState.progress.totalPages}</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div 
                    className="bg-green-600 h-2 rounded-full transition-all duration-300"
                    style={{ 
                      width: `${(processingState.progress.extractedPages / Math.max(processingState.progress.totalPages, 1)) * 100}%` 
                    }}
                  />
                </div>
              </div>
            )}
          </div>

          {/* Real-time Metrics */}
          {processingState.phase === 'extracting' && (
            <div className="mt-4 grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
              <div className="text-center">
                <div className="text-gray-500">Speed</div>
                <div className="font-semibold">{processingState.metrics.qps.toFixed(1)} pages/sec</div>
              </div>
              <div className="text-center">
                <div className="text-gray-500">ETA</div>
                <div className="font-semibold">
                  {processingState.metrics.etaSeconds 
                    ? `${Math.ceil(processingState.metrics.etaSeconds / 60)}m ${processingState.metrics.etaSeconds % 60}s`
                    : 'Calculating...'
                  }
                </div>
              </div>
              <div className="text-center">
                <div className="text-gray-500">Cache Hits</div>
                <div className="font-semibold">{processingState.metrics.cacheHits}</div>
              </div>
              <div className="text-center">
                <div className="text-gray-500">Retries</div>
                <div className="font-semibold">{processingState.metrics.retries}</div>
              </div>
            </div>
          )}

          {/* Entities Found */}
          {processingState.phase === 'completed' && (
            <div className="mt-4 p-4 bg-green-50 rounded-lg">
              <h4 className="text-sm font-medium text-green-800 mb-2">Entities Extracted</h4>
              <div className="grid grid-cols-2 md:grid-cols-3 gap-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-green-700">Companies:</span>
                  <span className="font-semibold text-green-800">{processingState.progress.entitiesFound.companies}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-green-700">Products:</span>
                  <span className="font-semibold text-green-800">{processingState.progress.entitiesFound.products}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-green-700">Capabilities:</span>
                  <span className="font-semibold text-green-800">{processingState.progress.entitiesFound.capabilities}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-green-700">Releases:</span>
                  <span className="font-semibold text-green-800">{processingState.progress.entitiesFound.releases}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-green-700">Documents:</span>
                  <span className="font-semibold text-green-800">{processingState.progress.entitiesFound.documents}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-green-700">Signals:</span>
                  <span className="font-semibold text-green-800">{processingState.progress.entitiesFound.signals}</span>
                </div>
              </div>
              <div className="mt-3 text-sm text-green-700">
                <p>✅ Analysis complete! Redirecting to companies page...</p>
              </div>
            </div>
          )}

          {/* Error State */}
          {processingState.phase === 'error' && (
            <div className="mt-4 p-4 bg-red-50 rounded-lg">
              <h4 className="text-sm font-medium text-red-800 mb-2">Analysis Failed</h4>
              <p className="text-sm text-red-700">{processingState.error}</p>
            </div>
          )}
        </div>
      )}

      {/* Actions */}
      {processingState.phase === 'idle' && (
        <div className="flex items-center justify-end">
          <button
            onClick={handleCancel}
            className="px-4 py-2 text-gray-600 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
          >
            Cancel
          </button>
        </div>
      )}
    </div>
  );
}
