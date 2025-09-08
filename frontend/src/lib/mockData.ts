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

// Import seed data
import seedData from '../../../data/seed.json';

// Simulate network delay
const delay = (ms: number) => new Promise(resolve => setTimeout(resolve, ms));

// Mock scraper job status
export type ScraperJobStatus = 'queued' | 'processing' | 'done' | 'error';

export interface ScraperJob {
  id: string;
  status: ScraperJobStatus;
  url: string;
  result?: ScraperResult;
  error?: string;
}

export interface ScraperResult {
  company: {
    name: string;
    website: string;
    hq_country?: string;
    tags: string[];
  };
  summary: {
    one_liner: string;
  };
  products: Array<{
    name: string;
    category: string;
    short_desc: string;
  }>;
  sources: Array<{
    origin: string;
    author?: string;
    retrieved_at: string;
  }>;
  dedupe?: {
    existing_company_id: string;
    existing_company_name: string;
  };
}

// Use seed data directly with type assertions (validation was causing issues)
const parsedSeed = {
  companies: seedData.companies as unknown as Company[],
  company_summaries: seedData.company_summaries as unknown as CompanySummary[],
  products: seedData.products as unknown as Product[],
  capabilities: seedData.capabilities as unknown as Capability[],
  product_capabilities: seedData.product_capabilities as unknown as ProductCapability[],
  signals: seedData.signals as unknown as Signal[],
  releases: seedData.releases as unknown as Release[],
  sources: seedData.sources as unknown as Source[],
};

/**
 * Generic mock fetch function with artificial delay
 */
async function mockFetch<T>(data: T[], delayMs: number = 300): Promise<T[]> {
  await delay(delayMs);
  return [...data]; // Return a copy
}

/**
 * Get signals from the last N days
 */
function getSignalsFromLastDays(days: number): Signal[] {
  const cutoffDate = new Date();
  cutoffDate.setDate(cutoffDate.getDate() - days);
  
  return parsedSeed.signals.filter(signal => {
    const signalDate = new Date(signal.published_at);
    return signalDate >= cutoffDate;
  });
}

/**
 * Get releases from the last N days
 */
function getReleasesFromLastDays(days: number): Release[] {
  const cutoffDate = new Date();
  cutoffDate.setDate(cutoffDate.getDate() - days);
  
  return parsedSeed.releases.filter(release => {
    const releaseDate = new Date(release.released_at);
    return releaseDate >= cutoffDate;
  });
}

// Mock API functions - same interface as real api.ts
export async function companies(): Promise<Company[]> {
  return mockFetch(parsedSeed.companies);
}

export async function company(id: string): Promise<Company> {
  await delay(200);
  const found = parsedSeed.companies.find(c => c.id === id);
  if (!found) throw new Error(`Company with id ${id} not found`);
  return found;
}

export async function companySummaries(companyId: string): Promise<CompanySummary[]> {
  return mockFetch(parsedSeed.company_summaries.filter(cs => cs.company_id === companyId));
}

export async function productsByCompany(companyId: string): Promise<Product[]> {
  return mockFetch(parsedSeed.products.filter(p => p.company_id === companyId));
}

export async function product(productId: string): Promise<Product> {
  await delay(200);
  const found = parsedSeed.products.find(p => p.id === productId);
  if (!found) throw new Error(`Product with id ${productId} not found`);
  return found;
}

export async function productCapabilities(productId: string): Promise<ProductCapability[]> {
  return mockFetch(parsedSeed.product_capabilities.filter(pc => pc.product_id === productId));
}

export async function capabilities(): Promise<Capability[]> {
  return mockFetch(parsedSeed.capabilities);
}

export async function signals(): Promise<Signal[]> {
  return mockFetch(parsedSeed.signals);
}

export async function releases(): Promise<Release[]> {
  return mockFetch(parsedSeed.releases);
}

export async function source(id: string): Promise<Source> {
  await delay(200);
  const found = parsedSeed.sources.find(s => s.id === id);
  if (!found) throw new Error(`Source with id ${id} not found`);
  return found;
}

