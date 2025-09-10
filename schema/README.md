# Schema

This directory contains the core data models and validation schemas for the Auralis platform. The schemas define the structure for tech industry intelligence data including companies, products, capabilities, signals, and more.

The schema system provides a **single source of truth** with automatic conversion from TypeScript/Zod schemas to JSON Schema for backend validation, ensuring type safety across the entire stack.

## 📁 File Structure

- **`enums.ts`** - Core enumeration types
- **`specs.ts`** - Flexible specification value types
- **`types.ts`** - TypeScript interface definitions
- **`zod.ts`** - Runtime validation schemas using Zod
- **`index.ts`** - Re-exports all types and schemas
- **`build-json-schema.ts`** - Build script for JSON Schema generation
- **`package.json`** - NPM package configuration
- **`tsconfig.json`** - TypeScript configuration

### Generated Files

- **`../backend/app/schema/json/*.schema.json`** - Auto-generated JSON Schema files for backend validation

## 🏗️ Data Model Overview

### Core Entities

#### Company
Represents technology companies with basic information and status tracking.
```typescript
interface Company {
  id: string;
  name: string;
  aliases: string[];
  hq_country?: string;
  website?: string;
  status: 'active' | 'dormant';
  tags: string[];
}
```

#### Product
Technology products with lifecycle management, specifications, and compliance tracking.
```typescript
interface Product {
  id: string;
  company_id: string;
  name: string;
  category: string;
  stage: ProductStage; // 'alpha' | 'beta' | 'ga' | 'discontinued'
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
```

#### Capability
Technical capabilities that can be measured and tracked across products.
```typescript
interface Capability {
  id: string;
  name: string;
  definition?: string;
  tags: string[];
}
```

#### ProductCapability
Links products to capabilities with maturity assessment and metrics.
```typescript
interface ProductCapability {
  id: string;
  product_id: string;
  capability_id: string;
  maturity: 'basic' | 'intermediate' | 'advanced' | 'expert';
  details?: string;
  metrics?: Record<string, string | number>;
  observed_at?: string; // ISO date string
  source_id?: string;
  method?: 'measured' | 'reported' | 'inferred';
}
```

#### Signal
News, events, and other signals with impact scoring and entity associations.
```typescript
interface Signal {
  id: string;
  type: SignalType; // 'news' | 'job' | 'paper' | 'funding' | 'release' | 'social'
  headline: string;
  summary?: string;
  published_at: string; // ISO date string
  url: string;
  company_ids: string[];
  product_ids: string[];
  capability_ids: string[];
  impact: -2 | -1 | 0 | 1 | 2; // Negative to positive impact scale
  source_id?: string;
}
```

#### Release
Product release information with versioning and notes.
```typescript
interface Release {
  id: string;
  company_id: string;
  product_id: string;
  version?: string;
  notes?: string;
  released_at: string; // ISO date string
  source_id?: string;
}
```

#### Source
Data provenance and credibility tracking for all information.
```typescript
interface Source {
  id: string;
  origin: string;
  author?: string;
  retrieved_at?: string; // ISO date string
  credibility?: 'low' | 'medium' | 'high';
}
```

### Flexible Specification System

The `SpecValue` type provides a flexible way to store various types of product specifications:

```typescript
type SpecValue =
  | { type: 'text'; value: string }
  | { type: 'number'; value: number; unit?: string }
  | { type: 'boolean'; value: boolean }
  | { type: 'enum'; value: string }
  | { type: 'range'; min: number; max: number; unit?: string }
  | { type: 'array'; value: SpecValue[] }
  | { type: 'url'; value: string };
```

### Data Exchange Format

The `Seed` interface represents a complete dataset for data exchange:

```typescript
interface Seed {
  companies: Company[];
  company_summaries: CompanySummary[];
  products: Product[];
  capabilities: Capability[];
  product_capabilities: ProductCapability[];
  signals: Signal[];
  sources: Source[];
}
```

## 🚀 Usage

### TypeScript Types
```typescript
import { Company, Product, Signal } from './schema';
// or
import type { Company, Product, Signal } from './schema';
```

### Runtime Validation (Frontend)
```typescript
import { zCompany, zProduct, zSignal } from './schema';

// Validate data at runtime
const company = zCompany.parse(rawCompanyData);
const product = zProduct.parse(rawProductData);
const signal = zSignal.parse(rawSignalData);
```

### Backend Validation (Python)
```python
from app.services.validate import validate_company, validate_product, validate_signal

# Validate data against JSON Schema
validate_company(company_data)
validate_product(product_data)
validate_signal(signal_data)
```

### Complete Schema Import
```typescript
import * as Schema from './schema';
// Access all types and schemas via Schema.*
```

## 🔧 Schema Build System

The schema system includes an automated build pipeline that converts TypeScript/Zod schemas to JSON Schema for backend validation.

### Building Schemas

```bash
# Install dependencies
npm install

# Generate JSON schemas for backend
npm run build

# Watch for changes and rebuild automatically
npm run build:watch
```

### Build Process

1. **Source**: Zod schemas in `zod.ts` serve as the single source of truth
2. **Conversion**: `build-json-schema.ts` converts Zod schemas to JSON Schema using `zod-to-json-schema`
3. **Output**: JSON Schema files are generated in `../backend/app/schema/json/`
4. **Validation**: Backend uses `jsonschema` library to validate data against these schemas

### Available JSON Schemas

After building, the following JSON Schema files are available for backend validation:

- `Company.schema.json` - Company validation
- `Product.schema.json` - Product validation  
- `Capability.schema.json` - Capability validation
- `Signal.schema.json` - Signal validation
- `Release.schema.json` - Release validation
- `Source.schema.json` - Source validation
- `SpecValue.schema.json` - Specification value validation
- `Seed.schema.json` - Complete dataset validation

## 🔍 Key Design Principles

1. **Type Safety**: All interfaces are fully typed with proper optional fields
2. **Flexibility**: SpecValue system handles diverse product specifications
3. **Provenance**: Every piece of data can be traced to its source
4. **Validation**: Zod schemas provide runtime type checking
5. **Extensibility**: Tag systems allow for flexible categorization
6. **Impact Tracking**: Signal impact scoring enables trend analysis

## 📅 Date Handling

All date fields use ISO 8601 datetime strings (e.g., `"2024-01-15T10:30:00Z"`). The Zod schemas include `.datetime()` validation to ensure proper format.

## 🏷️ Tagging System

Both companies and products use flexible tag arrays for categorization. This allows for:
- Multiple categorization schemes
- Easy filtering and searching
- Flexible metadata without schema changes

## 🔗 Relationships

The schema supports complex relationships:
- Companies → Products (one-to-many)
- Products → Capabilities (many-to-many via ProductCapability)
- Signals → Companies/Products/Capabilities (many-to-many)
- All entities → Sources (provenance tracking)

## 🧪 Validation Examples

```typescript
import { zProduct, zSpecValue } from './schema';

// Valid product with specs
const validProduct = {
  id: "prod-123",
  company_id: "comp-456",
  name: "AI Platform",
  category: "Machine Learning",
  stage: "ga",
  markets: ["enterprise", "startups"],
  tags: ["ai", "ml", "enterprise"],
  specs: {
    "max_models": { type: "number", value: 1000 },
    "supported_formats": { type: "array", value: [
      { type: "text", value: "TensorFlow" },
      { type: "text", value: "PyTorch" }
    ]},
    "documentation": { type: "url", value: "https://docs.example.com" }
  }
};

const product = zProduct.parse(validProduct);
```

This schema provides a solid foundation for building comprehensive tech industry intelligence applications! 🚀
