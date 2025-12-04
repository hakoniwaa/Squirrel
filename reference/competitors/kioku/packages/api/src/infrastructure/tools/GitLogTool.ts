/**
 * Git Log Tool
 *
 * MCP tool for querying git commit history.
 *
 * @module infrastructure/mcp/tools
 */

import { z } from "zod";
import { GitClient } from "infrastructure/external/git-client";
import type { GitLogOptions } from "application/ports/IGitClient";
import type { GitCommit } from "domain/models/GitCommit";
import type { SessionManager } from "application/use-cases/SessionManager";
import { logger } from "../cli/logger";

// Zod schema for input validation
export const GitLogSchema = z.object({
  limit: z
    .number()
    .min(1)
    .max(100)
    .optional()
    .default(10)
    .describe("Maximum number of commits to return (default: 10)"),
  filePaths: z
    .array(z.string())
    .optional()
    .describe("Filter commits by file paths"),
  since: z
    .string()
    .optional()
    .describe("Show commits after this date (ISO 8601 format)"),
  until: z
    .string()
    .optional()
    .describe("Show commits before this date (ISO 8601 format)"),
  author: z
    .string()
    .optional()
    .describe("Filter commits by author name or email"),
});

export type GitLogInput = z.infer<typeof GitLogSchema>;

export class GitLogTool {
  private gitClient: GitClient;

  constructor(
    repoPath: string,
    _sessionManager?: SessionManager, // Reserved for future use when tracking git tool usage
  ) {
    this.gitClient = new GitClient(repoPath);
  }

  async execute(input: GitLogInput): Promise<string> {
    const startTime = Date.now();
    logger.info("Git log tool called", input);

    try {
      // Validate input
      const validated = GitLogSchema.parse(input);

      // Check if git repository
      const isRepo = await this.gitClient.isGitRepository();
      if (!isRepo) {
        logger.warn("Git log called on non-git repository");
        return "❌ **Not a git repository**\n\nThe current directory is not a git repository. Git history is not available.";
      }

      // Get commit history
      const logOptions: GitLogOptions = {
        limit: validated.limit,
      };

      if (validated.filePaths) {
        logOptions.filePaths = validated.filePaths;
      }
      if (validated.since) {
        logOptions.since = validated.since;
      }
      if (validated.until) {
        logOptions.until = validated.until;
      }
      if (validated.author) {
        logOptions.author = validated.author;
      }

      const commits = await this.gitClient.log(logOptions);

      // Check for shallow clone with limited history
      if (commits.length === 0 && validated.limit > 0) {
        logger.warn("No commits found", { options: logOptions });
      }

      // Format as markdown
      const result = this.formatCommits(commits, validated);
      const duration = Date.now() - startTime;

      logger.info("Git log completed", {
        commitsCount: commits.length,
        filters: {
          filePaths: validated.filePaths,
          since: validated.since,
          until: validated.until,
          author: validated.author,
        },
        duration,
      });

      return result;
    } catch (error) {
      const duration = Date.now() - startTime;
      logger.error("Git log failed", { error, input, duration });

      if (error instanceof Error) {
        if (error.message.includes("does not have any commits")) {
          return "❌ **Empty repository**\n\nThis repository does not have any commits yet.";
        }
        if (
          error.message.includes("not a git repository") ||
          error.message.includes("not inside a work tree")
        ) {
          return "❌ **Not a git repository**\n\nThe current directory is not a git repository. Git history is not available.";
        }
      }

      throw error;
    }
  }

  private formatCommits(commits: GitCommit[], options: GitLogInput): string {
    if (commits.length === 0) {
      return `# Git Log\n\nNo commits found with the given filters.\n\n**Filters applied:**\n${this.formatFilters(options)}`;
    }

    let markdown = `# Git Log\n\nFound ${commits.length} commit${commits.length === 1 ? "" : "s"}`;

    if (options.filePaths || options.since || options.until || options.author) {
      markdown += "\n\n**Filters:**\n" + this.formatFilters(options);
    }

    markdown += "\n\n---\n\n";

    for (const commit of commits) {
      markdown += `## ${commit.shortSha} - ${commit.messageShort}\n\n`;
      markdown += `**Author:** ${commit.author.name} <${commit.author.email}>\n`;
      markdown += `**Date:** ${commit.date.toISOString()}\n`;

      if (commit.filesChanged.length > 0) {
        markdown += `**Files Changed:** ${commit.filesChanged.length}\n`;
      }

      markdown += `\n**Message:**\n\`\`\`\n${commit.message}\n\`\`\`\n\n`;

      if (commit.filesChanged.length > 0 && commit.filesChanged.length <= 10) {
        markdown += "**Files:**\n";
        for (const file of commit.filesChanged) {
          markdown += `- \`${file}\`\n`;
        }
        markdown += "\n";
      }

      markdown += "---\n\n";
    }

    return markdown;
  }

  private formatFilters(options: GitLogInput): string {
    const filters: string[] = [];

    if (options.filePaths && options.filePaths.length > 0) {
      filters.push(
        `- Files: ${options.filePaths.map((f) => `\`${f}\``).join(", ")}`,
      );
    }

    if (options.since) {
      filters.push(`- Since: ${options.since}`);
    }

    if (options.until) {
      filters.push(`- Until: ${options.until}`);
    }

    if (options.author) {
      filters.push(`- Author: ${options.author}`);
    }

    if (options.limit) {
      filters.push(`- Limit: ${options.limit}`);
    }

    return filters.join("\n");
  }
}
