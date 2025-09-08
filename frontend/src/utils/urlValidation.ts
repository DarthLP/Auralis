// URL validation and normalization utility for Add Competitor feature

export interface ValidationResult {
  ok: boolean;
  reason?: string;
  normalized_origin: string;
  requested_url: string;
  original_path?: string;
  eTLD1: string;
}

// Private IP ranges and localhost patterns
const PRIVATE_IP_PATTERNS = [
  /^127\./,           // 127.0.0.0/8
  /^10\./,            // 10.0.0.0/8
  /^192\.168\./,      // 192.168.0.0/16
  /^172\.(1[6-9]|2[0-9]|3[0-1])\./, // 172.16.0.0/12
  /^::1$/,            // IPv6 localhost
  /^localhost$/i,     // localhost
  /^0\.0\.0\.0$/,     // 0.0.0.0
];

// Placeholder domains to reject
const PLACEHOLDER_DOMAINS = [
  'example.com',
  'example.org',
  'example.net',
  'test.com',
  'test.org',
  'test.net',
  'localhost',
  'local',
];

// Simple eTLD+1 extraction (fallback for common cases)
function extractETLD1(hostname: string): string {
  const parts = hostname.toLowerCase().split('.');
  
  if (parts.length <= 1) {
    return hostname.toLowerCase();
  }
  
  // Handle common two-part TLDs
  const twoPartTLDs = [
    'co.uk', 'com.au', 'co.jp', 'co.kr', 'co.za', 'co.in',
    'com.br', 'com.mx', 'com.ar', 'com.sg', 'com.hk',
    'org.uk', 'net.uk', 'ac.uk', 'gov.uk',
    'com.cn', 'net.cn', 'org.cn', 'gov.cn',
  ];
  
  // Check for two-part TLD
  if (parts.length >= 3) {
    const potentialTLD = `${parts[parts.length - 2]}.${parts[parts.length - 1]}`;
    if (twoPartTLDs.includes(potentialTLD)) {
      return `${parts[parts.length - 3]}.${potentialTLD}`;
    }
  }
  
  // Default: take last two parts
  return parts.slice(-2).join('.');
}

// Check if hostname is a private IP or localhost
function isPrivateOrLocalhost(hostname: string): boolean {
  // Check for localhost
  if (hostname.toLowerCase() === 'localhost') {
    return true;
  }
  
  // Check for IPv4 private ranges
  if (PRIVATE_IP_PATTERNS.some(pattern => pattern.test(hostname))) {
    return true;
  }
  
  // Check for IPv6 localhost
  if (hostname === '::1') {
    return true;
  }
  
  return false;
}

// Check if domain is a placeholder
function isPlaceholderDomain(hostname: string): boolean {
  return PLACEHOLDER_DOMAINS.includes(hostname.toLowerCase());
}

