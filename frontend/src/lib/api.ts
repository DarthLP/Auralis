import { z } from 'zod';
import {
  Company,
  CompanySummary,
  Product,
  ProductCapability,
  Capability,
  Signal,
  Release,
  Source,
} from '@schema/types';
import {
  zCompany,
  zCompanySummary,
  zProduct,
  zProductCapability,
  zCapability,
  zSignal,
  zRelease,
  zSource,
} from '@schema/zod';

/**
 * Generic API fetch function with schema validation
 * @param path - API endpoint path
 * @param schema - Zod schema for validation
 * @returns Promise<T> - Validated data of type T
 */
export async function fetchAs<T>(path: string, schema: z.ZodType<T>): Promise<T> {
  const baseUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
  const url = `${baseUrl}${path}`;
  
  try {
    const response = await fetch(url);
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    const json = await response.json();
    return schema.parse(json);
  } catch (error) {
    console.error(`API fetch error for ${path}:`, error);
    throw error;
  }
}

/**
 * Fetch all companies
 * @returns Promise<Company[]> - Array of companies
 */
export async function companies(): Promise<Company[]> {
  return fetchAs('/api/companies', z.array(zCompany));
}

/**
 * Fetch a specific company by ID
 * @param id - Company ID
 * @returns Promise<Company> - Company data
 */
export async function company(id: string): Promise<Company> {
  return fetchAs(`/api/companies/${id}`, zCompany);
}

/**
 * Fetch company summaries for a specific company
 * @param companyId - Company ID
 * @returns Promise<CompanySummary[]> - Array of company summaries
 */
export async function companySummaries(companyId: string): Promise<CompanySummary[]> {
  return fetchAs(`/api/companies/${companyId}/summaries`, z.array(zCompanySummary));
}

/**
 * Fetch products for a specific company
 * @param companyId - Company ID
 * @returns Promise<Product[]> - Array of products
 */
export async function productsByCompany(companyId: string): Promise<Product[]> {
  return fetchAs(`/api/companies/${companyId}/products`, z.array(zProduct));
}

/**
 * Fetch a specific product by ID
 * @param productId - Product ID
 * @returns Promise<Product> - Product data
 */
export async function product(productId: string): Promise<Product> {
  return fetchAs(`/api/products/${productId}`, zProduct);
}

/**
 * Fetch product capabilities for a specific product
 * @param productId - Product ID
 * @returns Promise<ProductCapability[]> - Array of product capabilities
 */
export async function productCapabilities(productId: string): Promise<ProductCapability[]> {
  return fetchAs(`/api/products/${productId}/capabilities`, z.array(zProductCapability));
}

/**
 * Fetch all capabilities
 * @returns Promise<Capability[]> - Array of capabilities
 */
export async function capabilities(): Promise<Capability[]> {
  return fetchAs('/api/capabilities', z.array(zCapability));
}

/**
 * Fetch signals with optional query string
 * @param qs - Query string parameters (e.g., "?type=news&impact=1")
 * @returns Promise<Signal[]> - Array of signals
 */
export async function signals(qs: string = ''): Promise<Signal[]> {
  return fetchAs(`/api/signals${qs}`, z.array(zSignal));
}

/**
 * Fetch releases with optional query string
 * @param qs - Query string parameters (e.g., "?company_id=123&product_id=456")
 * @returns Promise<Release[]> - Array of releases
 */
export async function releases(qs: string = ''): Promise<Release[]> {
  return fetchAs(`/api/releases${qs}`, z.array(zRelease));
}

/**
 * Fetch a specific source by ID
 * @param id - Source ID
 * @returns Promise<Source> - Source data
 */
export async function source(id: string): Promise<Source> {
  return fetchAs(`/api/sources/${id}`, zSource);
}

// ===== CRAWLING & EXTRACTION API =====

export interface CrawlRequest {
  url: string;
}

export interface CrawlResponse {
  input_url: string;
  base_domain: string;
  limits: Record<string, any>;
  pages: Array<{
    url: string;
    status: number;
    primary_category: string;
    secondary_categories: string[];
    score: number;
    signals: string[];
    content_hash: string;
    size_bytes: number;
    depth: number;
  }>;
  top_by_category: Record<string, string[]>;
  warnings: string[];
  crawl_session_id: number;
  pages_saved_to_db: number;
}

export interface FingerprintRequest {
  crawl_session_id: number;
  competitor: string;
}

export interface FingerprintResponse {
  fingerprint_session_id: number;
  crawl_session_id: number;
  competitor: string;
  started_at: string;
  completed_at: string | null;
  total_processed: number;
  total_errors: number;
  fingerprints: Array<{
    url: string;
    key_url: string;
    page_type: string;
    content_hash: string;
    normalized_text_len: number;
    extracted_text: string | null;
    low_text_pdf: boolean;
    needs_render: boolean;
    meta: {
      status: number | null;
      content_type: string | null;
      content_length: number;
      elapsed_ms: number;
      notes: string | null;
    };
  }>;
}

