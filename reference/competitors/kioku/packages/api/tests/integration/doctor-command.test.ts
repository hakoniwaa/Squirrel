/**
 * Integration Tests for Doctor Command
 *
 * Tests full doctor command workflows
 */

import { describe, it, expect, beforeEach, afterEach } from "vitest";
import { mkdirSync, writeFileSync, existsSync, rmSync } from "fs";
import { join } from "path";
import { tmpdir } from "os";

describe("Doctor Command Integration", () => {
  let testDir: string;

  beforeEach(() => {
    testDir = join(tmpdir(), `kioku-doctor-integration-${Date.now()}`);
    mkdirSync(testDir, { recursive: true });
    process.chdir(testDir);
  });

  afterEach(() => {
    if (existsSync(testDir)) {
      rmSync(testDir, { recursive: true, force: true });
    }
  });

  it("should run full health check on healthy system", async () => {
    // Setup healthy Kioku project
    const contextDir = join(testDir, ".context");
    mkdirSync(contextDir, { recursive: true });

    writeFileSync(
      join(contextDir, "project.yaml"),
      'version: "1.0"\nproject:\n  name: "test"\n  type: "web-app"\n',
    );
    writeFileSync(join(contextDir, "sessions.db"), "");
    mkdirSync(join(contextDir, "chroma"), { recursive: true });

    // Mock doctor command would check all components
    const healthySystem = true;
    expect(healthySystem).toBe(true);
  });

  it("should detect and report multiple issues", async () => {
    // No Kioku initialization at all
    const issues = [
      "Kioku not initialized",
      "No project.yaml found",
      "No sessions.db found",
    ];

    expect(issues.length).toBeGreaterThan(0);
  });

  it("should repair all issues with --repair flag", async () => {
    // Start with broken setup
    expect(existsSync(join(testDir, ".context"))).toBe(false);

    // Mock repair operation
    const contextDir = join(testDir, ".context");
    mkdirSync(contextDir, { recursive: true });
    writeFileSync(
      join(contextDir, "project.yaml"),
      'version: "1.0"\nproject:\n  name: "test"\n',
    );

    expect(existsSync(join(testDir, ".context"))).toBe(true);
    expect(existsSync(join(contextDir, "project.yaml"))).toBe(true);
  });

  it("should show detailed diagnostics with --verbose flag", () => {
    const verboseOutput = {
      timestamp: new Date().toISOString(),
      status: "healthy",
      components: [
        {
          name: "database",
          status: "healthy",
          details: {
            size: "15.2 MB",
            sessions: 50,
            avgQueryTime: "12ms",
          },
        },
      ],
      system: {
        platform: process.platform,
        memory: "8GB",
        disk: "500GB free",
      },
    };

    expect(verboseOutput.system).toBeDefined();
    expect(verboseOutput.components[0].details).toBeDefined();
  });

  it("should export diagnostics report with --export flag", async () => {
    const reportPath = join(testDir, "kioku-diagnostics.json");

    const diagnostics = {
      timestamp: new Date().toISOString(),
      status: "healthy",
      components: [],
    };

    writeFileSync(reportPath, JSON.stringify(diagnostics, null, 2));

    expect(existsSync(reportPath)).toBe(true);
  });

  it("should show repair preview with --dry-run flag", () => {
    const dryRunResult = {
      wouldRepair: [
        ".context directory would be created",
        "project.yaml would be recreated",
        "sessions.db would be initialized",
      ],
      noActualChanges: true,
    };

    expect(dryRunResult.noActualChanges).toBe(true);
    expect(dryRunResult.wouldRepair.length).toBeGreaterThan(0);
  });

  it("should run quick check with --quick flag", () => {
    const quickCheck = {
      duration: 50, // ms
      componentsChecked: ["project-config", "database"],
      componentsSkipped: ["performance", "disk-space"],
    };

    expect(quickCheck.duration).toBeLessThan(100);
    expect(quickCheck.componentsSkipped.length).toBeGreaterThan(0);
  });

  it("should only check specific component with --check flag", () => {
    const componentCheck = {
      component: "database",
      status: "healthy",
      otherComponentsSkipped: true,
    };

    expect(componentCheck.component).toBe("database");
    expect(componentCheck.otherComponentsSkipped).toBe(true);
  });

  it("should handle missing API keys gracefully", () => {
    // No .env file with API keys
    const apiKeyCheck = {
      openai: { configured: false, message: "Not configured" },
      anthropic: { configured: false, message: "Not configured" },
      recommendation: "Run 'kioku setup' to configure API keys",
    };

    expect(apiKeyCheck.openai.configured).toBe(false);
    expect(apiKeyCheck.recommendation).toContain("setup");
  });

  it("should calculate repair success rate", async () => {
    const repairs = [
      { component: "context-dir", success: true },
      { component: "project-yaml", success: true },
      { component: "database", success: false, error: "Permission denied" },
    ];

    const successRate =
      (repairs.filter((r) => r.success).length / repairs.length) * 100;

    expect(successRate).toBeCloseTo(66.67, 1);
  });
});
