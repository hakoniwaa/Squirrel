/**
 * Git Blame Tool
 *
 * MCP tool for showing line-by-line authorship of a file.
 *
 * @module infrastructure/mcp/tools
 */

import { z } from "zod";
import { GitClient } from "infrastructure/external/git-client";
import type { GitBlameOptions } from "application/ports/IGitClient";
import type { GitBlame, GitBlameLine } from "domain/models/GitBlame";
import type { SessionManager } from "application/use-cases/SessionManager";
import { logger } from "../cli/logger";

// Zod schema for input validation
export const GitBlameSchema = z.object({
  filePath: z
    .string()
    .min(1)
    .describe("Path to the file (relative to repository root)"),
  startLine: z
    .number()
    .min(1)
    .optional()
    .describe("Start line number (optional, for range)"),
  endLine: z
    .number()
    .min(1)
    .optional()
    .describe("End line number (optional, for range)"),
});

export type GitBlameInput = z.infer<typeof GitBlameSchema>;

export class GitBlameTool {
  private gitClient: GitClient;

  constructor(
    repoPath: string,
    _sessionManager?: SessionManager, // Reserved for future use when tracking git tool usage
  ) {
    this.gitClient = new GitClient(repoPath);
  }

  async execute(input: GitBlameInput): Promise<string> {
    const startTime = Date.now();
    logger.info("Git blame tool called", input);

    try {
      // Validate input
      const validated = GitBlameSchema.parse(input);

      // Check if git repository
      const isRepo = await this.gitClient.isGitRepository();
      if (!isRepo) {
        logger.warn("Git blame called on non-git repository", {
          filePath: validated.filePath,
        });
        return "❌ **Not a git repository**\n\nThe current directory is not a git repository. Git blame is not available.";
      }

      // Get blame information
      const blameOptions: GitBlameOptions = {
        filePath: validated.filePath,
      };

      if (validated.startLine !== undefined) {
        blameOptions.startLine = validated.startLine;
      }
      if (validated.endLine !== undefined) {
        blameOptions.endLine = validated.endLine;
      }

      const blame = await this.gitClient.blame(blameOptions);

      // Format as markdown
      const result = this.formatBlame(blame, validated);
      const duration = Date.now() - startTime;

      logger.info("Git blame completed", {
        filePath: validated.filePath,
        linesCount: blame.lines.length,
        duration,
      });

      return result;
    } catch (error) {
      const duration = Date.now() - startTime;
      logger.error("Git blame failed", {
        error,
        filePath: input.filePath,
        duration,
      });

      if (error instanceof Error) {
        if (
          error.message.includes("not a git repository") ||
          error.message.includes("not inside a work tree")
        ) {
          return "❌ **Not a git repository**\n\nThe current directory is not a git repository. Git blame is not available.";
        }
        if (error.message.includes("does not exist")) {
          return `❌ **File not found**\n\nThe file \`${input.filePath}\` does not exist in the repository.`;
        }
        if (error.message.includes("binary file")) {
          return `❌ **Binary file**\n\nThe file \`${input.filePath}\` is a binary file. Git blame is only available for text files.`;
        }
        if (error.message.includes("no such path")) {
          return `❌ **Invalid path**\n\nThe path \`${input.filePath}\` is not valid or not tracked by git.`;
        }
      }

      throw error;
    }
  }

  private formatBlame(blame: GitBlame, options: GitBlameInput): string {
    let markdown = `# Git Blame: ${blame.filePath}\n\n`;

    if (options.startLine && options.endLine) {
      markdown += `**Lines:** ${options.startLine}-${options.endLine}\n`;
    } else {
      markdown += `**Total Lines:** ${blame.totalLines}\n`;
    }

    markdown += "\n---\n\n";

    if (blame.lines.length === 0) {
      return markdown + "No lines to display.";
    }

    // Group consecutive lines by commit for cleaner output
    const groups: { commit: GitBlameLine["commit"]; lines: GitBlameLine[] }[] =
      [];
    let currentGroup: {
      commit: GitBlameLine["commit"];
      lines: GitBlameLine[];
    } | null = null;

    for (const line of blame.lines) {
      if (!currentGroup || currentGroup.commit.sha !== line.commit.sha) {
        currentGroup = {
          commit: line.commit,
          lines: [line],
        };
        groups.push(currentGroup);
      } else {
        currentGroup.lines.push(line);
      }
    }

    // Format groups
    for (const group of groups) {
      markdown += `### ${group.commit.shortSha} - ${group.commit.author}\n\n`;
      markdown += `**Date:** ${group.commit.date.toISOString()}\n`;
      markdown += `**Message:** ${group.commit.message}\n\n`;
      markdown += "```\n";

      for (const line of group.lines) {
        markdown += `${String(line.lineNumber).padStart(4, " ")} | ${line.content}\n`;
      }

      markdown += "```\n\n";
    }

    return markdown;
  }
}
