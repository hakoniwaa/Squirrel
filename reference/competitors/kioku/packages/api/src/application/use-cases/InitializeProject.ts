/**
 * Initialize Project Use Case
 *
 * Scans project directory, detects tech stack, identifies modules,
 * and creates initial project context.
 */

import { existsSync, readFileSync, readdirSync, statSync, mkdirSync } from "fs";
import { join, basename } from "path";
import type {
  ProjectContext,
  ModuleContext,
} from "domain/models/ProjectContext";
 
import { YAMLHandler } from "infrastructure/storage/yaml-handler";
 
import { SQLiteAdapter } from "infrastructure/storage/sqlite-adapter";

export class InitializeProject {
  async execute(projectPath: string): Promise<ProjectContext> {
    // Ensure .context directory exists
    const contextDir = join(projectPath, ".context");
    if (!existsSync(contextDir)) {
      mkdirSync(contextDir, { recursive: true });
    }

    // Scan project structure
    const context = await this.scanProject(projectPath);

    // Save to .context/project.yaml
    const yamlPath = join(contextDir, "project.yaml");
    YAMLHandler.saveProjectContext(context, yamlPath);

    // Initialize SQLite database (constructor initializes tables automatically)
    const dbPath = join(contextDir, "sessions.db");
    new SQLiteAdapter(dbPath);

    // Note: Chroma collection will be initialized on first search (lazy initialization)

    return context;
  }

  private async scanProject(projectPath: string): Promise<ProjectContext> {
    const now = new Date();

    // Read package.json if exists
    const packageJsonPath = join(projectPath, "package.json");
    let packageJson: Record<string, unknown> | undefined;
    if (existsSync(packageJsonPath)) {
      packageJson = JSON.parse(
        readFileSync(packageJsonPath, "utf-8"),
      ) as Record<string, unknown>;
    }

    // Detect project name
    const projectName =
      (packageJson?.name as string | undefined) ?? basename(projectPath);

    // Detect tech stack
    const techStack = this.detectTechStack(packageJson);

    // Detect package manager
    const packageManager = this.detectPackageManager(projectPath);

    // Detect runtime
    const runtime = this.detectRuntime(packageJson);

    // Infer project type
    const projectType = this.inferProjectType(packageJson);

    // Infer architecture pattern
    const architecture = this.inferArchitecture(projectPath);

    // Identify modules
    const modules = this.identifyModules(projectPath);

    return {
      version: "1.0",
      project: {
        name: projectName,
        type: projectType,
        path: projectPath,
      },
      tech: {
        stack: techStack,
        runtime,
        packageManager,
      },
      architecture,
      modules,
      metadata: {
        createdAt: now,
        updatedAt: now,
        lastScanAt: now,
      },
    };
  }

  private detectTechStack(packageJson?: Record<string, unknown>): string[] {
    const stack: string[] = [];

    if (!packageJson) {
      return stack;
    }

    const dependencies = {
      ...(packageJson.dependencies as Record<string, string> | undefined),
      ...(packageJson.devDependencies as Record<string, string> | undefined),
    };

    // Detect frameworks and libraries
    if (dependencies["next"]) stack.push("Next.js");
    if (dependencies["react"]) stack.push("React");
    if (dependencies["vue"]) stack.push("Vue");
    if (dependencies["express"]) stack.push("Express");
    if (dependencies["fastify"]) stack.push("Fastify");
    if (dependencies["typescript"]) stack.push("TypeScript");
    if (dependencies["tailwindcss"]) stack.push("Tailwind CSS");
    if (dependencies["prisma"]) stack.push("Prisma");
    if (dependencies["drizzle-orm"]) stack.push("Drizzle ORM");

    return stack;
  }

  private detectPackageManager(
    projectPath: string,
  ): "npm" | "yarn" | "pnpm" | "bun" {
    if (existsSync(join(projectPath, "bun.lockb"))) return "bun";
    if (existsSync(join(projectPath, "pnpm-lock.yaml"))) return "pnpm";
    if (existsSync(join(projectPath, "yarn.lock"))) return "yarn";
    return "npm";
  }

  private detectRuntime(packageJson?: Record<string, unknown>): string {
    if (!packageJson) {
      return "node";
    }

    const dependencies = {
      ...(packageJson.dependencies as Record<string, string> | undefined),
      ...(packageJson.devDependencies as Record<string, string> | undefined),
    };

    if (dependencies["bun-types"] !== undefined) return "bun";
    if (dependencies["deno"] !== undefined) return "deno";
    return "node";
  }

