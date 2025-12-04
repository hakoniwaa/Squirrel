/**
 * GitCommit - Represents a git commit with metadata
 *
 * Purpose: Provide historical context via git integration.
 * Used by: Git Integration feature (User Story 1)
 *
 * @module domain/models
 */

export interface GitCommit {
  sha: string;                     // Full commit SHA (40 chars)
  shortSha: string;                // Short SHA (7 chars)
  author: {
    name: string;
    email: string;
  };
  date: Date;
  message: string;                 // Full commit message
  messageShort: string;            // First line of message
  filesChanged: string[];          // Array of file paths
  parentSha?: string;              // Parent commit SHA
}
