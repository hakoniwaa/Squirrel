/**
 * Enrich Context Use Case
 *
 * Enriches project context by adding discoveries to relevant modules.
 */

 
import { YAMLHandler } from "infrastructure/storage/yaml-handler";
// eslint-disable-next-line boundaries/element-types -- MVP: Direct infrastructure usage, will refactor to ports/adapters pattern post-MVP
import { logger } from "../../infrastructure/cli/logger";
import { join } from "path";
import type {
  ProjectContext,
  ModuleContext,
} from "domain/models/ProjectContext";
import type { Discovery } from "./ExtractDiscoveries";

export class EnrichContext {
  private projectPath: string;

  constructor(projectPath: string) {
    this.projectPath = projectPath;
  }

  async execute(discoveries: Discovery[]): Promise<void> {
    logger.info("Enriching project context", {
      discoveryCount: discoveries.length,
    });

    if (discoveries.length === 0) {
      logger.info("No discoveries to enrich");
      return;
    }

    // Load current project context
    const yamlPath = join(this.projectPath, ".context", "project.yaml");
    let context: ProjectContext;

    try {
      context = YAMLHandler.loadProjectContext(yamlPath);
    } catch (error) {
      logger.error("Failed to load project context", { error });
      throw error;
    }

    let changeCount = 0;

    // Process each discovery
    for (const discovery of discoveries) {
      // Skip discoveries without module
      if (!discovery.module) {
        logger.debug("Skipping discovery without module", {
          type: discovery.type,
          content: discovery.content.substring(0, 50),
        });
        continue;
      }

      // Get or create module
      let module = context.modules[discovery.module];
      if (!module) {
        logger.info("Creating new module", { moduleName: discovery.module });
        module = this.createModule(discovery.module);
        context.modules[discovery.module] = module;
      }

      // Add discovery to module based on type
      const added = this.addDiscoveryToModule(module, discovery);
      if (added) {
        changeCount++;
      }
    }

    // Update metadata
    context.metadata.updatedAt = new Date();

    // Save updated context
    try {
      YAMLHandler.saveProjectContext(context, yamlPath);
      logger.info("Context enriched", {
        changesApplied: changeCount,
        totalDiscoveries: discoveries.length,
      });
    } catch (error) {
      logger.error("Failed to save enriched context", { error });
      throw error;
    }
  }

  private createModule(name: string): ModuleContext {
    return {
      name,
      description: `${name} module`,
      keyFiles: [],
      patterns: [],
      businessRules: [],
      commonIssues: [],
      dependencies: [],
    };
  }

  private addDiscoveryToModule(
    module: ModuleContext,
    discovery: Discovery,
  ): boolean {
    switch (discovery.type) {
      case "pattern":
        return this.addPattern(module, discovery.content);

      case "rule":
        return this.addBusinessRule(module, discovery.content);

      case "issue":
        return this.addIssue(module, discovery);

      case "decision":
        // Decisions can be treated as patterns
        return this.addPattern(module, discovery.content);

      default:
        logger.warn("Unknown discovery type", { type: discovery.type });
        return false;
    }
  }

  private addPattern(module: ModuleContext, content: string): boolean {
    // Check for duplicates
    if (this.isDuplicate(module.patterns, content)) {
      logger.debug("Skipping duplicate pattern", {
        content: content.substring(0, 50),
      });
      return false;
    }

    module.patterns.push(content);
    logger.debug("Added pattern", { content: content.substring(0, 50) });
    return true;
  }

  private addBusinessRule(module: ModuleContext, content: string): boolean {
    // Check for duplicates
    if (this.isDuplicate(module.businessRules, content)) {
      logger.debug("Skipping duplicate business rule", {
        content: content.substring(0, 50),
      });
      return false;
    }

    module.businessRules.push(content);
    logger.debug("Added business rule", { content: content.substring(0, 50) });
    return true;
  }

  private addIssue(module: ModuleContext, discovery: Discovery): boolean {
    // Parse issue content to extract description and solution
    const { description, solution } = this.parseIssueContent(discovery.content);

    // Check for duplicate issues
    const isDupe = module.commonIssues.some(
      (issue) =>
        this.isSimilar(issue.description, description) ||
        (issue.solution && this.isSimilar(issue.solution, solution)),
    );

    if (isDupe) {
      logger.debug("Skipping duplicate issue", {
        description: description.substring(0, 50),
      });
      return false;
    }

    module.commonIssues.push({
      description,
      solution,
      sessionId: discovery.sessionId,
      discoveredAt: discovery.createdAt,
    });

    logger.debug("Added issue", { description: description.substring(0, 50) });
    return true;
  }

  private parseIssueContent(content: string): {
    description: string;
    solution: string;
  } {
    // Try to split by "fixed by", "resolved by", "resolved with", etc.
    const splitPatterns = [
      / (?:fixed|resolved) (?:by|with) /i,
      /, (?:fixed|resolved) (?:by|with) /i,
    ];

    for (const pattern of splitPatterns) {
      const parts = content.split(pattern);
      if (parts.length === 2 && parts[0] && parts[1]) {
        return {
          description: parts[0].trim(),
          solution: parts[1].trim(),
        };
      }
    }

    // If no clear split, use entire content as description
    return {
      description: content,
      solution: "See session for details",
    };
  }

  private isDuplicate(existing: string[], content: string): boolean {
    const normalized = content.toLowerCase().trim();

    for (const item of existing) {
      if (this.isSimilar(item, normalized)) {
        return true;
      }
    }

    return false;
  }

  private isSimilar(a: string, b: string): boolean {
    const aNorm = a.toLowerCase().trim();
    const bNorm = b.toLowerCase().trim();

    // Exact match
    if (aNorm === bNorm) {
      return true;
    }

    // Check if 80% of words match
    const aWords = aNorm.split(/\s+/);
    const bWords = bNorm.split(/\s+/);
    const commonWords = aWords.filter((w) => bWords.includes(w));
    const similarity =
      commonWords.length / Math.max(aWords.length, bWords.length);

    return similarity > 0.8;
  }
}
