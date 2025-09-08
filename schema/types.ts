import { ProductStage, SignalType } from './enums';
import { SpecValue } from './specs';

export interface Company {
  id: string;
  name: string;
  aliases: string[];
  hq_country?: string;
  website?: string;
  status: 'active' | 'dormant';
  tags: string[];
  logoUrl?: string;
  isSelf?: boolean; // true if "Your Company"
}

export interface CompanySummary {
  company_id: string;
  one_liner: string;
  founded_year?: number;
  hq_city?: string;
  employees?: string;
  footprint?: string;
  sites?: string[];
  sources: string[];
}

export interface Product {
  id: string;
  company_id: string;
  name: string;
  category: string;
  stage: ProductStage;
  markets: string[];
  tags: string[];
  short_desc?: string;
  product_url?: string;
  docs_url?: string;
  media?: { hero?: string; video?: string };
  spec_profile?: string;
  specs?: Record<string, SpecValue>;
  released_at?: string; // ISO date string
  eol_at?: string; // ISO date string
  compliance?: string[];
}

export interface Capability {
  id: string;
  name: string;
  definition?: string;
  tags: string[];
}

export interface ProductCapability {
  id: string;
  product_id: string;
  capability_id: string;
  maturity: CapabilityMaturity;
  details?: string;
  metrics?: Record<string, string | number>;
  observed_at?: string; // ISO date string
  source_id?: string;
  method?: 'measured' | 'reported' | 'inferred';
}

export type CapabilityMaturity = 'basic' | 'intermediate' | 'advanced' | 'expert';

export interface Signal {
  id: string;
  type: SignalType;
  headline: string;
  summary?: string;
  published_at: string; // ISO date string
  url: string;
  company_ids: string[];
  product_ids: string[];
  capability_ids: string[];
  impact: '-2' | '-1' | '0' | '1' | '2';
  source_id?: string;
}

export interface Release {
  id: string;
  company_id: string;
  product_id: string;
  version?: string;
  notes?: string;
  released_at: string; // ISO date string
  source_id?: string;
}

export interface Source {
  id: string;
  origin: string;
  author?: string;
  retrieved_at?: string; // ISO date string
  credibility?: 'low' | 'medium' | 'high';
}

export interface Seed {
  companies: Company[];
  company_summaries: CompanySummary[];
  products: Product[];
  capabilities: Capability[];
  product_capabilities: ProductCapability[];
  signals: Signal[];
  releases: Release[];
  sources: Source[];
}
