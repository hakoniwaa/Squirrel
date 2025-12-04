/**
 * Context Search Tool
 *
 * MCP tool for searching project context.
 * Now supports both:
 * - Code chunk search (semantic, function/class level)
 * - Discovery search (text-based, concept level)
 */

import { z } from "zod";
import {
  SearchContext,
  type ContextSearchResult,
} from "application/use-cases/SearchContext";
import type {
  SearchCodeChunks} from "application/use-cases/SearchCodeChunks";
import {
  type CodeChunkSearchResult,
} from "application/use-cases/SearchCodeChunks";
import { logger } from "../cli/logger";
import type { SessionManager } from "application/use-cases/SessionManager";

// Zod schema for input validation
export const ContextSearchSchema = z.object({
  query: z.string().min(1).describe("Search query text"),
  searchType: z
    .enum(["code", "discovery", "both"])
    .optional()
    .default("code")
    .describe(
      "Search type: 'code' for semantic code search, 'discovery' for concept search, 'both' for combined",
    ),
  type: z
    .enum(["module", "pattern", "rule", "issue", "discovery"])
    .optional()
    .describe("Filter by result type (for discovery search)"),
  chunkType: z
    .enum(["function", "class", "method", "interface", "type", "enum"])
    .optional()
    .describe("Filter by chunk type (for code search)"),
  filePath: z
    .string()
    .optional()
    .describe("Filter by file path (for code search)"),
  module: z.string().optional().describe("Filter by specific module name"),
  limit: z
    .number()
    .min(1)
    .max(20)
    .optional()
    .default(5)
    .describe("Maximum number of results (default: 5)"),
});

export type ContextSearchInput = z.infer<typeof ContextSearchSchema>;

export class ContextSearchTool {
  private projectPath: string;
  private searchCodeChunks: SearchCodeChunks | null = null;

  constructor(
    projectPath: string,
    searchCodeChunks?: SearchCodeChunks,
    _sessionManager?: SessionManager, // Reserved for future use when tracking search queries
  ) {
    this.projectPath = projectPath;
    this.searchCodeChunks = searchCodeChunks || null;
  }

  async execute(input: ContextSearchInput): Promise<string> {
    logger.info("Context search tool called", {
      query: input.query,
      searchType: input.searchType || "code",
      type: input.type,
      chunkType: input.chunkType,
    });

    try {
      // Validate input
      const validated = ContextSearchSchema.parse(input);

      const searchType = validated.searchType || "code";

      // Execute appropriate search based on searchType
      if (searchType === "code" && this.searchCodeChunks) {
        return await this.executeCodeSearch(validated);
      } else if (searchType === "discovery") {
        return await this.executeDiscoverySearch(validated);
      } else if (searchType === "both" && this.searchCodeChunks) {
        return await this.executeCombinedSearch(validated);
      } else {
        // Fallback to discovery search if code search not available
        return await this.executeDiscoverySearch(validated);
      }
    } catch (error) {
      logger.error("Context search failed", { error });
      throw error;
    }
  }

  /**
   * Execute code chunk semantic search
   */
  private async executeCodeSearch(input: ContextSearchInput): Promise<string> {
    if (!this.searchCodeChunks) {
      return "Code search is not available. Please initialize the chunking service.";
    }

    const results = await this.searchCodeChunks.execute({
      query: input.query,
      limit: input.limit,
      ...(input.filePath && { filePath: input.filePath }),
      ...(input.chunkType && { chunkType: input.chunkType }),
    });

    return this.formatCodeResults(results, input.query);
  }

  /**
   * Execute discovery/concept search
   */
  private async executeDiscoverySearch(
    input: ContextSearchInput,
  ): Promise<string> {
    const searchContext = new SearchContext(this.projectPath);
    const searchOptions = {
      query: input.query,
      limit: input.limit,
      ...(input.type !== undefined && { type: input.type }),
      ...(input.module !== undefined && { module: input.module }),
    };
    const results = await searchContext.execute(searchOptions);

    return this.formatDiscoveryResults(results, input.query);
  }