  private inferProjectType(
    packageJson?: Record<string, unknown>,
  ): "web-app" | "api" | "cli" | "library" | "fullstack" {
    if (!packageJson) {
      return "library";
    }

    const dependencies = {
      ...(packageJson.dependencies as Record<string, string> | undefined),
      ...(packageJson.devDependencies as Record<string, string> | undefined),
    };

    // CLI if has bin field
    if (packageJson.bin !== undefined) return "cli";

    // Fullstack if has both frontend and backend frameworks
    const hasFrontend =
      dependencies["react"] !== undefined ||
      dependencies["vue"] !== undefined ||
      dependencies["next"] !== undefined;
    const hasBackend =
      dependencies["express"] !== undefined ||
      dependencies["fastify"] !== undefined;
    if (hasFrontend && hasBackend) return "fullstack";

    // Web app if has frontend framework
    if (hasFrontend) return "web-app";

    // API if has backend framework
    if (hasBackend) return "api";

    return "library";
  }

  private inferArchitecture(projectPath: string): {
    pattern: "feature-based" | "layered" | "modular" | "monorepo" | "unknown";
    description: string;
  } {
    const srcPath = join(projectPath, "src");

    if (!existsSync(srcPath)) {
      return {
        pattern: "unknown",
        description: "No src/ directory found",
      };
    }

    const srcDirs = readdirSync(srcPath).filter((item) => {
      const itemPath = join(srcPath, item);
      return statSync(itemPath).isDirectory();
    });

    // Check for onion/layered architecture
    const hasLayers =
      srcDirs.includes("domain") &&
      srcDirs.includes("application") &&
      srcDirs.includes("infrastructure");
    if (hasLayers) {
      return {
        pattern: "layered",
        description:
          "Onion/Clean Architecture with domain, application, and infrastructure layers",
      };
    }

    // Check for feature-based
    const hasFeatures =
      srcDirs.includes("features") ||
      srcDirs.some((dir) => dir.startsWith("feature-"));
    if (hasFeatures) {
      return {
        pattern: "feature-based",
        description: "Feature-based architecture with modular features",
      };
    }

    // Check for monorepo
    const hasPackages = existsSync(join(projectPath, "packages"));
    if (hasPackages) {
      return {
        pattern: "monorepo",
        description: "Monorepo with multiple packages",
      };
    }

    return {
      pattern: "modular",
      description: `Modular structure with ${srcDirs.length} top-level directories`,
    };
  }

  private identifyModules(projectPath: string): Record<string, ModuleContext> {
    const modules: Record<string, ModuleContext> = {};
    const srcPath = join(projectPath, "src");

    if (!existsSync(srcPath)) {
      return modules;
    }

    const srcDirs = readdirSync(srcPath).filter((item) => {
      const itemPath = join(srcPath, item);
      return statSync(itemPath).isDirectory();
    });

    // Create module for each top-level directory
    for (const dir of srcDirs) {
      modules[dir] = {
        name: dir,
        description: `${dir} module`,
        keyFiles: this.findKeyFiles(join(srcPath, dir)),
        patterns: [],
        businessRules: [],
        commonIssues: [],
        dependencies: [],
      };
    }

    return modules;
  }

  private findKeyFiles(modulePath: string): {
    path: string;
    role: "entry" | "config" | "core" | "test";
    description?: string;
  }[] {
    const keyFiles: {
      path: string;
      role: "entry" | "config" | "core" | "test";
      description?: string;
    }[] = [];

    if (!existsSync(modulePath)) {
      return keyFiles;
    }

    try {
      const files = readdirSync(modulePath);

      for (const file of files) {
        const filePath = join(modulePath, file);

        if (!statSync(filePath).isFile()) continue;

        // Identify entry points
        if (file === "index.ts" || file === "index.js") {
          keyFiles.push({
            path: filePath,
            role: "entry",
            description: "Module entry point",
          });
        }

        // Identify config files
        if (file.includes("config") || file.includes("settings")) {
          keyFiles.push({
            path: filePath,
            role: "config",
            description: "Configuration file",
          });
        }

        // Identify test files
        if (file.includes(".test.") || file.includes(".spec.")) {
          keyFiles.push({
            path: filePath,
            role: "test",
            description: "Test file",
          });
        }
      }
    } catch {
      // Ignore errors reading directory
    }

    return keyFiles;
  }
}