export interface ExtractionRequest {
  fingerprint_session_id: number;
  competitor: string;
  schema_version?: string;
  force_reprocess?: boolean;
}

export interface ExtractionResponse {
  extraction_session_id: number;
  fingerprint_session_id: number;
  competitor: string;
  schema_version: string;
  started_at: string;
  completed_at: string | null;
  status: 'running' | 'completed' | 'failed' | 'degraded';
  stats: {
    total_pages: number;
    processed_pages: number;
    skipped_pages: number;
    failed_pages: number;
    cache_hits: number;
    total_retries: number;
    companies_found: number;
    products_found: number;
    capabilities_found: number;
    releases_found: number;
    documents_found: number;
    signals_found: number;
    changes_detected: number;
  };
  error_summary?: Record<string, string>;
}

// Crawling API functions
export async function startCrawlDiscovery(url: string): Promise<CrawlResponse> {
  const baseUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
  const response = await fetch(`${baseUrl}/api/crawl/discover`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ url })
  });
  
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail?.message || `Crawl discovery failed: ${response.status}`);
  }
  
  return response.json();
}

export async function startFingerprinting(crawlSessionId: number, competitor: string): Promise<FingerprintResponse> {
  const baseUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
  const response = await fetch(`${baseUrl}/api/crawl/fingerprint`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ 
      crawl_session_id: crawlSessionId, 
      competitor 
    })
  });
  
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail?.message || `Fingerprinting failed: ${response.status}`);
  }
  
  return response.json();
}

// Stop crawl functions
export async function stopCrawl(crawlSessionId: number): Promise<{ success: boolean; message: string }> {
  const baseUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
  const response = await fetch(`${baseUrl}/api/crawl/stop`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ crawl_session_id: crawlSessionId })
  });
  
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.message || `Stop crawl failed: ${response.status}`);
  }
  
  return response.json();
}

export async function getActiveCrawlSessions(): Promise<{ active_sessions: number[] }> {
  const baseUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
  const response = await fetch(`${baseUrl}/api/crawl/active-sessions`);
  
  if (!response.ok) {
    throw new Error(`Get active sessions failed: ${response.status}`);
  }
  
  return response.json();
}

// Extraction API functions
export async function startExtraction(request: ExtractionRequest): Promise<ExtractionResponse> {
  const baseUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
  const response = await fetch(`${baseUrl}/api/extract/run`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(request)
  });
  
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || `Extraction failed: ${response.status}`);
  }
  
  return response.json();
}

export async function getExtractionStatus(sessionId: number): Promise<ExtractionResponse> {
  const baseUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
  const response = await fetch(`${baseUrl}/api/extract/status/${sessionId}`);
  
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || `Failed to get extraction status: ${response.status}`);
  }
  
  return response.json();
}

// Real-time progress tracking with Server-Sent Events
export class ExtractionProgressTracker {
  private eventSource: EventSource | null = null;
  private callbacks: Map<string, Function[]> = new Map();

  subscribe(sessionId: number) {
    const baseUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
    this.eventSource = new EventSource(`${baseUrl}/api/extract/stream/${sessionId}`);
    
    this.eventSource.addEventListener('session_started', (event) => {
      this.emit('session_started', JSON.parse(event.data));
    });
    
    this.eventSource.addEventListener('page_queued', (event) => {
      this.emit('page_queued', JSON.parse(event.data));
    });
    
    this.eventSource.addEventListener('page_started', (event) => {
      this.emit('page_started', JSON.parse(event.data));
    });
    
    this.eventSource.addEventListener('page_extracted', (event) => {
      this.emit('page_extracted', JSON.parse(event.data));
    });
    
    this.eventSource.addEventListener('page_merged', (event) => {
      this.emit('page_merged', JSON.parse(event.data));
    });
    
    this.eventSource.addEventListener('page_failed', (event) => {
      this.emit('page_failed', JSON.parse(event.data));
    });
    
    this.eventSource.addEventListener('metrics', (event) => {
      this.emit('metrics', JSON.parse(event.data));
    });
    
    this.eventSource.addEventListener('session_completed', (event) => {
      this.emit('session_completed', JSON.parse(event.data));
      this.close();
    });
    
    this.eventSource.addEventListener('session_finished', (event) => {
      this.emit('session_finished', JSON.parse(event.data));
      this.close();
    });
    
    this.eventSource.addEventListener('error', (event: MessageEvent) => {
      this.emit('error', JSON.parse(event.data));
    });
    
    this.eventSource.onerror = (error) => {
      console.error('SSE connection error:', error);
      this.emit('error', { message: 'Connection lost' });
    };
  }

  on(event: string, callback: Function) {
    if (!this.callbacks.has(event)) {
      this.callbacks.set(event, []);
    }
    this.callbacks.get(event)!.push(callback);
  }

  private emit(event: string, data: any) {
    const callbacks = this.callbacks.get(event) || [];
    callbacks.forEach(callback => callback(data));
  }

  close() {
    if (this.eventSource) {
      this.eventSource.close();
      this.eventSource = null;
    }
  }
}

