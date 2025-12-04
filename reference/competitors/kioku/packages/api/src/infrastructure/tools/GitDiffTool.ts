/**
 * Git Diff Tool
 *
 * MCP tool for comparing changes between git references.
 *
 * @module infrastructure/mcp/tools
 */

import { z } from "zod";
import { GitClient } from "infrastructure/external/git-client";
import type { GitDiffOptions } from "application/ports/IGitClient";
import type { GitDiff } from "domain/models/GitDiff";
import type { SessionManager } from "application/use-cases/SessionManager";
import { logger } from "../cli/logger";

// Zod schema for input validation
export const GitDiffSchema = z.object({
  ref1: z
    .string()
    .min(1)
    .describe("First git reference (commit SHA, branch, or tag)"),
  ref2: z
    .string()
    .optional()
    .describe("Second git reference (optional, defaults to working directory)"),
  filePaths: z
    .array(z.string())
    .optional()
    .describe("Filter diff by specific file paths"),
});

export type GitDiffInput = z.infer<typeof GitDiffSchema>;

export class GitDiffTool {
  private gitClient: GitClient;

  constructor(
    repoPath: string,
    _sessionManager?: SessionManager, // Reserved for future use when tracking git tool usage
  ) {
    this.gitClient = new GitClient(repoPath);
  }

  async execute(input: GitDiffInput): Promise<string> {
    const startTime = Date.now();
    logger.info("Git diff tool called", input);

    try {
      // Validate input
      const validated = GitDiffSchema.parse(input);

      // Check if git repository
      const isRepo = await this.gitClient.isGitRepository();
      if (!isRepo) {
        logger.warn("Git diff called on non-git repository");
        return "❌ **Not a git repository**\n\nThe current directory is not a git repository. Git diff is not available.";
      }

      // Get diff
      const diffOptions: GitDiffOptions = {
        ref1: validated.ref1,
      };

      if (validated.ref2) {
        diffOptions.ref2 = validated.ref2;
      }
      if (validated.filePaths) {
        diffOptions.filePaths = validated.filePaths;
      }

      const diff = await this.gitClient.diff(diffOptions);

      // Check for large diffs and provide summary mode
      const totalChanges =
        diff.summary.filesChanged +
        diff.summary.insertions +
        diff.summary.deletions;
      if (totalChanges > 1000) {
        logger.warn("Large diff detected, returning summary mode", {
          filesChanged: diff.summary.filesChanged,
          totalChanges,
        });
      }

      // Format as markdown
      const result = this.formatDiff(diff, validated);
      const duration = Date.now() - startTime;

      logger.info("Git diff completed", {
        ref1: validated.ref1,
        ref2: validated.ref2,
        filesChanged: diff.summary.filesChanged,
        insertions: diff.summary.insertions,
        deletions: diff.summary.deletions,
        duration,
      });

      return result;
    } catch (error) {
      const duration = Date.now() - startTime;
      logger.error("Git diff failed", { error, input, duration });

      if (error instanceof Error) {
        if (
          error.message.includes("not a git repository") ||
          error.message.includes("Not a git repository") ||
          error.message.includes("not inside a work tree")
        ) {
          return "❌ **Not a git repository**\n\nThe current directory is not a git repository. Git diff is not available.";
        }
        if (error.message.includes("unknown revision")) {
          return `❌ **Invalid reference**\n\nThe git reference \`${input.ref1}\` or \`${input.ref2 || "HEAD"}\` is not valid.`;
        }
        if (error.message.includes("ambiguous argument")) {
          return `❌ **Ambiguous reference**\n\nThe reference is ambiguous. Please use full commit SHA or branch name.`;
        }
      }

      throw error;
    }
  }

  private formatDiff(diff: GitDiff, _options: GitDiffInput): string {
    let markdown = `# Git Diff\n\n`;
    markdown += `**Comparing:** \`${diff.ref1}\``;

    if (diff.ref2) {
      markdown += ` → \`${diff.ref2}\``;
    } else {
      markdown += ` → working directory`;
    }

    markdown += "\n\n";

    // Summary
    markdown += "## Summary\n\n";
    markdown += `- **Files Changed:** ${diff.summary.filesChanged}\n`;
    markdown += `- **Insertions:** +${diff.summary.insertions}\n`;
    markdown += `- **Deletions:** -${diff.summary.deletions}\n\n`;

    if (diff.files.length === 0) {
      markdown += "---\n\n*No changes found.*";
      return markdown;
    }

    // Files
    markdown += "## Files\n\n";

    for (const file of diff.files) {
      const changeIcon = this.getChangeIcon(file.changeType);
      markdown += `### ${changeIcon} ${file.filePath}\n\n`;

      if (file.isBinary) {
        markdown += "*Binary file*\n\n";
      } else {
        markdown += `**Changes:** +${file.additions} -${file.deletions}\n\n`;
      }

      markdown += "---\n\n";
    }

    // Tip
    if (diff.files.length > 10) {
      markdown +=
        "\n💡 *Tip: Use the `filePaths` parameter to filter by specific files.*\n";
    }

    return markdown;
  }

  private getChangeIcon(changeType: string): string {
    const icons: Record<string, string> = {
      added: "✨",
      modified: "📝",
      deleted: "🗑️",
      renamed: "🔄",
    };
    return icons[changeType] ?? "📄";
  }
}
