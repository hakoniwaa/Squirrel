import { parse, stringify } from "yaml";
import { readFileSync, writeFileSync, existsSync, copyFileSync } from "fs";
import { z } from "zod";
import type { ProjectContext } from "domain/models/ProjectContext";
import { StorageError, ValidationError } from "@kioku/shared";
import { logger } from "../cli/logger";

// Zod validation schemas
const KeyFileSchema = z.object({
  path: z.string().min(1),
  role: z.enum(["entry", "config", "core", "test"]),
  description: z.string().optional(),
});

const IssueSchema = z.object({
  description: z.string().min(1),
  solution: z.string().min(1),
  sessionId: z.string().min(1),
  discoveredAt: z.string().datetime(),
});

const ModuleContextSchema = z.object({
  name: z.string().min(1),
  description: z.string(),
  keyFiles: z.array(KeyFileSchema),
  patterns: z.array(z.string()),
  businessRules: z.array(z.string()),
  commonIssues: z.array(IssueSchema),
  dependencies: z.array(z.string()),
});

const ProjectContextSchema = z.object({
  version: z.string(),
  project: z.object({
    name: z.string().min(1),
    type: z.enum(["web-app", "api", "cli", "library", "fullstack"]),
    path: z.string().min(1),
  }),
  tech: z.object({
    stack: z.array(z.string()),
    runtime: z.string(),
    packageManager: z.enum(["npm", "yarn", "pnpm", "bun"]),
  }),
  architecture: z.object({
    pattern: z.enum([
      "feature-based",
      "layered",
      "modular",
      "monorepo",
      "unknown",
    ]),
    description: z.string(),
  }),
  modules: z.record(z.string(), ModuleContextSchema),
  metadata: z.object({
    createdAt: z.string().datetime(),
    updatedAt: z.string().datetime(),
    lastScanAt: z.string().datetime(),
  }),
});

// eslint-disable-next-line @typescript-eslint/no-extraneous-class
export class YAMLHandler {
  /**
   * Load and validate project.yaml
   */
  static loadProjectContext(filePath: string): ProjectContext {
    try {
      if (!existsSync(filePath)) {
        throw new StorageError(`Project context file not found: ${filePath}`);
      }

      const content = readFileSync(filePath, "utf-8");
      const parsed = parse(content);

      // Validate with Zod
      const validated = ProjectContextSchema.parse(parsed);

      // Convert date strings to Date objects
      const context: ProjectContext = {
        ...validated,
        metadata: {
          createdAt: new Date(validated.metadata.createdAt),
          updatedAt: new Date(validated.metadata.updatedAt),
          lastScanAt: new Date(validated.metadata.lastScanAt),
        },
        modules: Object.fromEntries(
          Object.entries(validated.modules).map(([key, module]) => [
            key,
            {
              ...module,
              keyFiles: module.keyFiles.map((kf) => {
                const keyFile: {
                  path: string;
                  role: typeof kf.role;
                  description?: string;
                } = {
                  path: kf.path,
                  role: kf.role,
                };
                if (kf.description) {
                  keyFile.description = kf.description;
                }
                return keyFile;
              }),
              commonIssues: module.commonIssues.map((issue) => ({
                description: issue.description,
                solution: issue.solution,
                sessionId: issue.sessionId,
                discoveredAt: new Date(issue.discoveredAt),
              })),
            },
          ]),
        ),
      };

      logger.debug("Project context loaded", { filePath });
      return context;
    } catch (error) {
      if (error instanceof z.ZodError) {
        throw new ValidationError(`Invalid project.yaml: ${error.message}`);
      }
      throw new StorageError("Failed to load project context", error as Error);
    }
  }

  /**
   * Save project context with atomic write (backup before save)
   */
  static saveProjectContext(context: ProjectContext, filePath: string): void {
    try {
      // Create backup if file exists
      const backupPath = `${filePath}.backup`;
      if (existsSync(filePath)) {
        copyFileSync(filePath, backupPath);
        logger.debug("Created backup", { backupPath });
      }

      // Convert dates to ISO strings for YAML
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      const contextForYAML: any = {
        version: context.version,
        project: context.project,
        tech: context.tech,
        architecture: context.architecture,
        metadata: {
          createdAt: context.metadata.createdAt.toISOString(),
          updatedAt: context.metadata.updatedAt.toISOString(),
          lastScanAt: context.metadata.lastScanAt.toISOString(),
        },
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        modules: {} as Record<string, any>,
      };

      // Convert modules with proper date handling
      for (const [key, module] of Object.entries(context.modules)) {
        contextForYAML.modules[key] = {
          name: module.name,
          description: module.description,
          keyFiles: module.keyFiles,
          patterns: module.patterns,
          businessRules: module.businessRules,
          commonIssues: module.commonIssues.map((issue) => ({
            description: issue.description,
            solution: issue.solution,
            sessionId: issue.sessionId,
            discoveredAt: issue.discoveredAt.toISOString(),
          })),
          dependencies: module.dependencies,
        };
      }

      // Validate before saving
      ProjectContextSchema.parse(contextForYAML);

      // Convert to YAML and save
      const yaml = stringify(contextForYAML);
      writeFileSync(filePath, yaml, "utf-8");

      logger.info("Project context saved", { filePath });
    } catch (error) {
      // Restore from backup if save failed
      const backupPath = `${filePath}.backup`;
      if (existsSync(backupPath)) {
        try {
          copyFileSync(backupPath, filePath);
          logger.warn("Restored from backup after failed save", { filePath });
        } catch (restoreError) {
          logger.error("Failed to restore from backup", {
            error: restoreError,
          });
        }
      }

      if (error instanceof z.ZodError) {
        throw new ValidationError(`Invalid project context: ${error.message}`);
      }
      throw new StorageError("Failed to save project context", error as Error);
    }
  }
}
