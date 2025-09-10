import { ProductStage, SignalType } from './enums';
import { SpecValue } from './specs';

export interface Company {
  id: string;
  name: string;
  aliases: string[];
  hq_country?: string | null;
  website?: string | null;
  status: 'active' | 'dormant';
  tags: string[];
  logoUrl?: string | null;
  isSelf?: boolean | null; // true if "Your Company"
}

export interface CompanySummary {
  company_id: string;
  one_liner: string;
  founded_year?: number | null;
  hq_city?: string | null;
  employees?: string | null;
  footprint?: string | null;
  sites?: string[] | null;
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
  product_url?: string | null;
  docs_url?: string | null;
  media?: { hero?: string; video?: string } | null;
  spec_profile?: string | null;
  specs?: Record<string, SpecValue> | null;
  released_at?: string | null; // ISO date string
  eol_at?: string | null; // ISO date string
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
  metrics?: Record<string, string | number> | null;
  observed_at?: string | null; // ISO date string
  source_id?: string;
  method?: 'measured' | 'reported' | 'inferred' | null;
}

export type CapabilityMaturity = 'basic' | 'intermediate' | 'advanced' | 'expert' | 'ga';

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


export interface Source {
  id: string;
  origin: string;
  author?: string;
  retrieved_at?: string; // ISO date string
  credibility?: 'low' | 'medium' | 'high' | null;
}

export interface Seed {
  companies: Company[];
  company_summaries: CompanySummary[];
  products: Product[];
  capabilities: Capability[];
  product_capabilities: ProductCapability[];
  signals: Signal[];
  sources: Source[];
}
