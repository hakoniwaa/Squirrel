/**
 * Redaction Rules
 *
 * Patterns for detecting and redacting sensitive information
 * before sending data to external AI APIs
 *
 * Purpose: Protect user privacy and prevent credential leakage
 * Used by: AIDiscoveryService before calling Anthropic API
 */

export enum RedactionType {
  API_KEY = "API_KEY",
  OAUTH_TOKEN = "OAUTH_TOKEN",
  EMAIL = "EMAIL",
  PHONE = "PHONE",
  IP_ADDRESS = "IP_ADDRESS",
  CREDIT_CARD = "CREDIT_CARD",
  SSN = "SSN",
  PRIVATE_KEY = "PRIVATE_KEY",
}

export interface RedactionPattern {
  type: RedactionType;
  pattern: RegExp;
  replacement: string;
  description: string;
}

/**
 * Comprehensive redaction patterns for sensitive data
 * Ordered by specificity (more specific patterns first)
 */
export const REDACTION_PATTERNS: RedactionPattern[] = [
  // API Keys
  {
    type: RedactionType.API_KEY,
    pattern: /(sk-[a-zA-Z0-9]{20,}|sk-ant-[a-zA-Z0-9\-]{20,}|AKIA[0-9A-Z]{16}|[A-Z_]*API[_]?KEY[A-Z_]*\s*[:=]\s*['"]?[a-zA-Z0-9\-_]{16,}['"]?)/gi,
    replacement: "[REDACTED:API_KEY]",
    description: "API keys (OpenAI, Anthropic, AWS, generic)",
  },

  // OAuth and Bearer Tokens
  {
    type: RedactionType.OAUTH_TOKEN,
    pattern: /(Bearer\s+[a-zA-Z0-9\-._~+\/]+=*|ghp_[a-zA-Z0-9]{36}|gho_[a-zA-Z0-9]{36}|github_pat_[a-zA-Z0-9]{22}_[a-zA-Z0-9]{59}|glpat-[a-zA-Z0-9\-]{20}|access_token[:=]['"]?[a-zA-Z0-9\-._~+\/]+=*['"]?)/gi,
    replacement: "[REDACTED:OAUTH_TOKEN]",
    description: "OAuth tokens, Bearer tokens, GitHub tokens, GitLab tokens",
  },

  // Private Keys
  {
    type: RedactionType.PRIVATE_KEY,
    pattern: /(-----BEGIN\s+(RSA|DSA|EC|OPENSSH|PGP)\s+PRIVATE\s+KEY-----[\s\S]*?-----END\s+(RSA|DSA|EC|OPENSSH|PGP)\s+PRIVATE\s+KEY-----)/gi,
    replacement: "[REDACTED:PRIVATE_KEY]",
    description: "SSH, RSA, DSA, EC, OpenSSH, PGP private keys",
  },

  // Email Addresses
  {
    type: RedactionType.EMAIL,
    pattern: /\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b/g,
    replacement: "[REDACTED:EMAIL]",
    description: "Email addresses",
  },

  // Phone Numbers (various formats)
  {
    type: RedactionType.PHONE,
    pattern: /(\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b/g,
    replacement: "[REDACTED:PHONE]",
    description: "Phone numbers (US and international formats)",
  },

  // IP Addresses (IPv4)
  {
    type: RedactionType.IP_ADDRESS,
    pattern: /\b(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b/g,
    replacement: "[REDACTED:IP_ADDRESS]",
    description: "IPv4 addresses",
  },

  // Credit Card Numbers
  {
    type: RedactionType.CREDIT_CARD,
    pattern: /\b(?:\d{4}[-\s]?){3}\d{4}\b|\b\d{15,16}\b/g,
    replacement: "[REDACTED:CREDIT_CARD]",
    description: "Credit card numbers (Visa, MC, Amex, Discover)",
  },

  // Social Security Numbers
  {
    type: RedactionType.SSN,
    pattern: /\b\d{3}-?\d{2}-?\d{4}\b/g,
    replacement: "[REDACTED:SSN]",
    description: "Social Security Numbers",
  },
];

/**
 * Get all redaction patterns
 * Useful for iteration and testing
 */
export function getAllRedactionPatterns(): RedactionPattern[] {
  return [...REDACTION_PATTERNS];
}

/**
 * Get patterns by type
 */
export function getPatternsByType(type: RedactionType): RedactionPattern[] {
  return REDACTION_PATTERNS.filter(p => p.type === type);
}
