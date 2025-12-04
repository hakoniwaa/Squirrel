/**
 * Redact Sensitive Data
 *
 * Pure function to redact sensitive information from text
 * before sending to external AI APIs
 *
 * Purpose: Protect user privacy and prevent credential leakage
 * Used by: AIDiscoveryService
 */

import { REDACTION_PATTERNS, type RedactionPattern } from "domain/rules/redaction-rules";

export interface RedactionResult {
  redactedText: string;
  redactionsApplied: RedactionSummary[];
  hasRedactions: boolean;
}

export interface RedactionSummary {
  type: string;
  count: number;
  positions: number[];
}

/**
 * Redact all sensitive data patterns from text
 *
 * @param text - The text to redact
 * @param allowList - Optional array of strings to exclude from redaction
 * @returns Redaction result with redacted text and summary
 */
export function redactSensitiveData(
  text: string,
  allowList: string[] = []
): RedactionResult {
  let redactedText = text;
  const redactionsApplied = new Map<string, RedactionSummary>();

  // Apply each redaction pattern
  for (const pattern of REDACTION_PATTERNS) {
    const matches = Array.from(text.matchAll(pattern.pattern));

    if (matches.length === 0) {
      continue;
    }

    const positions: number[] = [];
    let offset = 0;

    for (const match of matches) {
      const matchedText = match[0];
      const matchIndex = match.index ?? 0;

      // Check if matched text is in allow-list
      if (isAllowed(matchedText, allowList)) {
        continue;
      }

      // Calculate position in redacted text (accounting for previous replacements)
      positions.push(matchIndex + offset);

      // Replace in redacted text
      const before = redactedText.substring(0, matchIndex + offset);
      const after = redactedText.substring(matchIndex + offset + matchedText.length);
      redactedText = before + pattern.replacement + after;

      // Update offset for subsequent replacements
      offset += pattern.replacement.length - matchedText.length;
    }

    // Track redactions applied
    if (positions.length > 0) {
      redactionsApplied.set(pattern.type, {
        type: pattern.type,
        count: positions.length,
        positions,
      });
    }
  }

  return {
    redactedText,
    redactionsApplied: Array.from(redactionsApplied.values()),
    hasRedactions: redactionsApplied.size > 0,
  };
}

/**
 * Check if a matched string is in the allow-list
 */
function isAllowed(text: string, allowList: string[]): boolean {
  if (allowList.length === 0) {
    return false;
  }

  // Case-insensitive match
  const lowerText = text.toLowerCase();
  return allowList.some(allowed => lowerText.includes(allowed.toLowerCase()));
}

/**
 * Redact sensitive data with custom patterns
 */
export function redactWithCustomPatterns(
  text: string,
  customPatterns: RedactionPattern[],
  allowList: string[] = []
): RedactionResult {
  let redactedText = text;
  const redactionsApplied = new Map<string, RedactionSummary>();

  // Apply custom patterns first, then standard patterns
  const allPatterns = [...customPatterns, ...REDACTION_PATTERNS];

  for (const pattern of allPatterns) {
    const matches = Array.from(text.matchAll(pattern.pattern));

    if (matches.length === 0) {
      continue;
    }

    const positions: number[] = [];
    let offset = 0;

    for (const match of matches) {
      const matchedText = match[0];
      const matchIndex = match.index ?? 0;

      if (isAllowed(matchedText, allowList)) {
        continue;
      }

      positions.push(matchIndex + offset);

      const before = redactedText.substring(0, matchIndex + offset);
      const after = redactedText.substring(matchIndex + offset + matchedText.length);
      redactedText = before + pattern.replacement + after;

      offset += pattern.replacement.length - matchedText.length;
    }

    if (positions.length > 0) {
      const existing = redactionsApplied.get(pattern.type);
      if (existing) {
        existing.count += positions.length;
        existing.positions.push(...positions);
      } else {
        redactionsApplied.set(pattern.type, {
          type: pattern.type,
          count: positions.length,
          positions,
        });
      }
    }
  }

  return {
    redactedText,
    redactionsApplied: Array.from(redactionsApplied.values()),
    hasRedactions: redactionsApplied.size > 0,
  };
}
