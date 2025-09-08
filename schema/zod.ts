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
  hq_country: z.string().optional().nullable(),
  website: z.string().url().optional().nullable(),
  status: z.enum(['active', 'dormant']),
  tags: z.array(z.string()),
  logoUrl: z.string().optional().nullable(),
  isSelf: z.boolean().optional().nullable(),
});

// CompanySummary schema
export const zCompanySummary = z.object({
  company_id: z.string(),
  one_liner: z.string(),
  founded_year: z.number().optional().nullable(),
  hq_city: z.string().optional().nullable(),
  employees: z.string().optional().nullable(),
  footprint: z.string().optional().nullable(),
  sites: z.array(z.string()).optional().nullable(),
  sources: z.array(z.string()),
});

// Product schema
export const zProduct = z.object({
  id: z.string(),
  company_id: z.string(),
  name: z.string(),
  category: z.string(),
  stage: z.enum(['alpha', 'beta', 'ga', 'discontinued', 'deprecated'] as const),
  markets: z.array(z.string()),
  tags: z.array(z.string()),
  short_desc: z.string().optional(),
  product_url: z.string().optional().nullable().refine(
    (val) => !val || val === '' || z.string().url().safeParse(val).success,
    { message: "Invalid URL" }
  ),
  docs_url: z.string().optional().nullable().refine(
    (val) => !val || val === '' || z.string().url().safeParse(val).success,
    { message: "Invalid URL" }
  ),
  media: z.object({
    hero: z.string().optional(),
    video: z.string().optional(),
  }).optional().nullable(),
  spec_profile: z.string().optional().nullable(),
  specs: z.record(z.string(), zSpecValue).optional().nullable(),
  released_at: z.string().datetime().optional().nullable(),
  eol_at: z.string().datetime().optional().nullable(),
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
  maturity: z.enum(['basic', 'intermediate', 'advanced', 'expert', 'ga']),
  details: z.string().optional(),
  metrics: z.record(z.string(), z.union([z.string(), z.number()])).optional().nullable(),
  observed_at: z.string().datetime().optional().nullable(),
  source_id: z.string().optional(),
  method: z.enum(['measured', 'reported', 'inferred']).optional().nullable(),
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
  credibility: z.enum(['low', 'medium', 'high']).optional().nullable(),
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
