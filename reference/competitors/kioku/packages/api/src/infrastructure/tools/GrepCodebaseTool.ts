/**
 * Grep Codebase Tool
 *
 * MCP tool for searching files with regex patterns.
 */

import { z } from "zod";
import { readdirSync, statSync, readFileSync } from "fs";
import { join, relative, extname } from "path";
import { logger } from "../cli/logger";
import { minimatch } from "minimatch";
import type { SessionManager } from "application/use-cases/SessionManager";

// Zod schema for input validation
export const GrepCodebaseSchema = z.object({
  pattern: z.string().min(1).describe("Regex pattern to search for"),
  fileTypes: z
    .array(z.string())
    .optional()
    .describe("Filter by file extensions (e.g., ['ts', 'js'])"),
  glob: z.string().optional().describe("Glob pattern to filter files"),
  caseSensitive: z
    .boolean()
    .optional()
    .default(true)
    .describe("Case sensitive search"),
  contextLines: z
    .number()
    .optional()
    .default(0)
    .describe("Number of context lines to show around matches"),
  maxResults: z
    .number()
    .optional()
    .default(50)
    .describe("Maximum number of files to return"),
});

export type GrepCodebaseInput = z.infer<typeof GrepCodebaseSchema>;

interface Match {
  file: string;
  line: number;
  content: string;
  context?: string[];
}

export class GrepCodebaseTool {
  private projectPath: string;

  constructor(
    projectPath: string,
    _sessionManager?: SessionManager, // Reserved for future use when tracking grep patterns
  ) {
    this.projectPath = projectPath;
  }

  async execute(input: GrepCodebaseInput): Promise<string> {
    logger.info("Grep codebase tool called", {
      pattern: input.pattern,
      fileTypes: input.fileTypes,
      glob: input.glob,
    });

    try {
      // Validate input
      const validated = GrepCodebaseSchema.parse(input);
      const {
        pattern,
        fileTypes,
        glob,
        caseSensitive,
        contextLines,
        maxResults,
      } = validated;

      // Create regex
      const flags = caseSensitive ? "g" : "gi";
      const regex = new RegExp(pattern, flags);

      // Search files
      const matches = this.searchFiles(
        this.projectPath,
        regex,
        fileTypes,
        glob,
        contextLines,
        maxResults,
      );

      // Format output
      return this.formatOutput(pattern, matches, maxResults);
    } catch (error) {
      logger.error("Grep failed", { error });
      throw error;
    }
  }

  private searchFiles(
    dir: string,
    regex: RegExp,
    fileTypes?: string[],
    globPattern?: string,
    contextLines = 0,
    maxResults = 50,
  ): Match[] {
    const matches: Match[] = [];
    const filesToSearch = this.getFiles(dir);

    for (const file of filesToSearch) {
      if (matches.length >= maxResults) break;

      // Skip node_modules
      if (file.includes("node_modules")) continue;

      // Apply file type filter
      if (fileTypes && fileTypes.length > 0) {
        const ext = extname(file).slice(1);
        if (!fileTypes.includes(ext)) continue;
      }

      // Apply glob filter
      if (globPattern) {
        const relativePath = relative(dir, file);
        if (!minimatch(relativePath, globPattern)) continue;
      }

      // Search file
      try {
        const content = readFileSync(file, "utf-8");
        const lines = content.split("\n");

        for (let i = 0; i < lines.length; i++) {
          if (matches.length >= maxResults) break;

          const line = lines[i];
          if (line && regex.test(line)) {
            let matchContext: string[] | undefined;

            if (contextLines > 0) {
              const context: string[] = [];
              // Add context before
              for (let j = Math.max(0, i - contextLines); j < i; j++) {
                const contextLine = lines[j];
                if (contextLine) context.push(contextLine);
              }
              if (context.length > 0) {
                matchContext = context;
              }
            }

            const match: Match = {
              file: relative(dir, file),
              line: i + 1,
              content: line.trim(),
            };

            if (matchContext !== undefined) {
              match.context = matchContext;
            }

            matches.push(match);
          }
        }
      } catch {
        // Skip files that can't be read
        continue;
      }
    }

    return matches;
  }

  private getFiles(dir: string): string[] {
    const files: string[] = [];

    try {
      const entries = readdirSync(dir);

      for (const entry of entries) {
        const fullPath = join(dir, entry);

        try {
          const stat = statSync(fullPath);

          if (stat.isDirectory()) {
            // Skip hidden directories and node_modules
            if (entry.startsWith(".") || entry === "node_modules") continue;
            files.push(...this.getFiles(fullPath));
          } else if (stat.isFile()) {
            files.push(fullPath);
          }
        } catch {
          // Skip files/dirs that can't be accessed
          continue;
        }
      }
    } catch {
      // Skip directories that can't be read
    }

    return files;
  }

  private formatOutput(
    pattern: string,
    matches: Match[],
    maxResults: number,
  ): string {
    if (matches.length === 0) {
      return `# Grep Results

**Pattern:** \`${pattern}\`

No matches found.`;
    }

    const truncated = matches.length >= maxResults;
    const fileCount = new Set(matches.map((m) => m.file)).size;

    let output = `# Grep Results

**Pattern:** \`${pattern}\`
**Files Found:** ${fileCount}
**Total Matches:** ${matches.length}${truncated ? ` (limited to ${maxResults})` : ""}

---

`;

    // Group by file
    const byFile = new Map<string, Match[]>();
    for (const match of matches) {
      const existing = byFile.get(match.file) || [];
      existing.push(match);
      byFile.set(match.file, existing);
    }

    // Format each file
    for (const [file, fileMatches] of byFile) {
      output += `## \`${file}\`\n\n`;
      output += `${fileMatches.length} match${fileMatches.length > 1 ? "es" : ""}\n\n`;

      for (const match of fileMatches) {
        output += `**Line ${match.line}:**\n\n`;

        if (match.context && match.context.length > 0) {
          for (const ctx of match.context) {
            output += `\`\`\`\n${ctx}\n\`\`\`\n\n`;
          }
        }

        output += `\`\`\`\n${match.content}\n\`\`\`\n\n`;
      }

      output += "---\n\n";
    }

    return output.trim();
  }
}
