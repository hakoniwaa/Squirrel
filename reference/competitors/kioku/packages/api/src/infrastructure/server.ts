/**
 * MCP Server
 *
 * Model Context Protocol server that exposes project context
 * as resources and provides tools for context management.
 */

import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  ListResourcesRequestSchema,
  ReadResourceRequestSchema,
  ListToolsRequestSchema,
  CallToolRequestSchema,
} from "@modelcontextprotocol/sdk/types.js";
import { zodToJsonSchema } from "zod-to-json-schema";
import { logger } from "./cli/logger";
import { YAMLHandler } from "infrastructure/storage/yaml-handler";
import { SQLiteAdapter } from "infrastructure/storage/sqlite-adapter";
import { ServiceManager } from "infrastructure/background/ServiceManager";
import { SessionManager } from "application/use-cases/SessionManager";
import { ProjectResource } from "./resources/ProjectResource";
import { ModuleResource } from "./resources/ModuleResource";
import { SessionResource } from "./resources/SessionResource";
import { SessionHistoryResource } from "./resources/SessionHistoryResource";
import {
  ContextSearchTool,
  ContextSearchSchema,
} from "./tools/ContextSearchTool";
import { ReadFileTool, ReadFileSchema } from "./tools/ReadFileTool";
import { GrepCodebaseTool, GrepCodebaseSchema } from "./tools/GrepCodebaseTool";
import { GitLogTool, GitLogSchema } from "./tools/GitLogTool";
import { GitBlameTool, GitBlameSchema } from "./tools/GitBlameTool";
import { GitDiffTool, GitDiffSchema } from "./tools/GitDiffTool";
import { join } from "path";
import type { ProjectContext } from "domain/models/ProjectContext";

export class MCPServer {
  private server: Server;
  private projectContext: ProjectContext | null = null;
  private projectPath: string;
  private sqliteAdapter: SQLiteAdapter | null = null;
  private serviceManager: ServiceManager | null = null;
  private sessionManager: SessionManager | null = null;

  constructor(projectPath: string) {
    this.projectPath = projectPath;
    this.server = new Server(
      {
        name: "kioku",
        version: "1.0.0",
      },
      {
        capabilities: {
          resources: {},
          tools: {},
        },
      },
    );
  }

  async start(): Promise<void> {
    // Load project context
    await this.loadProjectContext();

    // Initialize SQLite adapter
    this.initializeSQLite();

    // Start background services
    this.startBackgroundServices();

    // Initialize and start session tracking
    await this.startSessionTracking();

    // Register resources
    this.registerResources();

    // Register tools (future phases)
    this.registerTools();

    // Connect stdio transport
    const transport = new StdioServerTransport();
    await this.server.connect(transport);

    logger.info("Kioku MCP server started", {
      project: this.projectContext?.project.name,
      path: this.projectPath,
    });
  }

  /**
   * Stop the MCP server and all background services
   */
  async stop(): Promise<void> {
    logger.info("Stopping MCP server");

    // End session and trigger enrichment
    await this.stopSessionTracking();

    // Stop background services
    if (this.serviceManager) {
      this.serviceManager.stop();
    }

    // Close SQLite adapter
    if (this.sqliteAdapter) {
      this.sqliteAdapter.close();
    }

    logger.info("MCP server stopped");
  }

  private async loadProjectContext(): Promise<void> {
    try {
      const yamlPath = join(this.projectPath, ".context", "project.yaml");
      this.projectContext = YAMLHandler.loadProjectContext(yamlPath);
      logger.info("Project context loaded", {
        modules: Object.keys(this.projectContext.modules).length,
      });
    } catch (error) {
      logger.error("Failed to load project context", { error });
      throw error;
    }
  }

  private initializeSQLite(): void {
    const dbPath = join(this.projectPath, ".context", "sessions.db");
    this.sqliteAdapter = new SQLiteAdapter(dbPath);
    logger.debug("SQLite adapter initialized", { dbPath });
  }

  private startBackgroundServices(): void {
    if (!this.sqliteAdapter) {
      throw new Error("SQLite adapter must be initialized first");
    }

    this.serviceManager = new ServiceManager(this.sqliteAdapter);
    this.serviceManager.start();

    logger.info("Background services started", {
      services: this.serviceManager.getServices(),
    });
  }

