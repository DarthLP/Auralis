// Simple test cases for URL validation
import { validateAndNormalizeUrl, checkReachability, checkDeduplication } from '../urlValidation';

// Test cases as specified in the requirements
const testCases = [
  {
    input: "pal-robotics.com",
    expected: {
      ok: true,
      normalized_origin: "https://pal-robotics.com/",
      eTLD1: "pal-robotics.com"
    }
  },
  {
    input: "https://acme.co.uk/store",
    expected: {
      ok: true,
      normalized_origin: "https://acme.co.uk/",
      eTLD1: "acme.co.uk",
      original_path: "/store"
    }
  },
  {
    input: "ftp://acme.com",
    expected: {
      ok: false,
      reason: "Only HTTP and HTTPS URLs are supported"
    }
  },
  {
    input: "http://10.0.0.5",
    expected: {
      ok: false,
      reason: "Private IP addresses and localhost are not allowed"
    }
  },
  {
    input: "localhost",
    expected: {
      ok: false,
      reason: "Private IP addresses and localhost are not allowed"
    }
  },
  {
    input: "example.com",
    expected: {
      ok: false,
      reason: "Placeholder domains are not allowed"
    }
  }
];

// Run tests
console.log('🧪 Running URL Validation Tests...\n');

testCases.forEach((testCase, index) => {
  const result = validateAndNormalizeUrl(testCase.input);
  const passed = testCase.expected.ok === result.ok && 
    (testCase.expected.reason === result.reason || 
     testCase.expected.normalized_origin === result.normalized_origin);
  
  console.log(`Test ${index + 1}: ${testCase.input}`);
  console.log(`Expected: ${JSON.stringify(testCase.expected)}`);
  console.log(`Got: ${JSON.stringify(result)}`);
  console.log(`✅ ${passed ? 'PASS' : 'FAIL'}\n`);
});

// Test deduplication
console.log('🧪 Testing Deduplication...\n');

const mockCompanies = [
  { id: '1', name: 'PAL Robotics', website: 'https://pal-robotics.com' },
  { id: '2', name: 'Acme Corp', website: 'https://acme.com' }
];

const dedupeTest = checkDeduplication('pal-robotics.com', 'PAL Robotics', mockCompanies);
console.log('Deduplication test for pal-robotics.com:');
console.log(`Result: ${JSON.stringify(dedupeTest)}`);
console.log(`✅ ${dedupeTest.isDuplicate ? 'PASS (duplicate detected)' : 'FAIL (should detect duplicate)'}\n`);

export { testCases };
