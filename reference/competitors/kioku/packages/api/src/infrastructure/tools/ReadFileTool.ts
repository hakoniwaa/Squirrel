/**
 * Read File Tool
 *
 * MCP tool for reading files with optional dependency loading.
 */

import { z } from "zod";
import { readFileSync, existsSync } from "fs";
import { join, isAbsolute, dirname, extname, relative } from "path";
import { logger } from "../cli/logger";
import { parse } from "@babel/parser";
import traverse from "@babel/traverse";
import type { SessionManager } from "application/use-cases/SessionManager";

// Zod schema for input validation
export const ReadFileSchema = z.object({
  path: z
    .string()
    .min(1)
    .describe("File path (relative to project or absolute)"),
  includeDeps: z
    .boolean()
    .optional()
    .default(false)
    .describe("Include level 1 dependencies"),
});

export type ReadFileInput = z.infer<typeof ReadFileSchema>;

export class ReadFileTool {
  private projectPath: string;
  private sessionManager: SessionManager | undefined;

  constructor(projectPath: string, sessionManager?: SessionManager) {
    this.projectPath = projectPath;
    this.sessionManager = sessionManager;
  }

  async execute(input: ReadFileInput): Promise<string> {
    logger.info("Read file tool called", {
      path: input.path,
      includeDeps: input.includeDeps,
    });

    try {
      // Validate input
      const validated = ReadFileSchema.parse(input);
      const { path, includeDeps } = validated;

      // Resolve file path
      const filePath = this.resolveFilePath(path);

      // Check if file exists
      if (!existsSync(filePath)) {
        return this.formatError(`File not found: ${path}`);
      }

      // Read main file
      const content = readFileSync(filePath, "utf-8");
      const relativePath = relative(this.projectPath, filePath);

      // Track file access (for context scoring)
      await this.trackFileAccess(relativePath);

      // Format output
      let markdown = this.formatFile(relativePath, content);

      // Include dependencies if requested
      if (includeDeps) {
        const deps = await this.extractDependencies(filePath, content);
        for (const dep of deps) {
          markdown += "\n\n";
          markdown += this.formatDependency(dep);
        }
      }

      return markdown;
    } catch (error) {
      logger.error("Read file failed", { error });
      if (error instanceof Error) {
        return this.formatError(error.message);
      }
      return this.formatError("Unknown error occurred");
    }
  }

  private resolveFilePath(path: string): string {
    if (isAbsolute(path)) {
      return path;
    }
    return join(this.projectPath, path);
  }

  private async trackFileAccess(filePath: string): Promise<void> {
    logger.debug("File accessed", {
      filePath,
      timestamp: new Date().toISOString(),
    });

    // Track file access in session if SessionManager is available
    if (this.sessionManager) {
      try {
        await this.sessionManager.trackFileAccess(filePath);
        logger.debug("File access tracked in session", { filePath });
      } catch (error) {
        logger.error("Failed to track file access", { error, filePath });
        // Don't throw - file reading should still succeed
      }
    }
  }

  private formatFile(path: string, content: string): string {
    const ext = extname(path).slice(1); // Remove leading dot
    const lang = this.getLanguage(ext);

    return `# File: ${path}

\`\`\`${lang}
${content}
\`\`\``;
  }

  private formatDependency(dep: { path: string; content: string }): string {
    const ext = extname(dep.path).slice(1);
    const lang = this.getLanguage(ext);

    return `# Dependency: ${dep.path}

\`\`\`${lang}
${dep.content}
\`\`\``;
  }

  private formatError(message: string): string {
    return `# Error

${message}

**Suggestions:**
- Check if the file path is correct
- Verify the file exists in the project
- Ensure you have read permissions`;
  }

  private getLanguage(ext: string): string {
    const langMap: Record<string, string> = {
      ts: "typescript",
      tsx: "typescript",
      js: "javascript",
      jsx: "javascript",
      json: "json",
      md: "markdown",
      yaml: "yaml",
      yml: "yaml",
      css: "css",
      scss: "scss",
      html: "html",
      py: "python",
      go: "go",
      rs: "rust",
      java: "java",
      c: "c",
      cpp: "cpp",
      sh: "bash",
    };
    return langMap[ext] ?? ext;
  }

  private async extractDependencies(
    filePath: string,
    content: string,
  ): Promise<{ path: string; content: string }[]> {
    try {
      const imports = this.parseImports(content);
      const deps: { path: string; content: string }[] = [];

      for (const importPath of imports) {
        // Skip node_modules
        if (!importPath.startsWith(".") && !importPath.startsWith("/")) {
          continue;
        }

        // Resolve import path
        const depPath = this.resolveImport(filePath, importPath);
        if (!depPath || !existsSync(depPath)) {
          continue;
        }

        // Read dependency file
        const depContent = readFileSync(depPath, "utf-8");
        const relativePath = relative(this.projectPath, depPath);

        // Track file access
        await this.trackFileAccess(relativePath);

        deps.push({
          path: relativePath,
          content: depContent,
        });
      }

      return deps;
    } catch (error) {
      logger.warn("Failed to parse imports", { error, filePath });
      return [];
    }
  }

  private parseImports(content: string): string[] {
    const imports: string[] = [];

    try {
      // Parse with Babel
      const ast = parse(content, {
        sourceType: "module",
        plugins: ["typescript", "jsx"],
      });

      // Traverse AST and extract import paths
      traverse(ast, {
        ImportDeclaration(path) {
          const source = path.node.source.value;
          imports.push(source);
        },
        // Also handle require() calls
        CallExpression(path) {
          if (
            path.node.callee.type === "Identifier" &&
            path.node.callee.name === "require" &&
            path.node.arguments.length > 0
          ) {
            const firstArg = path.node.arguments[0];
            if (firstArg && firstArg.type === "StringLiteral") {
              imports.push(firstArg.value);
            }
          }
        },
      });
    } catch (error) {
      logger.warn("Failed to parse file with Babel", { error });
    }

    return imports;
  }

  private resolveImport(fromFile: string, importPath: string): string | null {
    const fromDir = dirname(fromFile);
    const resolvedPath = join(fromDir, importPath);

    // Try different extensions
    const extensions = [".ts", ".tsx", ".js", ".jsx", ".json"];

    // If no extension, try adding them
    if (!extname(resolvedPath)) {
      for (const ext of extensions) {
        const withExt = resolvedPath + ext;
        if (existsSync(withExt)) {
          return withExt;
        }
      }

      // Try index files
      for (const ext of extensions) {
        const indexFile = join(resolvedPath, `index${ext}`);
        if (existsSync(indexFile)) {
          return indexFile;
        }
      }
    } else {
      // Extension provided, check if exists
      if (existsSync(resolvedPath)) {
        return resolvedPath;
      }
    }

    return null;
  }
}
