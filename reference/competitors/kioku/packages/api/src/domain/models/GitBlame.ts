/**
 * GitBlame - Line-by-line authorship information
 *
 * Purpose: Show who wrote each line of code and when.
 * Used by: Git Integration feature (User Story 1)
 *
 * @module domain/models
 */

export interface GitBlameLine {
  lineNumber: number;
  content: string;                 // Code content
  commit: {
    sha: string;
    shortSha: string;
    author: string;
    authorEmail: string;
    date: Date;
    message: string;               // Commit message excerpt
  };
}

export interface GitBlame {
  filePath: string;
  lines: GitBlameLine[];
  totalLines: number;
}