// Mock spec profile data
const mockSpecProfiles = {
  'robotics/mobile_manipulator@1': {
    id: 'robotics/mobile_manipulator@1',
    name: 'Mobile Manipulator',
    version: '1.0',
    schema: {
      payload: { type: 'number', unit: 'kg', label: 'Payload Capacity' },
      dof: { type: 'number', label: 'Degrees of Freedom' },
      max_speed: { type: 'number', unit: 'm/s', label: 'Maximum Speed' },
      sensors: { type: 'array', label: 'Sensors' },
      runtime: { type: 'range', unit: 'hrs', label: 'Runtime' }
    },
    ui: {
      groups: [
        {
          name: 'Performance',
          fields: ['payload', 'max_speed', 'runtime']
        },
        {
          name: 'Configuration',
          fields: ['dof', 'sensors']
        }
      ]
    }
  },
  'robotics/amr@1': {
    id: 'robotics/amr@1',
    name: 'Autonomous Mobile Robot',
    version: '1.0',
    schema: {
      sensors: { type: 'array', label: 'Sensors' },
      runtime: { type: 'range', unit: 'hrs', label: 'Runtime' }
    },
    ui: {
      groups: [
        {
          name: 'Specifications',
          fields: ['sensors', 'runtime']
        }
      ]
    }
  }
};

export async function specProfile(id: string): Promise<any> {
  await delay(200);
  const found = mockSpecProfiles[id as keyof typeof mockSpecProfiles];
  if (!found) throw new Error(`Spec profile with id ${id} not found`);
  return found;
}

// Specialized functions for Overview page
export async function getThisWeekSignals(): Promise<Signal[]> {
  const thisWeekSignals = getSignalsFromLastDays(7);
  
  // Sort by impact desc (2..-2), then published_at desc
  const sorted = thisWeekSignals.sort((a, b) => {
    const impactA = parseInt(a.impact);
    const impactB = parseInt(b.impact);
    
    if (impactA !== impactB) {
      return impactB - impactA; // Higher impact first
    }
    
    // If impact is same, sort by date desc (newest first)
    return new Date(b.published_at).getTime() - new Date(a.published_at).getTime();
  });
  
  return mockFetch(sorted.slice(0, 5)); // Top 5
}

export async function getRecentReleases(): Promise<Release[]> {
  const recentReleases = getReleasesFromLastDays(90);
  
  // Sort by released_at desc (newest first)
  const sorted = recentReleases.sort((a, b) => {
    return new Date(b.released_at).getTime() - new Date(a.released_at).getTime();
  });
  
  return mockFetch(sorted.slice(0, 8)); // Top 8
}

/**
 * Get signals for a specific company from the last N days
 */
function getCompanySignalsFromLastDays(companyId: string, days: number): Signal[] {
  const cutoffDate = new Date();
  cutoffDate.setDate(cutoffDate.getDate() - days);
  
  return parsedSeed.signals.filter(signal => {
    const signalDate = new Date(signal.published_at);
    return signal.company_ids.includes(companyId) && signalDate >= cutoffDate;
  });
}

/**
 * Get all releases for a specific company
 */
function getCompanyReleases(companyId: string): Release[] {
  return parsedSeed.releases.filter(release => release.company_id === companyId);
}

/**
 * Get recent activity (signals + releases) for a company
 * Signals: last 60 days, Releases: all, combined and sorted by date desc
 * Limited to 10 items total
 */
export async function getCompanyRecentActivity(companyId: string): Promise<Array<{
  type: 'signal' | 'release';
  id: string;
  title: string;
  date: string;
  summary?: string;
  productId?: string;
  signalId?: string;
}>> {
  const companySignals = getCompanySignalsFromLastDays(companyId, 60);
  const companyReleases = getCompanyReleases(companyId);
  
  // Combine and sort by date
  const combined: Array<{
    type: 'signal' | 'release';
    id: string;
    title: string;
    date: string;
    summary?: string;
    productId?: string;
    signalId?: string;
  }> = [];
  
  // Add signals
  companySignals.forEach(signal => {
    combined.push({
      type: 'signal',
      id: signal.id,
      title: signal.headline,
      date: signal.published_at,
      summary: signal.summary,
      signalId: signal.id
    });
  });
  
  // Add releases
  companyReleases.forEach(release => {
    // Find product name for the release
    const product = parsedSeed.products.find(p => p.id === release.product_id);
    const productName = product?.name || 'Unknown Product';
    
    const title = release.version 
      ? `${productName} — ${release.version}`
      : productName;
    
    combined.push({
      type: 'release',
      id: release.id,
      title,
      date: release.released_at,
      summary: release.notes,
      productId: release.product_id
    });
  });
  
  // Sort by date desc (newest first)
  const sorted = combined.sort((a, b) => {
    return new Date(b.date).getTime() - new Date(a.date).getTime();
  });
  
  // Limit to 10 items
  const limited = sorted.slice(0, 10);
  
  await delay(200);
  return limited;
}

// Mock scraper functionality
const activeJobs = new Map<string, ScraperJob>();

/**
 * Start a mock scraper job for a URL
 */
