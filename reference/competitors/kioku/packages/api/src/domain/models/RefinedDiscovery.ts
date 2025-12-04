/**
 * RefinedDiscovery - AI-enhanced discovery from session conversations
 *
 * Purpose: Improve discovery quality via Claude API refinement.
 * Used by: AI Discovery feature (User Story 4)
 *
 * @module domain/models
 */

export enum DiscoveryType {
  PATTERN = 'pattern',
  RULE = 'rule',
  DECISION = 'decision',
  ISSUE = 'issue',
  INSIGHT = 'insight',
}

export interface RefinedDiscovery {
  id: string;                      // UUID v4
  sessionId: string;               // Reference to session

  // Content
  rawContent: string;              // Original regex-extracted content
  refinedContent: string;          // AI-refined description
  type: DiscoveryType;

  // AI metadata
  confidence: number;              // 0-1 (only persist if >= 0.6)
  supportingEvidence: string;      // Message excerpt from conversation
  suggestedModule?: string;        // Module where this applies

  // Processing metadata
  aiModel: string;                 // e.g., "claude-3-sonnet-20240229"
  tokensUsed: number;
  processingTime: number;          // Milliseconds

  // Status
  accepted: boolean;               // User accepted/rejected
  appliedAt?: Date;                // When applied to project.yaml

  // Timestamps
  createdAt: Date;
  updatedAt: Date;
}
