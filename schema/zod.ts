import { z } from 'zod';
import { SpecValue } from './specs';

// SpecValue schema
export const zSpecValue: z.ZodType<SpecValue> = z.discriminatedUnion('type', [
  z.object({ type: z.literal('text'), value: z.string() }),
  z.object({ type: z.literal('number'), value: z.number(), unit: z.string().optional() }),
  z.object({ type: z.literal('boolean'), value: z.boolean() }),
  z.object({ type: z.literal('enum'), value: z.string() }),
  z.object({ type: z.literal('range'), min: z.number(), max: z.number(), unit: z.string().optional() }),
  z.object({ type: z.literal('array'), value: z.lazy(() => z.array(zSpecValue)) }),
  z.object({ type: z.literal('url'), value: z.string().url() }),
]);

// Company schema
export const zCompany = z.object({
  id: z.string(),
  name: z.string(),
  aliases: z.array(z.string()),
  hq_country: z.string().optional(),
  website: z.string().url().optional(),
  status: z.enum(['active', 'dormant']),
  tags: z.array(z.string()),
});

// CompanySummary schema
export const zCompanySummary = z.object({
  company_id: z.string(),
  one_liner: z.string(),
  founded_year: z.number().optional(),
  hq_city: z.string().optional(),
  employees: z.string().optional(),
  footprint: z.string().optional(),
  sites: z.array(z.string()).optional(),
  sources: z.array(z.string()),
});

// Product schema
export const zProduct = z.object({
  id: z.string(),
  company_id: z.string(),
  name: z.string(),
  category: z.string(),
  stage: z.enum(['alpha', 'beta', 'ga', 'discontinued'] as const),
  markets: z.array(z.string()),
  tags: z.array(z.string()),
  short_desc: z.string().optional(),
  product_url: z.string().url().optional(),
  docs_url: z.string().url().optional(),
  media: z.object({
    hero: z.string().optional(),
    video: z.string().optional(),
  }).optional(),
  spec_profile: z.string().optional(),
  specs: z.record(z.string(), zSpecValue).optional(),
  released_at: z.string().datetime().optional(),
  eol_at: z.string().datetime().optional(),
  compliance: z.array(z.string()).optional(),
});

// Capability schema
export const zCapability = z.object({
  id: z.string(),
  name: z.string(),
  definition: z.string().optional(),
  tags: z.array(z.string()),
});

// ProductCapability schema
export const zProductCapability = z.object({
  id: z.string(),
  product_id: z.string(),
  capability_id: z.string(),
  maturity: z.enum(['basic', 'intermediate', 'advanced', 'expert']),
  details: z.string().optional(),
  metrics: z.record(z.string(), z.union([z.string(), z.number()])).optional(),
  observed_at: z.string().datetime().optional(),
  source_id: z.string().optional(),
  method: z.enum(['measured', 'reported', 'inferred']).optional(),
});

// Signal schema
export const zSignal = z.object({
  id: z.string(),
  type: z.enum(['news', 'job', 'paper', 'funding', 'release', 'social'] as const),
  headline: z.string(),
  summary: z.string().optional(),
  published_at: z.string().datetime(),
  url: z.string().url(),
  company_ids: z.array(z.string()),
  product_ids: z.array(z.string()),
  capability_ids: z.array(z.string()),
  impact: z.enum(['-2', '-1', '0', '1', '2']),
  source_id: z.string().optional(),
});

// Release schema
export const zRelease = z.object({
  id: z.string(),
  company_id: z.string(),
  product_id: z.string(),
  version: z.string().optional(),
  notes: z.string().optional(),
  released_at: z.string().datetime(),
  source_id: z.string().optional(),
});

// Source schema
export const zSource = z.object({
  id: z.string(),
  origin: z.string(),
  author: z.string().optional(),
  retrieved_at: z.string().datetime().optional(),
  credibility: z.enum(['low', 'medium', 'high']).optional(),
});

// Seed schema
export const zSeed = z.object({
  companies: z.array(zCompany),
  company_summaries: z.array(zCompanySummary),
  products: z.array(zProduct),
  capabilities: z.array(zCapability),
  product_capabilities: z.array(zProductCapability),
  signals: z.array(zSignal),
  releases: z.array(zRelease),
  sources: z.array(zSource),
});