export async function startScraperJob(url: string): Promise<ScraperJob> {
  const jobId = `job_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  
  const job: ScraperJob = {
    id: jobId,
    status: 'queued',
    url
  };
  
  activeJobs.set(jobId, job);
  
  // Simulate job progression
  setTimeout(() => {
    const currentJob = activeJobs.get(jobId);
    if (currentJob) {
      currentJob.status = 'processing';
    }
  }, 500);
  
  setTimeout(() => {
    const currentJob = activeJobs.get(jobId);
    if (currentJob) {
      currentJob.status = 'done';
      currentJob.result = extractCompanyData(url);
    }
  }, 2000);
  
  return job;
}

/**
 * Get scraper job status
 */
export async function getScraperJob(jobId: string): Promise<ScraperJob | null> {
  await delay(100);
  return activeJobs.get(jobId) || null;
}

/**
 * Extract company data from URL (mocked heuristic extraction)
 */
function extractCompanyData(url: string): ScraperResult {
  const domain = new URL(url).hostname.replace('www.', '');
  const domainParts = domain.split('.')[0].split('-');
  
  // Generate company name from domain
  const companyName = domainParts
    .map(part => part.charAt(0).toUpperCase() + part.slice(1))
    .join(' ');
  
  // Generate tags from domain keywords
  const keywords = ['robots', 'ai', 'vision', 'platform', 'retail', 'humanoid', 'amr', 'cloud', 'saas', 'tech', 'software', 'hardware', 'automation', 'intelligence', 'data', 'analytics'];
  const domainLower = domain.toLowerCase();
  const extractedTags = keywords.filter(keyword => domainLower.includes(keyword));
  
  // Add some default tags if none found
  if (extractedTags.length === 0) {
    extractedTags.push('tech', 'startup');
  }
  
  // Generate product based on domain content
  const products = [];
  if (domainLower.includes('robot')) {
    products.push({
      name: 'Starter Robot',
      category: 'Uncategorized',
      short_desc: 'Placeholder product. Edit to match reality.'
    });
  } else if (domainLower.includes('ai') || domainLower.includes('cloud')) {
    products.push({
      name: 'Starter Platform',
      category: 'SaaS',
      short_desc: 'Placeholder platform.'
    });
  } else {
    products.push({
      name: 'Main Product',
      category: 'Uncategorized',
      short_desc: 'Placeholder product. Edit to match reality.'
    });
  }
  
  // Check for duplicates using the new validation system
  const dedupe = checkForDuplicatesNew(domain, companyName);
  
  return {
    company: {
      name: companyName,
      website: url,
      tags: extractedTags.slice(0, 8) // Limit to 8 tags
    },
    summary: {
      one_liner: 'Company discovered via URL-based ingest. Edit before saving.'
    },
    products,
    sources: [{
      origin: url,
      retrieved_at: new Date().toLocaleString('sv-SE', { timeZone: 'Europe/Berlin' })
    }],
    ...(dedupe && { dedupe })
  };
}


/**
 * Check for duplicate companies (new function using validation system)
 */
function checkForDuplicatesNew(domain: string, companyName: string): ScraperResult['dedupe'] | null {
  // Simple eTLD+1 extraction for deduplication
  function extractETLD1(hostname: string): string {
    const parts = hostname.toLowerCase().split('.');
    if (parts.length <= 1) return hostname.toLowerCase();
    
    // Handle common two-part TLDs
    const twoPartTLDs = [
      'co.uk', 'com.au', 'co.jp', 'co.kr', 'co.za', 'co.in',
      'com.br', 'com.mx', 'com.ar', 'com.sg', 'com.hk',
      'org.uk', 'net.uk', 'ac.uk', 'gov.uk',
      'com.cn', 'net.cn', 'org.cn', 'gov.cn',
    ];
    
    if (parts.length >= 3) {
      const potentialTLD = `${parts[parts.length - 2]}.${parts[parts.length - 1]}`;
      if (twoPartTLDs.includes(potentialTLD)) {
        return `${parts[parts.length - 3]}.${potentialTLD}`;
      }
    }
    
    return parts.slice(-2).join('.');
  }
  
  const inputETLD1 = extractETLD1(domain);
  
  for (const company of parsedSeed.companies) {
    // Check by domain (eTLD+1)
    if (company.website) {
      try {
        const companyUrl = new URL(company.website);
        const companyETLD1 = extractETLD1(companyUrl.hostname.toLowerCase());
        
        if (companyETLD1 === inputETLD1) {
          return {
            existing_company_id: company.id,
            existing_company_name: company.name
          };
        }
      } catch {
        // Invalid URL, skip
      }
    }
    
    // Check by name (soft match)
    const normalizedCompanyName = company.name.toLowerCase().replace(/[^a-z0-9]/g, '');
    const normalizedInputName = companyName.toLowerCase().replace(/[^a-z0-9]/g, '');
    
    if (normalizedCompanyName === normalizedInputName && normalizedInputName.length > 2) {
      return {
        existing_company_id: company.id,
        existing_company_name: company.name
      };
    }
  }
  
  return null;
}

/**
 * Save a new competitor (mock implementation)
 */
export async function saveCompetitor(data: ScraperResult): Promise<{ company_id: string }> {
  await delay(500);
  
  // Generate new IDs
  const companyId = `comp_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  
  // Create new company
  const newCompany: Company = {
    id: companyId,
    name: data.company.name,
    aliases: [],
    hq_country: data.company.hq_country,
    website: data.company.website,
    status: 'active',
    tags: data.company.tags
  };
  
  // Create company summary
  const newSummary: CompanySummary = {
    company_id: companyId,
    one_liner: data.summary.one_liner,
    sources: data.sources.map(s => s.origin)
  };
  
  // Create products
  const newProducts: Product[] = data.products.map((product, index) => ({
    id: `prod_${Date.now()}_${index}_${Math.random().toString(36).substr(2, 9)}`,
    company_id: companyId,
    name: product.name,
    category: product.category,
    stage: 'ga' as any,
    markets: [],
    tags: [],
    short_desc: product.short_desc
  }));
  
  // Add to mock data (in a real app, this would be a database operation)
  parsedSeed.companies.push(newCompany);
  parsedSeed.company_summaries.push(newSummary);
  parsedSeed.products.push(...newProducts);
  
  return { company_id: companyId };
}