  /**
   * Execute both code and discovery search
   */
  private async executeCombinedSearch(
    input: ContextSearchInput,
  ): Promise<string> {
    const halfLimit = Math.ceil(input.limit / 2);

    const [codeResults, discoveryResults] = await Promise.all([
      this.searchCodeChunks!.execute({
        query: input.query,
        limit: halfLimit,
        ...(input.filePath && { filePath: input.filePath }),
        ...(input.chunkType && { chunkType: input.chunkType }),
      }),
      new SearchContext(this.projectPath).execute({
        query: input.query,
        limit: halfLimit,
        ...(input.type && { type: input.type }),
        ...(input.module && { module: input.module }),
      }),
    ]);

    let markdown = `# Combined Search Results for "${input.query}"\n\n`;

    if (codeResults.length > 0) {
      markdown += `## Code Chunks (${codeResults.length})\n\n`;
      markdown += this.formatCodeResults(codeResults, input.query, false);
      markdown += "\n---\n\n";
    }

    if (discoveryResults.length > 0) {
      markdown += `## Discoveries & Concepts (${discoveryResults.length})\n\n`;
      markdown += this.formatDiscoveryResults(
        discoveryResults,
        input.query,
        false,
      );
    }

    if (codeResults.length === 0 && discoveryResults.length === 0) {
      markdown += "No results found.\n";
    }

    return markdown;
  }

  /**
   * Format code chunk search results
   */
  private formatCodeResults(
    results: CodeChunkSearchResult[],
    query: string,
    includeHeader = true,
  ): string {
    if (results.length === 0) {
      return includeHeader
        ? `# Code Search Results for "${query}"\n\nNo code chunks found.`
        : "No code chunks found.";
    }

    let markdown = includeHeader
      ? `# Code Search Results for "${query}"\n\nFound ${results.length} code chunk${results.length === 1 ? "" : "s"}:\n\n`
      : "";

    for (let i = 0; i < results.length; i++) {
      const result = results[i];
      if (!result) continue;

      const { chunk, relevanceScore, snippet } = result;

      markdown += `### ${i + 1}. \`${chunk.name}\` (${chunk.type})\n\n`;
      markdown += `**Relevance**: ${Math.round(relevanceScore * 100)}%\n`;
      markdown += `**File**: \`${chunk.filePath}:${chunk.startLine}-${chunk.endLine}\`\n`;

      if (chunk.metadata.signature) {
        markdown += `**Signature**: \`${chunk.metadata.signature}\`\n`;
      }

      if (chunk.scopePath.length > 0) {
        markdown += `**Scope**: ${chunk.scopePath.join(" > ")}\n`;
      }

      if (chunk.metadata.jsDoc) {
        markdown += `\n${chunk.metadata.jsDoc}\n`;
      }

      markdown += `\n\`\`\`${this.getLanguageFromPath(chunk.filePath)}\n${snippet}\n\`\`\`\n\n`;

      if (i < results.length - 1) {
        markdown += "---\n\n";
      }
    }

    return markdown;
  }

  /**
   * Format discovery search results
   */
  private formatDiscoveryResults(
    results: ContextSearchResult[],
    query: string,
    includeHeader = true,
  ): string {
    if (results.length === 0) {
      return includeHeader
        ? `# Discovery Search Results for "${query}"\n\nNo results found.`
        : "No results found.";
    }

    let markdown = includeHeader
      ? `# Discovery Search Results for "${query}"\n\nFound ${results.length} result${results.length === 1 ? "" : "s"}:\n\n`
      : "";

    for (let i = 0; i < results.length; i++) {
      const result = results[i];
      if (!result) continue;

      markdown += `### ${i + 1}. ${this.formatType(result.type)}\n\n`;
      markdown += `**Relevance**: ${Math.round(result.relevanceScore * 100)}%\n`;
      markdown += `**Source**: ${result.source}\n`;

      if (result.metadata.module) {
        markdown += `**Module**: ${result.metadata.module}\n`;
      }

      if (result.metadata.sessionId) {
        markdown += `**Session**: ${result.metadata.sessionId}\n`;
      }

      if (result.metadata.discoveredAt) {
        markdown += `**Discovered**: ${result.metadata.discoveredAt.toISOString()}\n`;
      }

      markdown += `\n${result.content}\n\n`;

      if (i < results.length - 1) {
        markdown += "---\n\n";
      }
    }

    return markdown;
  }

  /**
   * Get file language from path for syntax highlighting
   */
  private getLanguageFromPath(filePath: string): string {
    const ext = filePath.split(".").pop()?.toLowerCase();
    const languageMap: Record<string, string> = {
      ts: "typescript",
      tsx: "tsx",
      js: "javascript",
      jsx: "jsx",
      py: "python",
      rb: "ruby",
      go: "go",
      rs: "rust",
      java: "java",
      cpp: "cpp",
      c: "c",
      cs: "csharp",
    };
    return languageMap[ext || ""] || "typescript";
  }

  private formatType(type: string): string {
    const typeMap: Record<string, string> = {
      module: "Module",
      pattern: "Pattern",
      rule: "Business Rule",
      issue: "Common Issue",
      discovery: "Discovery",
    };
    return typeMap[type] ?? type;
  }
}
