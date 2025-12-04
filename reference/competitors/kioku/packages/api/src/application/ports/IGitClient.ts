/**
 * IGitClient - Interface for Git operations
 *
 * Purpose: Define contract for git history queries.
 * Implementation: GitClient (simple-git wrapper) will implement this.
 * Used by: Git MCP tools (git_log, git_blame, git_diff)
 *
 * @module application/ports
 */

import type { GitCommit } from 'domain/models/GitCommit';
import type { GitBlame } from 'domain/models/GitBlame';
import type { GitDiff } from 'domain/models/GitDiff';

export interface GitLogOptions {
  filePaths?: string[];
  limit?: number;
  since?: string;          // ISO date string
  until?: string;          // ISO date string
  author?: string;
}

export interface GitBlameOptions {
  filePath: string;
  startLine?: number;
  endLine?: number;
}

export interface GitDiffOptions {
  ref1: string;            // Commit SHA, branch, or tag
  ref2?: string;           // If omitted, compare ref1 to working directory
  filePaths?: string[];
}

export interface IGitClient {
  /**
   * Check if current directory is a git repository
   */
  isGitRepository(): Promise<boolean>;

  /**
   * Get commit history
   */
  log(options: GitLogOptions): Promise<GitCommit[]>;

  /**
   * Get line-by-line authorship (git blame)
   */
  blame(options: GitBlameOptions): Promise<GitBlame>;

  /**
   * Get diff between two references
   */
  diff(options: GitDiffOptions): Promise<GitDiff>;

  /**
   * Get current branch name
   */
  getCurrentBranch(): Promise<string>;

  /**
   * Get repository root path
   */
  getRepositoryRoot(): Promise<string>;
}
