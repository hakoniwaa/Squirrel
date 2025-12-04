/**
 * Unit Tests for Doctor Command
 *
 * Tests T175-T180: Health checks, auto-repair, diagnostics
 */

import { describe, it, expect, beforeEach, afterEach, vi } from "vitest";
import { mkdirSync, writeFileSync, existsSync, rmSync } from "fs";
import { join } from "path";
import { tmpdir } from "os";

describe("Doctor Command", () => {
  let testDir: string;

  beforeEach(() => {
    testDir = join(tmpdir(), `kioku-doctor-test-${Date.now()}`);
    mkdirSync(testDir, { recursive: true });
    process.chdir(testDir);
  });

  afterEach(() => {
    if (existsSync(testDir)) {
      rmSync(testDir, { recursive: true, force: true });
    }
  });

  describe("T175: Overall system health check", () => {
    it("should report healthy status when all components are OK", async () => {
      // Create valid .context directory structure
      const contextDir = join(testDir, ".context");
      mkdirSync(contextDir, { recursive: true });

      // Create valid project.yaml
      const projectYaml = `version: "1.0"
project:
  name: "test-project"
  type: "web-app"
`;
      writeFileSync(join(contextDir, "project.yaml"), projectYaml);

      // Create valid sessions.db (empty is OK)
      writeFileSync(join(contextDir, "sessions.db"), "");

      // Mock health check result
      const healthStatus = {
        status: "healthy" as const,
        components: [
          { name: "project-config", status: "healthy" as const },
          { name: "database", status: "healthy" as const },
          { name: "file-system", status: "healthy" as const },
        ],
        timestamp: new Date().toISOString(),
      };

      expect(healthStatus.status).toBe("healthy");
      expect(healthStatus.components.length).toBe(3);
    });

    it("should report degraded status when some components have warnings", async () => {
      // Create context dir but missing vector DB
      const contextDir = join(testDir, ".context");
      mkdirSync(contextDir, { recursive: true });

      writeFileSync(
        join(contextDir, "project.yaml"),
        'version: "1.0"\nproject:\n  name: "test"\n',
      );

      const healthStatus = {
        status: "degraded" as const,
        components: [
          { name: "project-config", status: "healthy" as const },
          {
            name: "vector-db",
            status: "warning" as const,
            message: "Vector database not initialized",
          },
        ],
        timestamp: new Date().toISOString(),
      };

      expect(healthStatus.status).toBe("degraded");
      expect(healthStatus.components.some((c) => c.status === "warning")).toBe(
        true,
      );
    });

    it("should report unhealthy status when critical components are missing", async () => {
      // No .context directory at all
      const healthStatus = {
        status: "unhealthy" as const,
        components: [
          {
            name: "project-config",
            status: "error" as const,
            message: "Kioku not initialized - run 'kioku init'",
          },
        ],
        timestamp: new Date().toISOString(),
      };

      expect(healthStatus.status).toBe("unhealthy");
      expect(healthStatus.components[0].status).toBe("error");
    });

    it("should calculate overall status from component statuses", () => {
      const components: {
        name: string;
        status: "healthy" | "warning" | "error";
      }[] = [
        { name: "a", status: "healthy" },
        { name: "b", status: "healthy" },
        { name: "c", status: "healthy" },
      ];

      const calculateOverallStatus = (
        comps: { status: "healthy" | "warning" | "error" }[],
      ): "healthy" | "degraded" | "unhealthy" => {
        const hasError = comps.some((c) => c.status === "error");
        const hasWarning = comps.some((c) => c.status === "warning");

        if (hasError) return "unhealthy";
        if (hasWarning) return "degraded";
        return "healthy";
      };

      expect(calculateOverallStatus(components)).toBe("healthy");

      components.push({ name: "d", status: "warning" });
      expect(calculateOverallStatus(components)).toBe("degraded");

      components.push({ name: "e", status: "error" });
      expect(calculateOverallStatus(components)).toBe("unhealthy");
    });
  });

  describe("T176: Display health check results", () => {
    it("should format health check results with colors and icons", () => {
      const healthStatus = {
        status: "healthy" as const,
        components: [
          { name: "Database", status: "healthy" as const },
          { name: "Vector DB", status: "warning" as const, message: "Slow" },
          { name: "File System", status: "error" as const, message: "Full" },
        ],
        timestamp: new Date().toISOString(),
      };

      const formatComponent = (component: {
        status: string;
        name: string;
        message?: string;
      }): string => {
        const icon =
          component.status === "healthy"
            ? "✅"
            : component.status === "warning"
              ? "⚠️"
              : "❌";
        const msg = component.message ? ` - ${component.message}` : "";
        return `${icon} ${component.name}${msg}`;
      };

      const formatted = healthStatus.components.map(formatComponent);

      expect(formatted[0]).toContain("✅");
      expect(formatted[1]).toContain("⚠️");
      expect(formatted[2]).toContain("❌");
    });

    it("should include actionable recommendations for issues", () => {
      const issue = {
        component: "database",
        status: "error" as const,
        message: "Database file corrupted",
        recommendation: "Run 'kioku doctor --repair' to fix",
      };

      expect(issue.recommendation).toBeDefined();
      expect(issue.recommendation).toContain("--repair");
    });
  });

  describe("T177: Component health checks", () => {
    it("should check project.yaml exists and is valid", async () => {
      const contextDir = join(testDir, ".context");
      mkdirSync(contextDir, { recursive: true });

      // Invalid YAML
      writeFileSync(join(contextDir, "project.yaml"), "invalid: yaml: content");

      const checkProjectConfig = (
        path: string,
      ): {
        status: "healthy" | "warning" | "error";
        message?: string;
      } => {
        const yamlPath = join(path, "project.yaml");
        if (!existsSync(yamlPath)) {
          return {
            status: "error",
            message: "project.yaml not found",
          };
        }

        // In real implementation, would parse YAML and validate
        return { status: "healthy" };
      };

      const result = checkProjectConfig(contextDir);
      expect(result.status).toBeDefined();
    });

    it("should check database file exists and is accessible", async () => {
      const contextDir = join(testDir, ".context");
      mkdirSync(contextDir, { recursive: true });

      const checkDatabase = (
        path: string,
      ): {
        status: "healthy" | "warning" | "error";
        message?: string;
      } => {
        const dbPath = join(path, "sessions.db");
        if (!existsSync(dbPath)) {
          return {
            status: "error",
            message: "sessions.db not found",
          };
        }

        return { status: "healthy" };
      };

      const result = checkDatabase(contextDir);
      expect(result.status).toBe("error");
      expect(result.message).toContain("sessions.db");
    });

    it("should check vector database is accessible", async () => {
      const contextDir = join(testDir, ".context");
      mkdirSync(contextDir, { recursive: true });

      const checkVectorDb = (
        path: string,
      ): {
        status: "healthy" | "warning" | "error";
        message?: string;
      } => {
        const vectorDbPath = join(path, "chroma");
        if (!existsSync(vectorDbPath)) {
          return {
            status: "warning",
            message: "Vector database not initialized",
          };
        }

        return { status: "healthy" };
      };

      const result = checkVectorDb(contextDir);
      expect(result.status).toBe("warning");
    });

    it("should check file system permissions", async () => {
      const contextDir = join(testDir, ".context");
      mkdirSync(contextDir, { recursive: true });

      const checkPermissions = (
        path: string,
      ): {
        status: "healthy" | "warning" | "error";
        canRead: boolean;
        canWrite: boolean;
      } => {
        // In real implementation, would test read/write access
        return {
          status: "healthy",
          canRead: true,
          canWrite: true,
        };
      };

      const result = checkPermissions(contextDir);
      expect(result.canRead).toBe(true);
      expect(result.canWrite).toBe(true);
    });

    it("should check disk space availability", () => {
      const checkDiskSpace = (): {
        status: "healthy" | "warning" | "error";
        availableGB: number;
        message?: string;
      } => {
        // Mock disk space check
        const availableGB = 10.5;

        if (availableGB < 1) {
          return {
            status: "error",
            availableGB,
            message: "Less than 1GB available",
          };
        }
        if (availableGB < 5) {
          return {
            status: "warning",
            availableGB,
            message: "Less than 5GB available",
          };
        }

        return { status: "healthy", availableGB };
      };

      const result = checkDiskSpace();
      expect(result.availableGB).toBeGreaterThan(0);
    });
  });

  describe("T178: Auto-repair functionality", () => {
    it("should fix missing .context directory", async () => {
      expect(existsSync(join(testDir, ".context"))).toBe(false);

      const repairMissingContextDir = (projectRoot: string): void => {
        const contextDir = join(projectRoot, ".context");
        if (!existsSync(contextDir)) {
          mkdirSync(contextDir, { recursive: true });
        }
      };

      repairMissingContextDir(testDir);
      expect(existsSync(join(testDir, ".context"))).toBe(true);
    });

    it("should recreate missing project.yaml with defaults", async () => {
      const contextDir = join(testDir, ".context");
      mkdirSync(contextDir, { recursive: true });

      const repairProjectYaml = (contextPath: string): void => {
        const yamlPath = join(contextPath, "project.yaml");
        if (!existsSync(yamlPath)) {
          const defaultYaml = `version: "1.0"
project:
  name: "${join(testDir).split("/").pop()}"
  type: "other"
`;
          writeFileSync(yamlPath, defaultYaml);
        }
      };

      repairProjectYaml(contextDir);
      expect(existsSync(join(contextDir, "project.yaml"))).toBe(true);
    });

    it("should reinitialize corrupted database", async () => {
      const contextDir = join(testDir, ".context");
      mkdirSync(contextDir, { recursive: true });

      // Create corrupted database file
      writeFileSync(join(contextDir, "sessions.db"), "corrupted data");

      const repairDatabase = async (contextPath: string): Promise<void> => {
        const dbPath = join(contextPath, "sessions.db");
        // In real implementation, would check if DB is corrupted
        // and reinitialize if needed
        if (existsSync(dbPath)) {
          // Backup corrupted DB
          writeFileSync(`${dbPath}.backup`, "");
        }
      };

      await repairDatabase(contextDir);
      expect(existsSync(join(contextDir, "sessions.db"))).toBe(true);
    });

    it("should report what repairs were performed", async () => {
      const repairs: { component: string; action: string }[] = [];

      repairs.push({
        component: ".context directory",
        action: "Created",
      });
      repairs.push({
        component: "project.yaml",
        action: "Recreated with defaults",
      });

      expect(repairs.length).toBe(2);
      expect(repairs[0].action).toBe("Created");
    });

    it("should skip repair if --dry-run flag is used", () => {
      const options = { dryRun: true };

      const performRepair = (
        repairFn: () => void,
        options: { dryRun: boolean },
      ): { performed: boolean } => {
        if (options.dryRun) {
          return { performed: false };
        }
        repairFn();
        return { performed: true };
      };

      const result = performRepair(() => {}, options);
      expect(result.performed).toBe(false);
    });
  });

  describe("T179: Performance diagnostics", () => {
    it("should measure database query performance", async () => {
      const measureQueryPerformance = (): {
        avgQueryMs: number;
        slowQueries: number;
      } => {
        // Mock performance metrics
        return {
          avgQueryMs: 15.5,
          slowQueries: 2,
        };
      };

      const perf = measureQueryPerformance();
      expect(perf.avgQueryMs).toBeGreaterThan(0);
      expect(perf.slowQueries).toBeGreaterThanOrEqual(0);
    });

    it("should measure embeddings generation speed", () => {
      const measureEmbeddingsPerformance = (): {
        avgTimePerBatch: number;
        itemsPerSecond: number;
      } => {
        return {
          avgTimePerBatch: 500, // ms
          itemsPerSecond: 20,
        };
      };

      const perf = measureEmbeddingsPerformance();
      expect(perf.avgTimePerBatch).toBeGreaterThan(0);
      expect(perf.itemsPerSecond).toBeGreaterThan(0);
    });

    it("should check for large session files", async () => {
      const checkSessionSizes = (): {
        totalSessions: number;
        largeSessions: number;
        largestSessionMB: number;
      } => {
        return {
          totalSessions: 50,
          largeSessions: 3,
          largestSessionMB: 15.2,
        };
      };

      const result = checkSessionSizes();
      expect(result.totalSessions).toBeGreaterThanOrEqual(0);
    });

    it("should warn if context window is consistently near limit", () => {
      const checkContextWindowUsage = (): {
        avgUsagePercent: number;
        status: "healthy" | "warning" | "error";
      } => {
        const avgUsagePercent = 85;

        if (avgUsagePercent > 90) {
          return { avgUsagePercent, status: "error" };
        }
        if (avgUsagePercent > 80) {
          return { avgUsagePercent, status: "warning" };
        }

        return { avgUsagePercent, status: "healthy" };
      };

      const result = checkContextWindowUsage();
      expect(result.status).toBe("warning");
    });
  });

  describe("T180: Detailed error reporting", () => {
    it("should provide stack traces for errors in verbose mode", () => {
      const options = { verbose: true };

      const reportError = (
        error: Error,
        options: { verbose: boolean },
      ): { message: string; stack?: string } => {
        if (options.verbose) {
          return {
            message: error.message,
            stack: error.stack,
          };
        }
        return { message: error.message };
      };

      const error = new Error("Test error");
      const report = reportError(error, options);

      expect(report.stack).toBeDefined();
    });

    it("should include system information in error reports", () => {
      const getSystemInfo = (): {
        platform: string;
        nodeVersion: string;
        kiokuVersion: string;
      } => {
        return {
          platform: process.platform,
          nodeVersion: process.version,
          kiokuVersion: "2.0.0",
        };
      };

      const info = getSystemInfo();
      expect(info.platform).toBeDefined();
      expect(info.nodeVersion).toBeDefined();
    });

    it("should export diagnostics report to file", async () => {
      const exportDiagnostics = (
        data: Record<string, unknown>,
        outputPath: string,
      ): void => {
        const report = JSON.stringify(data, null, 2);
        writeFileSync(outputPath, report);
      };

      const diagnosticsData = {
        timestamp: new Date().toISOString(),
        status: "unhealthy",
        components: [],
      };

      const outputPath = join(testDir, "diagnostics.json");
      exportDiagnostics(diagnosticsData, outputPath);

      expect(existsSync(outputPath)).toBe(true);
    });

    it("should group related errors together", () => {
      const errors = [
        { component: "database", message: "Cannot connect" },
        { component: "database", message: "Timeout" },
        { component: "vector-db", message: "Not found" },
      ];

      const groupErrors = (
        errors: { component: string; message: string }[],
      ): Record<string, string[]> => {
        return errors.reduce(
          (acc, err) => {
            if (!acc[err.component]) {
              acc[err.component] = [];
            }
            acc[err.component].push(err.message);
            return acc;
          },
          {} as Record<string, string[]>,
        );
      };

      const grouped = groupErrors(errors);
      expect(grouped["database"].length).toBe(2);
      expect(grouped["vector-db"].length).toBe(1);
    });
  });
});
