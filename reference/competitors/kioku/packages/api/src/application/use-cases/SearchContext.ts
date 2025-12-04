/**
 * Search Context Use Case
 *
 * Searches project context using text-based search.
 * For MVP: Simple text search in project.yaml and discoveries.
 * Future: Will add semantic search with embeddings.
 */

 
import { SQLiteAdapter } from "infrastructure/storage/sqlite-adapter";
 
import { YAMLHandler } from "infrastructure/storage/yaml-handler";
// eslint-disable-next-line boundaries/element-types -- MVP: Direct infrastructure usage, will refactor to ports/adapters pattern post-MVP
import { logger } from "../../infrastructure/cli/logger";
import { join } from "path";
import type { ProjectContext } from "domain/models/ProjectContext";

export interface ContextSearchResult {
  content: string;
  source: string;
  type: "module" | "pattern" | "rule" | "issue" | "discovery";
  relevanceScore: number;
  metadata: {
    module?: string;
    sessionId?: string;
    discoveredAt?: Date;
  };
}

export interface SearchOptions {
  query: string;
  type?: "module" | "pattern" | "rule" | "issue" | "discovery";
  module?: string;
  limit?: number;
}

export class SearchContext {
  private projectPath: string;
  private sqliteAdapter: SQLiteAdapter | null = null;

  constructor(projectPath: string) {
    this.projectPath = projectPath;
  }

  async execute(options: SearchOptions): Promise<ContextSearchResult[]> {
    const { query, type, module, limit = 5 } = options;

    logger.info("Searching context", { query, type, module, limit });

    // Use text search for MVP
    const searchOptions: Omit<SearchOptions, "query"> = {
      limit,
      ...(type !== undefined && { type }),
      ...(module !== undefined && { module }),
    };
    const results = await this.textSearch(query, searchOptions);

    logger.info("Search completed", {
      query,
      resultsCount: results.length,
    });

    return results;
  }

  private async textSearch(
    query: string,
    options: Omit<SearchOptions, "query">,
  ): Promise<ContextSearchResult[]> {
    const results: ContextSearchResult[] = [];
    const queryLower = query.toLowerCase();

    // Load project context
    const yamlPath = join(this.projectPath, ".context", "project.yaml");
    let projectContext: ProjectContext;

    try {
      projectContext = YAMLHandler.loadProjectContext(yamlPath);
    } catch {
      logger.warn("Could not load project context for text search");
      return [];
    }

    // Search in modules
    for (const [moduleName, moduleContext] of Object.entries(
      projectContext.modules,
    )) {
      // Skip if module filter specified and doesn't match
      if (options.module && moduleName !== options.module) {
        continue;
      }

      // Search patterns
      if (!options.type || options.type === "pattern") {
        for (const pattern of moduleContext.patterns) {
          if (pattern.toLowerCase().includes(queryLower)) {
            results.push({
              content: pattern,
              source: `module:${moduleName}/patterns`,
              type: "pattern",
              relevanceScore: this.calculateTextRelevance(pattern, queryLower),
              metadata: { module: moduleName },
            });
          }
        }
      }

      // Search business rules
      if (!options.type || options.type === "rule") {
        for (const rule of moduleContext.businessRules) {
          if (rule.toLowerCase().includes(queryLower)) {
            results.push({
              content: rule,
              source: `module:${moduleName}/rules`,
              type: "rule",
              relevanceScore: this.calculateTextRelevance(rule, queryLower),
              metadata: { module: moduleName },
            });
          }
        }
      }

      // Search common issues
      if (!options.type || options.type === "issue") {
        for (const issue of moduleContext.commonIssues) {
          const searchText =
            `${issue.description} ${issue.solution}`.toLowerCase();
          if (searchText.includes(queryLower)) {
            results.push({
              content: `${issue.description}\nSolution: ${issue.solution}`,
              source: `module:${moduleName}/issues`,
              type: "issue",
              relevanceScore: this.calculateTextRelevance(
                searchText,
                queryLower,
              ),
              metadata: {
                module: moduleName,
                ...(issue.sessionId !== undefined && {
                  sessionId: issue.sessionId,
                }),
                ...(issue.discoveredAt !== undefined && {
                  discoveredAt: issue.discoveredAt,
                }),
              },
            });
          }
        }
      }
    }

    // Search discoveries from database
    if (!options.type || options.type === "discovery") {
      if (!this.sqliteAdapter) {
        const dbPath = join(this.projectPath, ".context", "sessions.db");
        this.sqliteAdapter = new SQLiteAdapter(dbPath);
      }

      const discoveries = this.sqliteAdapter.getAllDiscoveries();
      for (const discovery of discoveries) {
        if (discovery.content.toLowerCase().includes(queryLower)) {
          results.push({
            content: discovery.content,
            source: `discovery:${discovery.id}`,
            type: "discovery",
            relevanceScore: this.calculateTextRelevance(
              discovery.content,
              queryLower,
            ),
            metadata: {
              ...(discovery.module !== undefined && {
                module: discovery.module,
              }),
              ...(discovery.sessionId !== undefined && {
                sessionId: discovery.sessionId,
              }),
              ...(discovery.createdAt !== undefined && {
                discoveredAt: discovery.createdAt,
              }),
            },
          });
        }
      }
    }

    // Sort by relevance and limit
    results.sort((a, b) => b.relevanceScore - a.relevanceScore);
    return results.slice(0, options.limit ?? 5);
  }

  private calculateTextRelevance(text: string, query: string): number {
    const textLower = text.toLowerCase();

    // Exact match gets highest score
    if (textLower === query) {
      return 1.0;
    }

    // Contains as whole word
    const wordMatch = new RegExp(`\\b${this.escapeRegex(query)}\\b`, "i");
    if (wordMatch.test(text)) {
      return 0.8;
    }

    // Contains substring
    if (textLower.includes(query)) {
      return 0.6;
    }

    // Fuzzy match (shared words)
    const queryWords = query.split(/\s+/);
    const textWords = textLower.split(/\s+/);
    const matchingWords = queryWords.filter((word) =>
      textWords.some((textWord) => textWord.includes(word)),
    );

    return (matchingWords.length / queryWords.length) * 0.4;
  }

  private escapeRegex(str: string): string {
    return str.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  }
}