// Validate and normalize URL
export function validateAndNormalizeUrl(input: string): ValidationResult {
  const trimmed = input.trim();
  
  // Check max length
  if (trimmed.length > 2000) {
    return {
      ok: false,
      reason: 'URL is too long (max 2000 characters)',
      normalized_origin: '',
      requested_url: trimmed,
      eTLD1: ''
    };
  }
  
  // Check for spaces
  if (trimmed.includes(' ')) {
    return {
      ok: false,
      reason: 'URL cannot contain spaces',
      normalized_origin: '',
      requested_url: trimmed,
      eTLD1: ''
    };
  }
  
  // Auto-prepend https:// if no scheme
  let urlToProcess = trimmed;
  // let addedScheme = false;
  
  if (!trimmed.includes('://')) {
    urlToProcess = `https://${trimmed}`;
    // addedScheme = true;
  }
  
  let parsedUrl: URL;
  try {
    parsedUrl = new URL(urlToProcess);
  } catch {
    return {
      ok: false,
      reason: 'Invalid URL format',
      normalized_origin: '',
      requested_url: trimmed,
      eTLD1: ''
    };
  }
  
  // Check scheme
  if (!['http:', 'https:'].includes(parsedUrl.protocol)) {
    return {
      ok: false,
      reason: 'Only HTTP and HTTPS URLs are supported',
      normalized_origin: '',
      requested_url: trimmed,
      eTLD1: ''
    };
  }
  
  // Extract hostname
  const hostname = parsedUrl.hostname.toLowerCase();
  
  // Check for private IPs and localhost
  if (isPrivateOrLocalhost(hostname)) {
    return {
      ok: false,
      reason: 'Private IP addresses and localhost are not allowed',
      normalized_origin: '',
      requested_url: trimmed,
      eTLD1: ''
    };
  }
  
  // Check for placeholder domains
  if (isPlaceholderDomain(hostname)) {
    return {
      ok: false,
      reason: 'Placeholder domains are not allowed',
      normalized_origin: '',
      requested_url: trimmed,
      eTLD1: ''
    };
  }
  
  // Check if hostname has at least one dot (valid domain)
  if (!hostname.includes('.')) {
    return {
      ok: false,
      reason: 'Invalid domain name',
      normalized_origin: '',
      requested_url: trimmed,
      eTLD1: ''
    };
  }
  
  // Build normalized origin
  const port = parsedUrl.port && !['80', '443'].includes(parsedUrl.port) 
    ? `:${parsedUrl.port}` 
    : '';
  const normalized_origin = `${parsedUrl.protocol}//${hostname}${port}/`;
  
  // Extract eTLD+1
  const eTLD1 = extractETLD1(hostname);
  
  // Extract original path if it exists
  const original_path = parsedUrl.pathname + parsedUrl.search + parsedUrl.hash;
  const hasPath = original_path && original_path !== '/';
  
  return {
    ok: true,
    normalized_origin,
    requested_url: trimmed,
    original_path: hasPath ? original_path : undefined,
    eTLD1
  };
}

// Mock reachability check
export interface ReachabilityResult {
  ok: boolean;
  reason?: string;
  status?: number;
  redirects?: number;
  final_url?: string;
}

export async function checkReachability(normalized_origin: string): Promise<ReachabilityResult> {
  // Simulate network delay
  await new Promise(resolve => setTimeout(resolve, 500));
  
  try {
    const url = new URL(normalized_origin);
    const hostname = url.hostname.toLowerCase();
    
    // Check if hostname has a dot (valid domain)
    if (!hostname.includes('.')) {
      return {
        ok: false,
        reason: 'Invalid domain name'
      };
    }
    
    // Check for private IPs and localhost
    if (isPrivateOrLocalhost(hostname)) {
      return {
        ok: false,
        reason: 'Private IP addresses and localhost are not allowed'
      };
    }
    
    // Check for placeholder domains
    if (isPlaceholderDomain(hostname)) {
      return {
        ok: false,
        reason: 'Placeholder domains are not allowed'
      };
    }
    
    // Mock successful response
    return {
      ok: true,
      status: 200,
      redirects: 1, // Simulate one redirect (scheme upgrade)
      final_url: normalized_origin
    };
    
  } catch (error) {
    return {
      ok: false,
      reason: 'Failed to reach the website'
    };
  }
}

// De-duplication check
export interface DeduplicationResult {
  isDuplicate: boolean;
  existing_company_id?: string;
  existing_company_name?: string;
  match_type?: 'domain' | 'name';
}

export function checkDeduplication(
  eTLD1: string, 
  companyName: string, 
  existingCompanies: Array<{ id: string; name: string; website?: string | null }>
): DeduplicationResult {
  for (const company of existingCompanies) {
    // Check by domain (eTLD+1)
    if (company.website) {
      try {
        const companyUrl = new URL(company.website);
        const companyETLD1 = extractETLD1(companyUrl.hostname.toLowerCase());
        
        if (companyETLD1 === eTLD1) {
          return {
            isDuplicate: true,
            existing_company_id: company.id,
            existing_company_name: company.name,
            match_type: 'domain'
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
        isDuplicate: true,
        existing_company_id: company.id,
        existing_company_name: company.name,
        match_type: 'name'
      };
    }
  }
  
  return { isDuplicate: false };
}
