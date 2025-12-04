/**
 * Extract Discoveries Use Case
 *
 * Extracts learnings (patterns, rules, decisions, issues) from session conversations.
 */

// eslint-disable-next-line boundaries/element-types -- MVP: Direct infrastructure usage, will refactor to ports/adapters pattern post-MVP
import { logger } from "../../infrastructure/cli/logger";

export interface Discovery {
  id?: string;
  sessionId: string;
  type: "pattern" | "rule" | "decision" | "issue";
  content: string;
  module?: string;
  createdAt: Date;
}

interface ExtractionPattern {
  type: Discovery["type"];
  regex: RegExp;
  description: string;
}

export class ExtractDiscoveries {
  private patterns: ExtractionPattern[] = [
    // Patterns: "we use X for Y", "X stores Y in Z"
    {
      type: "pattern",
      regex: /we use [\w\s]+ for [\w\s]+/gi,
      description: "Usage patterns",
    },
    {
      type: "pattern",
      regex: /(?:the system|it|we) stores? [\w\s]+ in [\w\s]+/gi,
      description: "Storage patterns",
    },
    {
      type: "pattern",
      regex: /(?:using|implemented|built with) [\w\s]+ (?:for|to) [\w\s]+/gi,
      description: "Implementation patterns",
    },

    // Business rules: "must always", "must never", "should always"
    {
      type: "rule",
      regex: /[\w\s]+ must (?:always|never) [\w\s]+/gi,
      description: "Must rules",
    },
    {
      type: "rule",
      regex: /[\w\s]+ should (?:always|never) [\w\s]+/gi,
      description: "Should rules",
    },

    // Decisions: "decided to", "chose to", "switched to"
    {
      type: "decision",
      regex: /(?:we |team )?(?:decided|chose) to [\w\s]+/gi,
      description: "Decisions made",
    },
    {
      type: "decision",
      regex: /switched (?:from [\w\s]+ )?to [\w\s]+/gi,
      description: "Technology switches",
    },

    // Issues: "fixed", "resolved", "bug with"
    {
      type: "issue",
      regex: /(?:fixed|resolved) (?:the |a )?[\w\s]+ (?:by|with|in) [\w\s]+/gi,
      description: "Fixed issues",
    },
    {
      type: "issue",
      regex:
        /bug (?:with|in) [\w\s]+,?\s*(?:fixed|resolved) (?:by|with) [\w\s]+/gi,
      description: "Bugs and fixes",
    },
  ];

  execute(sessionId: string, messages: string[]): Discovery[] {
    logger.info("Extracting discoveries", {
      sessionId,
      messageCount: messages.length,
    });

    if (messages.length === 0) {
      return [];
    }

    const discoveries: Discovery[] = [];
    const seen = new Set<string>(); // For deduplication

    // Join all messages for pattern matching
    const fullText = messages.join(" ");

    // Apply each pattern
    for (const pattern of this.patterns) {
      const matches = fullText.match(pattern.regex);
      if (matches) {
        for (const match of matches) {
          // Normalize for deduplication (lowercase, trim)
          const normalized = match.toLowerCase().trim();

          // Skip if we've seen something very similar
          if (this.isDuplicate(normalized, seen)) {
            continue;
          }

          seen.add(normalized);

          // Detect module from context
          const module = this.detectModule(match, fullText);

          const discovery: Discovery = {
            sessionId,
            type: pattern.type,
            content: match.trim(),
            createdAt: new Date(),
          };

          if (module !== undefined) {
            discovery.module = module;
          }

          discoveries.push(discovery);
        }
      }
    }

    // Limit to 10 discoveries per session (prioritize by type)
    const limited = this.limitDiscoveries(discoveries, 10);

    logger.info("Discoveries extracted", {
      sessionId,
      count: limited.length,
      byType: this.countByType(limited),
    });

    return limited;
  }

  private isDuplicate(normalized: string, seen: Set<string>): boolean {
    // Check exact match
    if (seen.has(normalized)) {
      return true;
    }

    // Check similarity (simple: if 80% of words match)
    const words = normalized.split(/\s+/);
    for (const existing of seen) {
      const existingWords = existing.split(/\s+/);
      const commonWords = words.filter((w) => existingWords.includes(w));
      const similarity =
        commonWords.length / Math.max(words.length, existingWords.length);

      if (similarity > 0.8) {
        return true;
      }
    }

    return false;
  }

  private detectModule(_match: string, fullText: string): string | undefined {
    // Look for file paths in the surrounding context
    const filePathMatch = fullText.match(
      /src\/(\w+)\/[\w/]+\.(ts|js|tsx|jsx)/i,
    );
    if (filePathMatch) {
      return filePathMatch[1];
    }

    // Look for explicit module mentions in full text
    const moduleMatch = fullText.match(/(?:in|for) the (\w+) module/i);
    if (moduleMatch) {
      return moduleMatch[1];
    }

    return undefined;
  }

  private limitDiscoveries(
    discoveries: Discovery[],
    limit: number,
  ): Discovery[] {
    // Priority: issues > decisions > rules > patterns
    const priorityOrder: Record<Discovery["type"], number> = {
      issue: 0,
      decision: 1,
      rule: 2,
      pattern: 3,
    };

    return discoveries
      .sort((a, b) => priorityOrder[a.type] - priorityOrder[b.type])
      .slice(0, limit);
  }

  private countByType(discoveries: Discovery[]): Record<string, number> {
    const counts: Record<string, number> = {
      pattern: 0,
      rule: 0,
      decision: 0,
      issue: 0,
    };

    for (const discovery of discoveries) {
      const currentCount = counts[discovery.type];
      if (currentCount !== undefined) {
        counts[discovery.type] = currentCount + 1;
      }
    }

    return counts;
  }
}