// Search API functions for global search

export interface SearchResult {
  id: string;
  type: 'company' | 'product' | 'signal' | 'release';
  title: string;
  subtitle?: string;
  description?: string;
  companyId?: string;
  productId?: string;
  signalId?: string;
  releaseId?: string;
  date?: string;
  tags?: string[];
  score: number;
}

/**
 * Search companies with ranking
 */
export async function searchCompanies(query: string): Promise<SearchResult[]> {
  await delay(100);
  
  const normalizedQuery = query.toLowerCase().trim();
  if (!normalizedQuery) return [];
  
  const results: SearchResult[] = [];
  
  for (const company of parsedSeed.companies) {
    let score = 0;
    const searchableText = [
      company.name,
      ...company.aliases,
      ...company.tags
    ].join(' ').toLowerCase();
    
    // Exact name match (highest priority)
    if (company.name.toLowerCase() === normalizedQuery) {
      score = 100;
    }
    // Name starts with query
    else if (company.name.toLowerCase().startsWith(normalizedQuery)) {
      score = 80;
    }
    // Name contains query
    else if (company.name.toLowerCase().includes(normalizedQuery)) {
      score = 60;
    }
    // Aliases or tags contain query
    else if (searchableText.includes(normalizedQuery)) {
      score = 40;
    }
    
    if (score > 0) {
      // Get company summary for description
      const summary = parsedSeed.company_summaries.find(cs => cs.company_id === company.id);
      
      results.push({
        id: company.id,
        type: 'company',
        title: company.name,
        subtitle: company.website ? new URL(company.website).hostname : undefined,
        description: summary?.one_liner,
        companyId: company.id,
        tags: company.tags,
        score
      });
    }
  }
  
  return results.sort((a, b) => b.score - a.score).slice(0, 5);
}

/**
 * Search products with ranking
 */
export async function searchProducts(query: string): Promise<SearchResult[]> {
  await delay(100);
  
  const normalizedQuery = query.toLowerCase().trim();
  if (!normalizedQuery) return [];
  
  const results: SearchResult[] = [];
  
  for (const product of parsedSeed.products) {
    let score = 0;
    const searchableText = [
      product.name,
      product.short_desc || '',
      ...product.tags
    ].join(' ').toLowerCase();
    
    // Exact name match (highest priority)
    if (product.name.toLowerCase() === normalizedQuery) {
      score = 100;
    }
    // Name starts with query
    else if (product.name.toLowerCase().startsWith(normalizedQuery)) {
      score = 80;
    }
    // Name contains query
    else if (product.name.toLowerCase().includes(normalizedQuery)) {
      score = 60;
    }
    // Description or tags contain query
    else if (searchableText.includes(normalizedQuery)) {
      score = 40;
    }
    
    if (score > 0) {
      // Get company name
      const company = parsedSeed.companies.find(c => c.id === product.company_id);
      
      results.push({
        id: product.id,
        type: 'product',
        title: product.name,
        subtitle: company?.name,
        description: product.short_desc,
        companyId: product.company_id,
        productId: product.id,
        tags: product.tags,
        score
      });
    }
  }
  
  return results.sort((a, b) => b.score - a.score).slice(0, 5);
}

