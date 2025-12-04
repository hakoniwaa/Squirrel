/**
 * GitClient - Git operations wrapper using simple-git
 *
 * Purpose: Implement IGitClient interface for git history queries.
 * Used by: Git MCP tools (git_log, git_blame, git_diff)
 *
 * @module infrastructure/external
 */

import type { SimpleGit } from "simple-git";
import simpleGit from "simple-git";
import type {
  IGitClient,
  GitLogOptions,
  GitBlameOptions,
  GitDiffOptions,
} from "application/ports/IGitClient";
import type { GitCommit } from "domain/models/GitCommit";
import type { GitBlame, GitBlameLine } from "domain/models/GitBlame";
import type { GitDiff, FileDiff } from "domain/models/GitDiff";
import { ChangeType } from "domain/models/GitDiff";
import { logger } from "../cli/logger";

export class GitClient implements IGitClient {
  private git: SimpleGit;

  constructor(repoPath: string = process.cwd()) {
    this.git = simpleGit(repoPath);
    logger.debug("GitClient initialized", { repoPath });
  }

  async isGitRepository(): Promise<boolean> {
    try {
      await this.git.checkIsRepo();
      return true;
    } catch {
      return false;
    }
  }

  async log(options: GitLogOptions): Promise<GitCommit[]> {
    try {
      logger.debug("Git log requested", options);

      const logOptions: Record<string, string | number> = {
        maxCount: options.limit || 10,
      };

      if (
        options.filePaths &&
        options.filePaths.length > 0 &&
        options.filePaths[0]
      ) {
        logOptions.file = options.filePaths[0];
      }

      if (options.since) {
        logOptions["--since"] = options.since;
      }

      if (options.until) {
        logOptions["--until"] = options.until;
      }

      if (options.author) {
        logOptions["--author"] = options.author;
      }

      const result = await this.git.log(logOptions);

      return result.all.map((commit) => ({
        sha: commit.hash,
        shortSha: commit.hash.substring(0, 7),
        author: {
          name: commit.author_name,
          email: commit.author_email,
        },
        date: new Date(commit.date),
        message: commit.message,
        messageShort: commit.message.split("\n")[0] || commit.message,
        filesChanged: commit.diff?.files?.map((f) => f.file) || [],
      }));
    } catch (error) {
      logger.error("Git log failed", { error, options });
      throw error;
    }
  }

  async blame(options: GitBlameOptions): Promise<GitBlame> {
    try {
      logger.debug("Git blame requested", options);

      const args = ["blame", "--line-porcelain"];

      if (options.startLine && options.endLine) {
        args.push("-L", `${options.startLine},${options.endLine}`);
      }

      args.push(options.filePath);

      const output = await this.git.raw(args);
      const lines = this.parseBlameOutput(output, options.filePath);

      return {
        filePath: options.filePath,
        lines,
        totalLines: lines.length,
      };
    } catch (error) {
      logger.error("Git blame failed", { error, options });
      throw error;
    }
  }

  private parseBlameOutput(output: string, _filePath: string): GitBlameLine[] {
    const lines: GitBlameLine[] = [];
    const outputLines = output.split("\n");

    let currentCommit: Partial<GitBlameLine["commit"]> = {};
    let lineNumber = 1;

    for (const line of outputLines) {
      if (!line) continue;

      if (line.match(/^[a-f0-9]{40}/)) {
        const parts = line.split(" ");
        if (parts[0]) {
          currentCommit.sha = parts[0];
          currentCommit.shortSha = parts[0].substring(0, 7);
        }
      } else if (line.startsWith("author ")) {
        currentCommit.author = line.substring(7);
      } else if (line.startsWith("author-mail ")) {
        currentCommit.authorEmail = line.substring(12).replace(/[<>]/g, "");
      } else if (line.startsWith("author-time ")) {
        currentCommit.date = new Date(parseInt(line.substring(12)) * 1000);
      } else if (line.startsWith("summary ")) {
        currentCommit.message = line.substring(8);
      } else if (line.startsWith("\t")) {
        const content = line.substring(1);

        // Only add line if we have all required commit info
        if (
          currentCommit.sha &&
          currentCommit.shortSha &&
          currentCommit.author &&
          currentCommit.authorEmail &&
          currentCommit.date &&
          currentCommit.message
        ) {
          lines.push({
            lineNumber,
            content,
            commit: {
              sha: currentCommit.sha,
              shortSha: currentCommit.shortSha,
              author: currentCommit.author,
              authorEmail: currentCommit.authorEmail,
              date: currentCommit.date,
              message: currentCommit.message,
            },
          });
        }

        lineNumber++;
        currentCommit = {};
      }
    }

    return lines;
  }

  async diff(options: GitDiffOptions): Promise<GitDiff> {
    try {
      logger.debug("Git diff requested", options);

      const args = ["diff", "--numstat"];

      if (options.ref2) {
        args.push(options.ref1, options.ref2);
      } else {
        args.push(options.ref1);
      }

      if (options.filePaths && options.filePaths.length > 0) {
        args.push("--", ...options.filePaths);
      }

      const numstatOutput = await this.git.raw(args);

      const files: FileDiff[] = [];
      let totalInsertions = 0;
      let totalDeletions = 0;

      const lines = numstatOutput.split("\n").filter((l) => l.trim());
      for (const line of lines) {
        const parts = line.split("\t");
        if (parts.length === 3 && parts[0] && parts[1] && parts[2]) {
          const additions = parseInt(parts[0]) || 0;
          const deletions = parseInt(parts[1]) || 0;
          const filePath = parts[2];

          totalInsertions += additions;
          totalDeletions += deletions;

          files.push({
            filePath,
            changeType: ChangeType.MODIFIED,
            additions,
            deletions,
            diff: "",
            isBinary: parts[0] === "-" && parts[1] === "-",
          });
        }
      }

      const result: GitDiff = {
        ref1: options.ref1,
        files,
        summary: {
          filesChanged: files.length,
          insertions: totalInsertions,
          deletions: totalDeletions,
        },
      };

      if (options.ref2) {
        result.ref2 = options.ref2;
      }

      return result;
    } catch (error) {
      logger.error("Git diff failed", { error, options });
      throw error;
    }
  }

  async getCurrentBranch(): Promise<string> {
    try {
      const branch = await this.git.revparse(["--abbrev-ref", "HEAD"]);
      return branch.trim();
    } catch (error) {
      logger.error("Failed to get current branch", { error });
      throw error;
    }
  }

  async getRepositoryRoot(): Promise<string> {
    try {
      const root = await this.git.revparse(["--show-toplevel"]);
      return root.trim();
    } catch (error) {
      logger.error("Failed to get repository root", { error });
      throw error;
    }
  }
}
