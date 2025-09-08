#!/usr/bin/env tsx

import { zodToJsonSchema } from 'zod-to-json-schema';
import { writeFileSync, mkdirSync } from 'fs';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';

// Import all Zod schemas
import {
  zSpecValue,
  zCompany,
  zCompanySummary,
  zProduct,
  zCapability,
  zProductCapability,
  zSignal,
  zRelease,
  zSource,
  zSeed
} from './zod';

// Define schema mappings
const schemas = {
  SpecValue: zSpecValue,
  Company: zCompany,
  CompanySummary: zCompanySummary,
  Product: zProduct,
  Capability: zCapability,
  ProductCapability: zProductCapability,
  Signal: zSignal,
  Release: zRelease,
  Source: zSource,
  Seed: zSeed
} as const;

// Get current directory
const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

// Define output directory
const outputDir = join(__dirname, '..', 'backend', 'app', 'schema', 'json');

/**
 * Convert Zod schemas to JSON Schema and write to files
 */
function buildJsonSchemas() {
  console.log('🔧 Building JSON schemas from Zod definitions...');
  
  // Ensure output directory exists
  mkdirSync(outputDir, { recursive: true });
  
  let successCount = 0;
  let errorCount = 0;
  
  // Convert each schema
  for (const [name, zodSchema] of Object.entries(schemas)) {
    try {
      console.log(`📝 Converting ${name}...`);
      
      // Convert Zod schema to JSON Schema
      const jsonSchema = zodToJsonSchema(zodSchema, {
        name,
        target: 'jsonSchema7',
        // Add metadata for better validation error messages
        errorMessages: true,
        markdownDescription: true,
      });
      
      // Add additional metadata
      const enhancedSchema = {
        ...jsonSchema,
        $schema: 'https://json-schema.org/draft/2020-12/schema',
        $id: `https://auralis.com/schemas/${name}.schema.json`,
        title: `${name} Schema`,
        description: `JSON Schema for ${name} validation in Auralis backend`,
        generated: new Date().toISOString(),
        version: '1.0.0'
      };
      
      // Write to file
      const outputPath = join(outputDir, `${name}.schema.json`);
      writeFileSync(outputPath, JSON.stringify(enhancedSchema, null, 2), 'utf8');
      
      console.log(`✅ ${name}.schema.json created`);
      successCount++;
      
    } catch (error) {
      console.error(`❌ Error converting ${name}:`, error);
      errorCount++;
    }
  }
  
  // Summary
  console.log('\n📊 Build Summary:');
  console.log(`✅ Success: ${successCount} schemas`);
  console.log(`❌ Errors: ${errorCount} schemas`);
  console.log(`📁 Output: ${outputDir}`);
  
  if (errorCount > 0) {
    process.exit(1);
  }
  
  console.log('\n🎉 JSON Schema build completed successfully!');
}

// Run the build
buildJsonSchemas();

export { buildJsonSchemas };