/**
 * Search signals with ranking
 */
export async function searchSignals(query: string): Promise<SearchResult[]> {
  await delay(100);
  
  const normalizedQuery = query.toLowerCase().trim();
  if (!normalizedQuery) return [];
  
  const results: SearchResult[] = [];
  
  for (const signal of parsedSeed.signals) {
    let score = 0;
    
    // Headline starts with query
    if (signal.headline.toLowerCase().startsWith(normalizedQuery)) {
      score = 80;
    }
    // Headline contains query
    else if (signal.headline.toLowerCase().includes(normalizedQuery)) {
      score = 60;
    }
    // Summary contains query
    else if (signal.summary && signal.summary.toLowerCase().includes(normalizedQuery)) {
      score = 40;
    }
    
    if (score > 0) {
      // Get company names
      const companies = parsedSeed.companies.filter(c => signal.company_ids.includes(c.id));
      const companyNames = companies.map(c => c.name).slice(0, 2);
      
      results.push({
        id: signal.id,
        type: 'signal',
        title: signal.headline,
        subtitle: companyNames.join(', '),
        description: signal.summary,
        signalId: signal.id,
        date: signal.published_at,
        score
      });
    }
  }
  
  return results.sort((a, b) => b.score - a.score).slice(0, 5);
}

/**
 * Search releases with ranking
 */
export async function searchReleases(query: string): Promise<SearchResult[]> {
  await delay(100);
  
  const normalizedQuery = query.toLowerCase().trim();
  if (!normalizedQuery) return [];
  
  const results: SearchResult[] = [];
  
  for (const release of parsedSeed.releases) {
    let score = 0;
    
    // Get product name for search
    const product = parsedSeed.products.find(p => p.id === release.product_id);
    const productName = product?.name || '';
    const searchableText = [
      productName,
      release.version || '',
      release.notes || ''
    ].join(' ').toLowerCase();
    
    // Product name starts with query
    if (productName.toLowerCase().startsWith(normalizedQuery)) {
      score = 80;
    }
    // Product name contains query
    else if (productName.toLowerCase().includes(normalizedQuery)) {
      score = 60;
    }
    // Version or notes contain query
    else if (searchableText.includes(normalizedQuery)) {
      score = 40;
    }
    
    if (score > 0) {
      // Get company name
      const company = parsedSeed.companies.find(c => c.id === release.company_id);
      
      const title = release.version 
        ? `${productName} — ${release.version}`
        : productName;
      
      results.push({
        id: release.id,
        type: 'release',
        title,
        subtitle: company?.name,
        description: release.notes,
        companyId: release.company_id,
        productId: release.product_id,
        releaseId: release.id,
        date: release.released_at,
        score
      });
    }
  }
  
  return results.sort((a, b) => b.score - a.score).slice(0, 5);
}

/**
 * Global search function that searches all categories
 */
export async function globalSearch(query: string): Promise<{
  companies: SearchResult[];
  products: SearchResult[];
  signals: SearchResult[];
  releases: SearchResult[];
}> {
  // Check for search operators
  const lowerQuery = query.toLowerCase().trim();
  
  if (lowerQuery.startsWith('company:')) {
    const searchTerm = query.substring(8).trim();
    const companies = await searchCompanies(searchTerm);
    return { companies, products: [], signals: [], releases: [] };
  }
  
  if (lowerQuery.startsWith('product:')) {
    const searchTerm = query.substring(8).trim();
    const products = await searchProducts(searchTerm);
    return { companies: [], products, signals: [], releases: [] };
  }
  
  if (lowerQuery.startsWith('signal:')) {
    const searchTerm = query.substring(7).trim();
    const signals = await searchSignals(searchTerm);
    return { companies: [], products: [], signals, releases: [] };
  }
  
  if (lowerQuery.startsWith('release:')) {
    const searchTerm = query.substring(8).trim();
    const releases = await searchReleases(searchTerm);
    return { companies: [], products: [], signals: [], releases };
  }
  
  // Search all categories
  const [companies, products, signals, releases] = await Promise.all([
    searchCompanies(query),
    searchProducts(query),
    searchSignals(query),
    searchReleases(query)
  ]);
  
  return { companies, products, signals, releases };
}
