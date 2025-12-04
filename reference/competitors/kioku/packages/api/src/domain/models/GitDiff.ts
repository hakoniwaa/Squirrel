/**
 * GitDiff - Represents changes between two git references
 *
 * Purpose: Show what changed between commits/branches.
 * Used by: Git Integration feature (User Story 1)
 *
 * @module domain/models
 */

export enum ChangeType {
  ADDED = 'added',
  MODIFIED = 'modified',
  DELETED = 'deleted',
  RENAMED = 'renamed',
}

export interface FileDiff {
  filePath: string;
  oldPath?: string;                // For renames
  changeType: ChangeType;
  additions: number;               // Lines added
  deletions: number;               // Lines deleted
  diff: string;                    // Unified diff format
  isBinary: boolean;               // Is binary file?
}

export interface GitDiff {
  ref1: string;                    // First reference (commit/branch/tag)
  ref2?: string;                   // Second reference (if comparing two)
  files: FileDiff[];
  summary: {
    filesChanged: number;
    insertions: number;
    deletions: number;
  };
}