  private async startSessionTracking(): Promise<void> {
    logger.info("Starting session tracking");

    if (!this.sqliteAdapter) {
      throw new Error("SQLite adapter must be initialized before session tracking");
    }

    // Create SessionManager instance
    this.sessionManager = new SessionManager(this.projectPath, this.sqliteAdapter);

    // Start a new session (this will end any existing active session first)
    const session = await this.sessionManager.startSession();

    logger.info("Session started on MCP connection", {
      sessionId: session.id,
      projectId: session.projectId,
    });
  }

  private async stopSessionTracking(): Promise<void> {
    if (!this.sessionManager) {
      logger.debug("No session manager to stop");
      return;
    }

    logger.info("Stopping session tracking");

    try {
      // Get current session before ending it
      const session = await this.sessionManager.getCurrentSession();

      if (!session) {
        logger.debug("No active session to end");
        return;
      }

      const sessionId = session.id;

      // End the session
      await this.sessionManager.endSession();

      logger.info("Session ended", { sessionId });

      // NOTE: Discovery extraction and enrichment deferred to v2
      // MVP tracks sessions but does not store conversation messages.
      // v2 will add message tracking to enable:
      // 1. Retrieve session messages from database
      // 2. Extract discoveries using patterns
      // 3. Enrich project.yaml with discoveries
      // See: Future Enhancements in kioku.md (AI-based Discovery)

      logger.debug("Discovery extraction not available in MVP v1.0", {
        sessionId,
        note: "Message tracking required - deferred to v2",
      });
    } catch (error) {
      logger.error("Error during session stop", { error });
      // Don't throw - we still want to clean up the server
    }
  }

  private registerResources(): void {
    // List all available resources
    this.server.setRequestHandler(ListResourcesRequestSchema, async () => {
      if (!this.projectContext) {
        return { resources: [] };
      }

      const resources = [
        {
          uri: "context://project/overview",
          name: "Project Overview",
          mimeType: "text/markdown",
          description:
            "High-level project information, tech stack, and architecture",
        },
      ];

      // Add module resources
      const moduleNames = ModuleResource.getModuleNames(
        this.projectContext.modules,
      );
      for (const moduleName of moduleNames) {
        resources.push({
          uri: `context://module/${moduleName}`,
          name: `Module: ${moduleName}`,
          mimeType: "text/markdown",
          description: `Detailed context for ${moduleName} module`,
        });
      }

      // Add current session resource
      resources.push({
        uri: "context://session/current",
        name: "Current Session",
        mimeType: "text/markdown",
        description: "Current coding session information",
      });

      // Add session history resource
      resources.push({
        uri: "context://sessions/history",
        name: "Session History",
        mimeType: "text/markdown",
        description: "Recent coding sessions with metadata",
      });

      return { resources };
    });

    // Read specific resource
    this.server.setRequestHandler(
      ReadResourceRequestSchema,
      async (request) => {
        const uri = request.params.uri;

        if (!this.projectContext) {
          throw new Error("Project context not loaded");
        }

        // Project overview
        if (uri === "context://project/overview") {
          const markdown = ProjectResource.formatAsMarkdown(
            this.projectContext,
          );
          return {
            contents: [
              {
                uri,
                mimeType: "text/markdown",
                text: markdown,
              },
            ],
          };
        }

        // Module detail
        if (uri.startsWith("context://module/")) {
          const moduleName = uri.replace("context://module/", "");
          const module = this.projectContext.modules[moduleName];

          if (!module) {
            throw new Error(`Module not found: ${moduleName}`);
          }

          const markdown = ModuleResource.formatAsMarkdown(moduleName, module);
          return {
            contents: [
              {
                uri,
                mimeType: "text/markdown",
                text: markdown,
              },
            ],
          };
        }

        // Current session
        if (uri === "context://session/current") {
          if (!this.sqliteAdapter) {
            throw new Error("SQLite adapter not initialized");
          }

          const session = this.sqliteAdapter.getActiveSession(
            this.projectContext.project.name,
          );
          const markdown = SessionResource.formatAsMarkdown(session ?? null);
          return {
            contents: [
              {
                uri,
                mimeType: "text/markdown",
                text: markdown,
              },
            ],
          };
        }

        // Session history
        if (uri === "context://sessions/history") {
          if (!this.sqliteAdapter) {
            throw new Error("SQLite adapter not initialized");
          }

          const historyResource = new SessionHistoryResource(
            this.sqliteAdapter,
          );
          const markdown = await historyResource.read();
          return {
            contents: [
              {
                uri,
                mimeType: "text/markdown",
                text: markdown,
              },
            ],
          };
        }

        throw new Error(`Unknown resource URI: ${uri}`);
      },
    );

    logger.debug("Resources registered");
  }

