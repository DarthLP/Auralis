import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  startCrawlDiscovery,
  startFingerprinting,
  startExtraction,
  getExtractionStatus,
  stopCrawl,
  scorePagesWithAI,
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
  phase: 'idle' | 'discovering' | 'discovery_complete' | 'scoring' | 'fingerprinting' | 'extracting' | 'completed' | 'error';
  crawlSessionId: number | null;
  fingerprintSessionId: number | null;
  extractionSessionId: number | null;
  
  // Step completion tracking
  stepsCompleted: {
    discovery: boolean;
    scoring: boolean;
    fingerprinting: boolean;
    extraction: boolean;
  };
  
  // Progress tracking
  progress: {
    discoveredPages: number;
    processedPages: number;
    extractedPages: number;
    totalPages: number;
    skippedPages: number;
    entitiesFound: {
      companies: number;
      products: number;
      capabilities: number;
      documents: number;
      signals: number;
    };
  };
  
  // Extracted companies
  extractedCompanies: any[];
  
  // Real-time metrics
  metrics: {
    qps: number;
    etaSeconds: number | null;
    cacheHits: number;
    retries: number;
  };
  
  // Debug information
  discoveredPages: Array<{
    url: string;
    score: number;
    primary_category: string;
    secondary_categories: string[];
    scoring_method: string;
    ai_confidence?: number;
    ai_reasoning?: string;
    signals: string[];
    // Content fields for AI scoring
    has_minimal_content: boolean;
    title: string;
    h1: string;
    h2: string;
    h3: string;
    content_length: number;
    // Dual scoring debug fields
    ai_score?: number | null;
    ai_category?: string;
    ai_signals?: string[];
    ai_success?: boolean;
    ai_scoring_reason?: string;
    ai_error?: string;
    rules_score?: number | null;
    rules_category?: string;
    rules_signals?: string[];
  }>;
  
  // Skipped URLs information
  skippedUrls: Array<{
    url: string;
    reason: string;
  }>;
  
  // Sitemap processing information
  sitemapUrls: string[];
  filteredSitemapUrls: string[];
  sitemapFilteredCount: number;
  sitemapProcessedCount: number;
  
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
    stepsCompleted: {
      discovery: false,
      scoring: false,
      fingerprinting: false,
      extraction: false
    },
    progress: {
      discoveredPages: 0,
      processedPages: 0,
      extractedPages: 0,
      totalPages: 0,
      skippedPages: 0,
      entitiesFound: { companies: 0, products: 0, capabilities: 0, documents: 0, signals: 0 }
    },
    extractedCompanies: [],
    metrics: { qps: 0, etaSeconds: null, cacheHits: 0, retries: 0 },
    discoveredPages: [],
    skippedUrls: [],
    sitemapUrls: [],
    filteredSitemapUrls: [],
    sitemapFilteredCount: 0,
    sitemapProcessedCount: 0,
    error: null,
    competitorName: null
  });
  const [progressTracker, setProgressTracker] = useState<ExtractionProgressTracker | null>(null);
  const [showDebugView, setShowDebugView] = useState(false);

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
    if (!domain || domain.trim() === '') {
      return 'Unknown';
    }
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
      // Fetch companies for this competitor (data is now in main companies table)
      let extractedCompaniesData: any[] = [];
      try {
        const allCompanies = await companies();
        // Filter by competitor name to find the newly added company
        extractedCompaniesData = allCompanies.filter(company => 
          company.name.toLowerCase().includes(processingState.competitorName?.toLowerCase() || '') ||
          company.aliases?.some((alias: string) => 
            alias.toLowerCase().includes(processingState.competitorName?.toLowerCase() || '')
          )
        );
      } catch (error) {
        console.error('Failed to fetch companies:', error);
      }
      
      setProcessingState(prev => ({
        ...prev,
        phase: 'completed',
        stepsCompleted: { ...prev.stepsCompleted, extraction: true },
        progress: {
          ...prev.progress,
          entitiesFound: {
            companies: data.stats?.companies_found || 0,
            products: data.stats?.products_found || 0,
            capabilities: data.stats?.capabilities_found || 0,
            documents: data.stats?.documents_found || 0,
            signals: data.stats?.signals_found || 0
          }
        },
        extractedCompanies: extractedCompaniesData
      }));
      setIsAnalyzing(false);
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
    
    // Fallback: Check extraction status every 5 seconds in case SSE doesn't work
    const statusCheckInterval = setInterval(async () => {
      try {
        const status = await getExtractionStatus(extractionSessionId);
        if (status.status === 'completed') {
          clearInterval(statusCheckInterval);
          
          // Fetch companies for this competitor (data is now in main companies table)
          let extractedCompaniesData: any[] = [];
          try {
            const allCompanies = await companies();
            // Filter by competitor name to find the newly added company
            extractedCompaniesData = allCompanies.filter(company => 
              company.name.toLowerCase().includes(processingState.competitorName?.toLowerCase() || '') ||
              company.aliases?.some((alias: string) => 
                alias.toLowerCase().includes(processingState.competitorName?.toLowerCase() || '')
              )
            );
          } catch (error) {
            console.error('Failed to fetch companies:', error);
          }
          
          setProcessingState(prev => ({
            ...prev,
            phase: 'completed',
            stepsCompleted: { ...prev.stepsCompleted, extraction: true },
            progress: {
              ...prev.progress,
              entitiesFound: {
                companies: status.stats?.companies_found || 0,
                products: status.stats?.products_found || 0,
                capabilities: status.stats?.capabilities_found || 0,
                documents: status.stats?.documents_found || 0,
                signals: status.stats?.signals_found || 0
              }
            },
            extractedCompanies: extractedCompaniesData
          }));
          setIsAnalyzing(false);
        } else if (status.status === 'failed') {
          clearInterval(statusCheckInterval);
          setProcessingState(prev => ({
            ...prev,
            phase: 'error',
            error: 'Extraction failed'
          }));
          setIsAnalyzing(false);
        }
      } catch (error) {
        console.error('Failed to check extraction status:', error);
      }
    }, 5000); // Check every 5 seconds for faster response
    
    // Clean up interval when component unmounts or tracker is closed
    const originalClose = tracker.close.bind(tracker);
    tracker.close = () => {
      clearInterval(statusCheckInterval);
      originalClose();
    };
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
      console.log('Validation result:', validationResult);
      console.log('eTLD1:', validationResult.eTLD1);
      const competitorName = extractCompetitorNameFromDomain(validationResult.eTLD1);
      console.log('Final competitor name:', competitorName);
      setProcessingState(prev => ({ ...prev, competitorName }));

      // Phase 1: Discovery Only
      const crawlResult = await startCrawlDiscovery(validationResult.normalized_origin);
      
      setProcessingState(prev => ({
        ...prev,
        phase: 'discovery_complete',
        crawlSessionId: crawlResult.crawl_session_id,
        stepsCompleted: { ...prev.stepsCompleted, discovery: true },
        progress: {
          ...prev.progress,
          discoveredPages: crawlResult.pages.length,
          totalPages: crawlResult.pages.length,
          skippedPages: crawlResult.skipped_urls || 0
        },
        discoveredPages: crawlResult.pages.map((page: any) => ({
          url: page.url,
          score: page.score || 0,
          primary_category: page.primary_category || 'other',
          secondary_categories: page.secondary_categories || [],
          scoring_method: page.scoring_method || 'rules',
          ai_confidence: page.ai_confidence,
          ai_reasoning: page.ai_reasoning,
          signals: page.signals || [],
          // Content fields for AI scoring
          has_minimal_content: page.has_minimal_content || false,
          title: page.title || '',
          h1: page.h1 || '',
          h2: page.h2 || '',
          h3: page.h3 || '',
          content_length: page.content_length || 0,
          // Dual scoring debug fields
          ai_score: page.ai_score,
          ai_category: page.ai_category,
          ai_signals: page.ai_signals || [],
          ai_success: page.ai_success,
          ai_scoring_reason: page.ai_scoring_reason,
          ai_error: page.ai_error,
          rules_score: page.rules_score,
          rules_category: page.rules_category,
          rules_signals: page.rules_signals || []
        })),
        skippedUrls: crawlResult.skipped_urls_details || [],
        sitemapUrls: crawlResult.sitemap_urls || [],
        filteredSitemapUrls: crawlResult.filtered_sitemap_urls || [],
        sitemapFilteredCount: crawlResult.sitemap_filtered_count || 0,
        sitemapProcessedCount: crawlResult.sitemap_processed_count || 0
      }));

      setIsAnalyzing(false);
      
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

  // Manual step functions
  const handleStartScoring = async () => {
    if (!processingState.discoveredPages.length || !processingState.competitorName) return;
    
    setIsAnalyzing(true);
    setProcessingState(prev => ({ ...prev, phase: 'scoring' }));

    try {
      const scoringResult = await scorePagesWithAI(
        processingState.discoveredPages,
        processingState.competitorName
      );
      
      setProcessingState(prev => ({
        ...prev,
        phase: 'scoring',  // Keep in scoring phase, don't auto-start fingerprinting
        stepsCompleted: { ...prev.stepsCompleted, scoring: true },
        discoveredPages: scoringResult.pages
      }));

      setIsAnalyzing(false);
    } catch (error) {
      console.error('AI scoring failed:', error);
      setProcessingState(prev => ({
        ...prev,
        phase: 'error',
        error: error instanceof Error ? error.message : 'AI scoring failed'
      }));
      setIsAnalyzing(false);
    }
  };

  const handleStartFingerprinting = async () => {
    if (!processingState.crawlSessionId || !processingState.competitorName) return;
    
    setIsAnalyzing(true);
    setProcessingState(prev => ({ ...prev, phase: 'fingerprinting' }));

    try {
      const fingerprintResult = await startFingerprinting(
        processingState.crawlSessionId, 
        processingState.competitorName
      );
      
      setProcessingState(prev => ({
        ...prev,
        phase: 'extracting',
        fingerprintSessionId: fingerprintResult.fingerprint_session_id,
        stepsCompleted: { ...prev.stepsCompleted, scoring: true, fingerprinting: true },
        progress: {
          ...prev.progress,
          processedPages: fingerprintResult.total_processed
        }
      }));

      setIsAnalyzing(false);
    } catch (error) {
      console.error('Fingerprinting failed:', error);
      setProcessingState(prev => ({
        ...prev,
        phase: 'error',
        error: error instanceof Error ? error.message : 'Fingerprinting failed'
      }));
      setIsAnalyzing(false);
    }
  };

  const handleStartExtraction = async () => {
    if (!processingState.fingerprintSessionId || !processingState.competitorName) return;
    
    setIsAnalyzing(true);
    setProcessingState(prev => ({ ...prev, phase: 'extracting' }));

    try {
      const extractionResult = await startExtraction({
        fingerprint_session_id: processingState.fingerprintSessionId,
        competitor: processingState.competitorName,
        schema_version: 'v1'
      });
      
      setProcessingState(prev => ({
        ...prev,
        extractionSessionId: extractionResult.extraction_session_id
      }));

      // Start real-time progress tracking
      startProgressTracking(extractionResult.extraction_session_id);
      
    } catch (error) {
      console.error('Extraction failed:', error);
      setProcessingState(prev => ({
        ...prev,
        phase: 'error',
        error: error instanceof Error ? error.message : 'Extraction failed'
      }));
      setIsAnalyzing(false);
    }
  };

  const handleStop = async () => {
    if (processingState.crawlSessionId) {
      try {
        await stopCrawl(processingState.crawlSessionId);
        setProcessingState(prev => ({
          ...prev,
          phase: 'error',
          error: 'Crawling stopped by user'
        }));
        setIsAnalyzing(false);
      } catch (error) {
        console.error('Failed to stop crawling:', error);
        setErrors({ general: 'Failed to stop crawling. Please try again.' });
      }
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

      {/* Stepped Process */}
      {processingState.phase !== 'idle' && (
        <div className="bg-white rounded-lg border border-gray-200 p-6 mb-6">
          <div className="mb-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Analysis Steps</h3>
            
            {/* Step 1: Discovery */}
            <div className="mb-6 p-4 border rounded-lg">
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center">
                  <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium ${
                    processingState.stepsCompleted.discovery 
                      ? 'bg-green-100 text-green-800' 
                      : processingState.phase === 'discovering'
                      ? 'bg-blue-100 text-blue-800 animate-pulse'
                      : 'bg-gray-100 text-gray-600'
                  }`}>
                    {processingState.stepsCompleted.discovery ? '✓' : '1'}
                  </div>
                  <div className="ml-3">
                    <h4 className="text-sm font-medium text-gray-900">Discovery</h4>
                    <p className="text-xs text-gray-500">Find and analyze pages</p>
                  </div>
                </div>
                {processingState.stepsCompleted.discovery && (
                  <div className="text-right">
                    <div className="text-sm text-green-600 font-medium">
                      {processingState.progress.discoveredPages} discovered
                    </div>
                    {processingState.progress.skippedPages > 0 && (
                      <div className="text-xs text-gray-500">
                        {processingState.progress.skippedPages} URLs skipped
                      </div>
                    )}
                  </div>
                )}
              </div>
              
              {processingState.stepsCompleted.discovery && (
                <div className="mt-3">
                  <div className="text-sm text-gray-600 mb-2">
                    Discovered {processingState.progress.discoveredPages} pages
                    {processingState.progress.skippedPages > 0 && (
                      <span className="ml-2 text-gray-500">
                        (skipped {processingState.progress.skippedPages} low-value URLs)
                      </span>
                    )}
                  </div>
                  
                  {/* Sitemap Processing Overview */}
                  {processingState.sitemapUrls.length > 0 && (
                    <div className="mb-4">
                      <h5 className="text-xs font-medium text-gray-700 mb-2">
                        Sitemap Processing ({processingState.sitemapUrls.length} URLs found)
                      </h5>
                      <div className="bg-blue-50 border border-blue-200 rounded-lg p-3 mb-3">
                        <div className="grid grid-cols-3 gap-4 text-xs">
                          <div className="text-center">
                            <div className="text-blue-600 font-semibold">{processingState.sitemapUrls.length}</div>
                            <div className="text-blue-700">Total Found</div>
                          </div>
                          <div className="text-center">
                            <div className="text-orange-600 font-semibold">{processingState.sitemapFilteredCount}</div>
                            <div className="text-orange-700">Filtered Out</div>
                          </div>
                          <div className="text-center">
                            <div className="text-green-600 font-semibold">{processingState.sitemapProcessedCount}</div>
                            <div className="text-green-700">Processed</div>
                          </div>
                        </div>
                      </div>
                    </div>
                  )}

                  {/* All Sitemap URLs */}
                  {processingState.sitemapUrls.length > 0 && (
                    <div className="mb-4">
                      <h5 className="text-xs font-medium text-gray-700 mb-2">All Sitemap URLs</h5>
                      <div className="max-h-32 overflow-y-auto">
                        <div className="space-y-1">
                          {processingState.sitemapUrls.map((url, index) => {
                            const isFiltered = !processingState.filteredSitemapUrls.includes(url);
                            const isProcessed = processingState.discoveredPages.some(page => page.url === url);
                            return (
                              <div key={index} className={`flex items-center justify-between text-xs p-2 rounded ${
                                isFiltered 
                                  ? 'bg-red-50 border-l-2 border-red-200' 
                                  : isProcessed
                                  ? 'bg-green-50 border-l-2 border-green-200'
                                  : 'bg-yellow-50 border-l-2 border-yellow-200'
                              }`}>
                                <span className="truncate flex-1 mr-2">{url}</span>
                                <span className={`text-xs px-2 py-1 rounded ${
                                  isFiltered 
                                    ? 'bg-red-100 text-red-700' 
                                    : isProcessed
                                    ? 'bg-green-100 text-green-700'
                                    : 'bg-yellow-100 text-yellow-700'
                                }`}>
                                  {isFiltered ? 'Filtered' : isProcessed ? 'Processed' : 'Queued'}
                                </span>
                              </div>
                            );
                          })}
                        </div>
                      </div>
                    </div>
                  )}

                  {/* Discovered Pages */}
                  <div className="mb-4">
                    <h5 className="text-xs font-medium text-gray-700 mb-2">Final Discovered Pages</h5>
                    <div className="max-h-40 overflow-y-auto">
                      <div className="space-y-1">
                        {processingState.discoveredPages.map((page, index) => (
                          <div key={index} className="flex items-center justify-between text-xs bg-gray-50 p-2 rounded">
                            <span className="truncate flex-1 mr-2">{page.url}</span>
                            <span className="text-gray-500">Score: {page.score.toFixed(2)}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>

                  {/* Skipped URLs */}
                  {processingState.progress.skippedPages > 0 && (
                    <div className="mb-4">
                      <h5 className="text-xs font-medium text-gray-700 mb-2">
                        Skipped URLs ({processingState.progress.skippedPages})
                      </h5>
                      <div className="max-h-32 overflow-y-auto">
                        <div className="space-y-1">
                          {processingState.skippedUrls.map((skipped, index) => (
                            <div key={index} className="flex items-start justify-between text-xs bg-red-50 p-2 rounded border-l-2 border-red-200">
                              <span className="truncate flex-1 mr-2 text-red-700">{skipped.url}</span>
                              <span className="text-red-500 text-right ml-2 flex-shrink-0">{skipped.reason}</span>
                            </div>
                          ))}
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>

            {/* Step 2: Scoring */}
            <div className="mb-6 p-4 border rounded-lg">
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center">
                  <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium ${
                    processingState.stepsCompleted.scoring 
                      ? 'bg-green-100 text-green-800' 
                      : (processingState.phase === 'scoring' || processingState.phase === 'discovery_complete')
                      ? 'bg-blue-100 text-blue-800 animate-pulse'
                      : 'bg-gray-100 text-gray-600'
                  }`}>
                    {processingState.stepsCompleted.scoring ? '✓' : '2'}
                  </div>
                  <div className="ml-3">
                    <h4 className="text-sm font-medium text-gray-900">Scoring</h4>
                    <p className="text-xs text-gray-500">AI-powered page scoring</p>
                  </div>
                </div>
                {processingState.stepsCompleted.scoring && (
                  <span className="text-sm text-green-600 font-medium">Completed</span>
                )}
              </div>
              
              {processingState.stepsCompleted.scoring && (
                <div className="mt-3">
                  <div className="text-sm text-gray-600 mb-2">
                    All pages scored with AI analysis
                  </div>
                </div>
              )}
            </div>

            {/* Step 3: Fingerprinting */}
            <div className="mb-6 p-4 border rounded-lg">
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center">
                  <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium ${
                    processingState.stepsCompleted.fingerprinting 
                      ? 'bg-green-100 text-green-800' 
                      : processingState.phase === 'fingerprinting'
                      ? 'bg-blue-100 text-blue-800 animate-pulse'
                      : 'bg-gray-100 text-gray-600'
                  }`}>
                    {processingState.stepsCompleted.fingerprinting ? '✓' : '3'}
                  </div>
                  <div className="ml-3">
                    <h4 className="text-sm font-medium text-gray-900">Fingerprinting</h4>
                    <p className="text-xs text-gray-500">Extract and process content</p>
                  </div>
                </div>
                {processingState.stepsCompleted.fingerprinting && (
                  <span className="text-sm text-green-600 font-medium">
                    {processingState.progress.processedPages} pages processed
                  </span>
                )}
              </div>
              
              {processingState.stepsCompleted.fingerprinting && (
                <div className="mt-3">
                  <div className="text-sm text-gray-600 mb-2">
                    Processed {processingState.progress.processedPages} pages
                  </div>
                </div>
              )}
            </div>

            {/* Step 4: Extraction */}
            <div className="mb-6 p-4 border rounded-lg">
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center">
                  <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium ${
                    processingState.stepsCompleted.extraction 
                      ? 'bg-green-100 text-green-800' 
                      : processingState.phase === 'extracting'
                      ? 'bg-blue-100 text-blue-800 animate-pulse'
                      : 'bg-gray-100 text-gray-600'
                  }`}>
                    {processingState.stepsCompleted.extraction ? '✓' : '4'}
                  </div>
                  <div className="ml-3">
                    <h4 className="text-sm font-medium text-gray-900">Extraction</h4>
                    <p className="text-xs text-gray-500">Extract structured data</p>
                  </div>
                </div>
                {processingState.stepsCompleted.extraction && (
                  <span className="text-sm text-green-600 font-medium">
                    {processingState.progress.extractedPages} pages extracted
                  </span>
                )}
              </div>
              
              {processingState.stepsCompleted.extraction && (
                <div className="mt-3">
                  <div className="text-sm text-gray-600 mb-2">
                    Extracted {processingState.progress.extractedPages} pages
                  </div>
                  
                  {/* Show extracted companies if any */}
                  {processingState.extractedCompanies.length > 0 && (
                    <div className="mt-4 p-3 bg-blue-50 border border-blue-200 rounded-lg">
                      <h5 className="text-sm font-medium text-blue-900 mb-2">
                        Extracted Companies ({processingState.extractedCompanies.length})
                      </h5>
                      <div className="space-y-2 max-h-40 overflow-y-auto">
                        {processingState.extractedCompanies.map((company, index) => (
                          <div key={company.id || index} className="text-xs text-blue-800 bg-white p-2 rounded border">
                            <div className="font-medium">{company.name}</div>
                            {company.description && (
                              <div className="text-gray-600 mt-1 line-clamp-2">{company.description}</div>
                            )}
                            {company.website && (
                              <div className="text-blue-600 mt-1">
                                <a href={company.website} target="_blank" rel="noopener noreferrer" className="hover:underline">
                                  {company.website}
                                </a>
                              </div>
                            )}
                            {company.confidence_score && (
                              <div className="text-gray-500 mt-1">
                                Confidence: {(company.confidence_score * 100).toFixed(1)}%
                              </div>
                            )}
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>

            {/* Action Buttons */}
            <div className="flex space-x-3">
              {(processingState.phase === 'scoring' || processingState.phase === 'discovery_complete') && !processingState.stepsCompleted.scoring && (
                <button
                  onClick={handleStartScoring}
                  disabled={isAnalyzing}
                  className="inline-flex items-center px-4 py-2 bg-purple-600 text-white text-sm font-medium rounded-md hover:bg-purple-700 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:ring-offset-2 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {isAnalyzing ? (
                    <>
                      <svg className="w-4 h-4 mr-2 animate-spin" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                      </svg>
                      Starting AI Scoring...
                    </>
                  ) : (
                    'Start AI Scoring'
                  )}
                </button>
              )}

              {(processingState.phase === 'scoring' || processingState.phase === 'discovery_complete') && processingState.stepsCompleted.scoring && !processingState.stepsCompleted.fingerprinting && (
                <button
                  onClick={handleStartFingerprinting}
                  disabled={isAnalyzing}
                  className="inline-flex items-center px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {isAnalyzing ? (
                    <>
                      <svg className="w-4 h-4 mr-2 animate-spin" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                      </svg>
                      Starting Fingerprinting...
                    </>
                  ) : (
                    'Start Fingerprinting'
                  )}
                </button>
              )}

              {processingState.phase === 'extracting' && !processingState.stepsCompleted.extraction && (
                <div className="flex space-x-2">
                  <button
                    onClick={handleStartExtraction}
                    disabled={isAnalyzing}
                    className="inline-flex items-center px-4 py-2 bg-green-600 text-white text-sm font-medium rounded-md hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-green-500 focus:ring-offset-2 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {isAnalyzing ? (
                      <>
                        <svg className="w-4 h-4 mr-2 animate-spin" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                        </svg>
                        Starting Extraction...
                      </>
                    ) : (
                      'Start Extraction'
                    )}
                  </button>
                  
                  <button
                    onClick={async () => {
                      if (!processingState.extractionSessionId) return;
                      try {
                        const status = await getExtractionStatus(processingState.extractionSessionId);
                        if (status.status === 'completed') {
                          // Fetch companies for this competitor
                          let extractedCompaniesData: any[] = [];
                          try {
                            const allCompanies = await companies();
                            extractedCompaniesData = allCompanies.filter(company => 
                              company.name.toLowerCase().includes(processingState.competitorName?.toLowerCase() || '') ||
                              company.aliases?.some((alias: string) => 
                                alias.toLowerCase().includes(processingState.competitorName?.toLowerCase() || '')
                              )
                            );
                          } catch (error) {
                            console.error('Failed to fetch companies:', error);
                          }
                          
                          setProcessingState(prev => ({
                            ...prev,
                            phase: 'completed',
                            stepsCompleted: { ...prev.stepsCompleted, extraction: true },
                            progress: {
                              ...prev.progress,
                              entitiesFound: {
                                companies: status.stats?.companies_found || 0,
                                products: status.stats?.products_found || 0,
                                capabilities: status.stats?.capabilities_found || 0,
                                documents: status.stats?.documents_found || 0,
                                signals: status.stats?.signals_found || 0
                              }
                            },
                            extractedCompanies: extractedCompaniesData
                          }));
                          setIsAnalyzing(false);
                        }
                      } catch (error) {
                        console.error('Failed to check extraction status:', error);
                      }
                    }}
                    className="inline-flex items-center px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 transition-colors"
                  >
                    <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                    </svg>
                    Check Status
                  </button>
                </div>
              )}

              {(processingState.phase === 'discovering' || processingState.phase === 'fingerprinting' || processingState.phase === 'extracting') && (
                <button
                  onClick={handleStop}
                  className="inline-flex items-center px-4 py-2 bg-red-600 text-white text-sm font-medium rounded-md hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-red-500 focus:ring-offset-2 transition-colors"
                >
                  <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 6h12v12H6z" />
                  </svg>
                  Stop Analysis
                </button>
              )}
            </div>
          </div>

          {/* Real-time Metrics */}
          {processingState.phase === 'extracting' && (
            <div className="mt-4 grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
              <div className="text-center">
                <div className="text-gray-500">Speed</div>
                <div className="font-semibold">{processingState.metrics.qps.toFixed(1)} pages/min</div>
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
                  <span className="text-green-700">Documents:</span>
                  <span className="font-semibold text-green-800">{processingState.progress.entitiesFound.documents}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-green-700">Signals:</span>
                  <span className="font-semibold text-green-800">{processingState.progress.entitiesFound.signals}</span>
                </div>
              </div>
              <div className="mt-3 text-sm text-green-700">
                <p>✅ Analysis complete! The competitor has been successfully added to your database.</p>
                <div className="mt-3 flex space-x-3">
                  <button
                    onClick={() => navigate('/companies')}
                    className="px-4 py-2 bg-green-600 text-white text-sm font-medium rounded-md hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-green-500 focus:ring-offset-2"
                  >
                    View Companies
                  </button>
                  <button
                    onClick={() => {
                      setProcessingState({
                        phase: 'idle',
                        crawlSessionId: null,
                        fingerprintSessionId: null,
                        extractionSessionId: null,
                        stepsCompleted: {
                          discovery: false,
                          scoring: false,
                          fingerprinting: false,
                          extraction: false
                        },
                        progress: {
                          discoveredPages: 0,
                          processedPages: 0,
                          extractedPages: 0,
                          totalPages: 0,
                          skippedPages: 0,
                          entitiesFound: {
                            companies: 0,
                            products: 0,
                            capabilities: 0,
                            documents: 0,
                            signals: 0
                          }
                        },
                        metrics: {
                          qps: 0,
                          etaSeconds: null,
                          cacheHits: 0,
                          retries: 0
                        },
                        extractedCompanies: [],
                        discoveredPages: [],
                        skippedUrls: [],
                        sitemapUrls: [],
                        filteredSitemapUrls: [],
                        sitemapFilteredCount: 0,
                        sitemapProcessedCount: 0,
                        competitorName: '',
                        error: null
                      });
                      setUrl('');
                      setValidationResult(null);
                      setIsAnalyzing(false);
                    }}
                    className="px-4 py-2 bg-gray-600 text-white text-sm font-medium rounded-md hover:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-gray-500 focus:ring-offset-2"
                  >
                    Add Another
                  </button>
                </div>
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

      {/* Debug: Discovered Pages with Scores */}
      {processingState.discoveredPages.length > 0 && (
        <div className="bg-white rounded-lg border border-gray-200 p-6 mb-6">
          <div className="mb-4 flex items-center justify-between">
            <div>
              <h3 className="text-lg font-semibold text-gray-900">Discovered Pages (Debug View)</h3>
              <p className="text-sm text-gray-600 mt-1">
                Showing {processingState.discoveredPages.length} pages with their AI/Rules-based scores and classifications
              </p>
            </div>
            <button
              onClick={() => setShowDebugView(!showDebugView)}
              className="px-3 py-1 text-sm bg-gray-100 text-gray-700 rounded-md hover:bg-gray-200 transition-colors"
            >
              {showDebugView ? 'Hide Details' : 'Show Details'}
            </button>
          </div>

          {showDebugView && (
            <div className="space-y-3 max-h-96 overflow-y-auto">
              {processingState.discoveredPages
                .sort((a, b) => b.score - a.score) // Sort by score descending
                .map((page, index) => (
                <div key={index} className="border border-gray-200 rounded-lg p-4 hover:bg-gray-50">
                  <div className="flex items-start justify-between">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center space-x-2 mb-2">
                        <span className="text-sm font-medium text-gray-900 truncate">
                          {page.url}
                        </span>
                        <span className={`px-2 py-1 text-xs font-medium rounded-full ${
                          page.scoring_method === 'ai' 
                            ? 'bg-blue-100 text-blue-800' 
                            : 'bg-gray-100 text-gray-800'
                        }`}>
                          {page.scoring_method.toUpperCase()}
                        </span>
                      </div>
                      
                      <div className="flex items-center space-x-4 text-sm text-gray-600">
                        <div className="flex items-center space-x-1">
                          <span className="font-medium">Primary Score:</span>
                          <span className={`font-bold ${
                            page.score >= 0.8 ? 'text-green-600' :
                            page.score >= 0.6 ? 'text-yellow-600' :
                            page.score >= 0.4 ? 'text-orange-600' :
                            'text-red-600'
                          }`}>
                            {page.score.toFixed(3)}
                          </span>
                          <span className="text-xs text-gray-500">({page.scoring_method})</span>
                        </div>
                        
                        <div className="flex items-center space-x-1">
                          <span className="font-medium">Category:</span>
                          <span className="px-2 py-1 bg-gray-100 text-gray-700 rounded text-xs">
                            {page.primary_category}
                          </span>
                        </div>

                        {page.ai_confidence && (
                          <div className="flex items-center space-x-1">
                            <span className="font-medium">AI Confidence:</span>
                            <span className="text-blue-600 font-medium">
                              {(page.ai_confidence * 100).toFixed(1)}%
                            </span>
                          </div>
                        )}
                      </div>

                      {/* Dual Scoring Debug Information */}
                      <div className="mt-2 p-2 bg-gray-50 rounded text-xs">
                        <div className="font-medium text-gray-700 mb-1">Dual Scoring Debug:</div>
                        <div className="grid grid-cols-2 gap-2">
                          <div>
                            <span className="font-medium text-blue-600">AI Score:</span>
                            <span className="ml-1">
                              {page.ai_score !== null && page.ai_score !== undefined 
                                ? page.ai_score.toFixed(3) 
                                : 'N/A'
                              }
                            </span>
                            {page.ai_category && (
                              <span className="ml-1 text-gray-500">({page.ai_category})</span>
                            )}
                          </div>
                          <div>
                            <span className="font-medium text-gray-600">Rules Score:</span>
                            <span className="ml-1">
                              {page.rules_score !== null && page.rules_score !== undefined 
                                ? page.rules_score.toFixed(3) 
                                : 'N/A'
                              }
                            </span>
                            {page.rules_category && (
                              <span className="ml-1 text-gray-500">({page.rules_category})</span>
                            )}
                          </div>
                        </div>
                        
                        {page.ai_success !== undefined && (
                          <div className="mt-1">
                            <span className="font-medium">AI Success:</span>
                            <span className={`ml-1 ${page.ai_success ? 'text-green-600' : 'text-red-600'}`}>
                              {page.ai_success ? 'Yes' : 'No'}
                            </span>
                            {!page.ai_success && page.ai_scoring_reason && (
                              <div className="mt-1 text-xs text-red-600">
                                <span className="font-medium">Reason:</span> {page.ai_scoring_reason}
                              </div>
                            )}
                            {!page.ai_success && page.ai_error && (
                              <div className="mt-1 text-xs text-red-600">
                                <span className="font-medium">Error:</span> {page.ai_error}
                              </div>
                            )}
                          </div>
                        )}

                        {/* AI Scoring Reason - Show even when AI success is undefined */}
                        {page.ai_scoring_reason && page.ai_success === undefined && (
                          <div className="mt-1 text-xs text-gray-600">
                            <span className="font-medium">AI Status:</span> {page.ai_scoring_reason}
                          </div>
                        )}
                      </div>

                      {page.secondary_categories.length > 0 && (
                        <div className="mt-2">
                          <span className="text-xs text-gray-500">Secondary: </span>
                          {page.secondary_categories.map((cat, i) => (
                            <span key={i} className="text-xs bg-gray-100 text-gray-600 px-1.5 py-0.5 rounded mr-1">
                              {cat}
                            </span>
                          ))}
                        </div>
                      )}

                      {page.signals.length > 0 && (
                        <div className="mt-2">
                          <span className="text-xs text-gray-500">Signals: </span>
                          {page.signals.map((signal, i) => (
                            <span key={i} className="text-xs bg-blue-100 text-blue-700 px-1.5 py-0.5 rounded mr-1">
                              {signal}
                            </span>
                          ))}
                        </div>
                      )}

                      {page.ai_reasoning && (
                        <div className="mt-2 p-2 bg-blue-50 rounded text-xs text-blue-800">
                          <span className="font-medium">AI Reasoning:</span> {page.ai_reasoning}
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* Summary Statistics - Always Visible */}
          <div className="mt-4 pt-4 border-t border-gray-200">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
              <div className="text-center">
                <div className="text-gray-500">AI Scored</div>
                <div className="font-semibold text-blue-600">
                  {processingState.discoveredPages.filter(p => p.scoring_method === 'ai').length}
                </div>
              </div>
              <div className="text-center">
                <div className="text-gray-500">Rules Scored</div>
                <div className="font-semibold text-gray-600">
                  {processingState.discoveredPages.filter(p => p.scoring_method === 'rules').length}
                </div>
              </div>
              <div className="text-center">
                <div className="text-gray-500">Avg Score</div>
                <div className="font-semibold">
                  {(processingState.discoveredPages.reduce((sum, p) => sum + p.score, 0) / processingState.discoveredPages.length).toFixed(3)}
                </div>
              </div>
              <div className="text-center">
                <div className="text-gray-500">High Value</div>
                <div className="font-semibold text-green-600">
                  {processingState.discoveredPages.filter(p => p.score >= 0.5).length}
                </div>
              </div>
            </div>
            
            {!showDebugView && (
              <div className="mt-3 text-center">
                <p className="text-xs text-gray-500">
                  Click "Show Details" to see individual page scores, categories, and AI reasoning
                </p>
              </div>
            )}
          </div>
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
