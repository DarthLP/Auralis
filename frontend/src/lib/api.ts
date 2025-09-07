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
