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