  private registerTools(): void {
    // List available tools
    this.server.setRequestHandler(ListToolsRequestSchema, async () => {
      return {
        tools: [
          {
            name: "context_search",
            description:
              "Search project context (patterns, rules, issues, discoveries) using text search",
            inputSchema: zodToJsonSchema(ContextSearchSchema),
          },
          {
            name: "read_file",
            description:
              "Read a file with optional dependency loading. Parses imports and can include level 1 dependencies.",
            inputSchema: zodToJsonSchema(ReadFileSchema),
          },
          {
            name: "grep_codebase",
            description:
              "Search files in the codebase using regex patterns. Supports file type filtering, glob patterns, and context lines.",
            inputSchema: zodToJsonSchema(GrepCodebaseSchema),
          },
          {
            name: "git_log",
            description:
              "Query git commit history with optional filters (limit, file paths, date range, author)",
            inputSchema: zodToJsonSchema(GitLogSchema),
          },
          {
            name: "git_blame",
            description:
              "Show line-by-line authorship for a file with commit details and dates",
            inputSchema: zodToJsonSchema(GitBlameSchema),
          },
          {
            name: "git_diff",
            description:
              "Compare changes between git references (branches, commits, tags) with file change summary",
            inputSchema: zodToJsonSchema(GitDiffSchema),
          },
        ],
      };
    });

    // Handle tool calls
    this.server.setRequestHandler(CallToolRequestSchema, async (request) => {
      const { name, arguments: args } = request.params;

      if (name === "context_search") {
        // TODO: Initialize SearchCodeChunks with proper dependencies
        // For now, ContextSearchTool will fallback to discovery search
        const tool = new ContextSearchTool(
          this.projectPath,
          undefined, // searchCodeChunks - not initialized yet
          this.sessionManager ?? undefined,
        );
        // eslint-disable-next-line @typescript-eslint/no-explicit-any -- MCP args are untyped, validated by Zod in tool
        const result = await tool.execute(args as any);

        return {
          content: [
            {
              type: "text",
              text: result,
            },
          ],
        };
      }

      if (name === "read_file") {
        const tool = new ReadFileTool(
          this.projectPath,
          this.sessionManager ?? undefined,
        );
        // eslint-disable-next-line @typescript-eslint/no-explicit-any -- MCP args are untyped, validated by Zod in tool
        const result = await tool.execute(args as any);

        return {
          content: [
            {
              type: "text",
              text: result,
            },
          ],
        };
      }

      if (name === "grep_codebase") {
        const tool = new GrepCodebaseTool(
          this.projectPath,
          this.sessionManager ?? undefined,
        );
        // eslint-disable-next-line @typescript-eslint/no-explicit-any -- MCP args are untyped, validated by Zod in tool
        const result = await tool.execute(args as any);

        return {
          content: [
            {
              type: "text",
              text: result,
            },
          ],
        };
      }

      if (name === "git_log") {
        const tool = new GitLogTool(
          this.projectPath,
          this.sessionManager ?? undefined,
        );
        // eslint-disable-next-line @typescript-eslint/no-explicit-any -- MCP args are untyped, validated by Zod in tool
        const result = await tool.execute(args as any);

        return {
          content: [
            {
              type: "text",
              text: result,
            },
          ],
        };
      }

      if (name === "git_blame") {
        const tool = new GitBlameTool(
          this.projectPath,
          this.sessionManager ?? undefined,
        );
        // eslint-disable-next-line @typescript-eslint/no-explicit-any -- MCP args are untyped, validated by Zod in tool
        const result = await tool.execute(args as any);

        return {
          content: [
            {
              type: "text",
              text: result,
            },
          ],
        };
      }

      if (name === "git_diff") {
        const tool = new GitDiffTool(
          this.projectPath,
          this.sessionManager ?? undefined,
        );
        // eslint-disable-next-line @typescript-eslint/no-explicit-any -- MCP args are untyped, validated by Zod in tool
        const result = await tool.execute(args as any);

        return {
          content: [
            {
              type: "text",
              text: result,
            },
          ],
        };
      }

      throw new Error(`Unknown tool: ${name}`);
    });

    logger.debug("Tools registered");
  }

  getProjectContext(): ProjectContext | null {
    return this.projectContext;
  }
}

export async function startMCPServer(
  projectPath: string = process.cwd(),
): Promise<MCPServer> {
  const server = new MCPServer(projectPath);
  await server.start();
  return server;
}
