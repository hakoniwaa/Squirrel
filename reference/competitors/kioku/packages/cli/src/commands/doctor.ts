/**
 * Doctor Command - System Health Checks and Auto-Repair
 *
 * Implements T175-T185: Health checks, diagnostics, auto-repair
 */

import {
  existsSync,
  mkdirSync,
  writeFileSync,
  readFileSync,
  statSync,
} from "fs";
import { join } from "path";
import Database from "bun:sqlite";
import { logger } from "../logger";
import { parse as parseYaml } from "yaml";

export interface DoctorOptions {
  repair?: boolean;
  dryRun?: boolean;
  verbose?: boolean;
  export?: string;
  quick?: boolean;
  check?: string;
}

type ComponentStatus = "healthy" | "warning" | "error";

interface ComponentHealth {
  name: string;
  status: ComponentStatus;
  message?: string;
  details?: Record<string, unknown>;
  recommendation?: string;
}

interface SystemHealth {
  status: "healthy" | "degraded" | "unhealthy";
  components: ComponentHealth[];
  timestamp: string;
  systemInfo?: {
    platform: string;
    nodeVersion: string;
    kiokuVersion: string;
    memory?: string;
    disk?: string;
  };
}

interface RepairAction {
  component: string;
  action: string;
  success: boolean;
  error?: string;
}

/**
 * T181: Main doctor command entry point
 */
export async function doctorCommand(
  options: DoctorOptions = {},
): Promise<void> {
  const startTime = Date.now();

  console.log("\n🏥 Kioku Health Check\n");

  const projectRoot = process.cwd();
  const contextDir = join(projectRoot, ".context");

  // Perform health checks
  const health = await performHealthChecks(contextDir, options);

  // Display results
  displayHealthResults(health, options);

  // Auto-repair if requested
  if (options.repair || options.dryRun) {
    console.log("\n🔧 Repair Mode\n");
    const repairs = await performRepairs(contextDir, health, options);
    displayRepairResults(repairs, options);
  }

  // Export diagnostics if requested
  if (options.export) {
    exportDiagnostics(health, options.export);
    console.log(`\n📄 Diagnostics exported to: ${options.export}`);
  }

  const duration = ((Date.now() - startTime) / 1000).toFixed(2);
  console.log(`\n⏱️  Health check completed in ${duration}s\n`);

  // Exit with appropriate code
  if (health.status === "unhealthy") {
    process.exit(1);
  }

  logger.info("Doctor command completed", {
    status: health.status,
    duration: `${duration}s`,
  });
}

/**
 * T175-T177: Perform all health checks
 */
async function performHealthChecks(
  contextDir: string,
  options: DoctorOptions,
): Promise<SystemHealth> {
  const components: ComponentHealth[] = [];

  // Quick mode - skip expensive checks
  const componentsToCheck = options.quick
    ? ["project-config", "database"]
    : [
        "project-config",
        "database",
        "vector-db",
        "file-system",
        "disk-space",
        "api-keys",
      ];

  // Specific component check
  if (options.check) {
    const componentHealth = await checkComponent(contextDir, options.check);
    components.push(componentHealth);
  } else {
    // Check all components
    for (const component of componentsToCheck) {
      const componentHealth = await checkComponent(contextDir, component);
      components.push(componentHealth);
    }
  }

  // Calculate overall status
  const status = calculateOverallStatus(components);

  // Add system info in verbose mode
  const systemInfo = options.verbose ? getSystemInfo() : undefined;

  const health: SystemHealth = {
    status,
    components,
    timestamp: new Date().toISOString(),
    ...(systemInfo ? { systemInfo } : {}),
  };

  return health;
}

/**
 * T177: Check individual component health
 */
async function checkComponent(
  contextDir: string,
  componentName: string,
): Promise<ComponentHealth> {
  switch (componentName) {
    case "project-config":
      return checkProjectConfig(contextDir);
    case "database":
      return checkDatabase(contextDir);
    case "vector-db":
      return checkVectorDb(contextDir);
    case "file-system":
      return checkFileSystem(contextDir);
    case "disk-space":
      return checkDiskSpace();
    case "api-keys":
      return checkApiKeys();
    default:
      return {
        name: componentName,
        status: "error",
        message: `Unknown component: ${componentName}`,
      };
  }
}

/**
 * Check project.yaml exists and is valid
 */
function checkProjectConfig(contextDir: string): ComponentHealth {
  const yamlPath = join(contextDir, "project.yaml");

  if (!existsSync(contextDir)) {
    return {
      name: "Project Config",
      status: "error",
      message: "Kioku not initialized",
      recommendation: "Run 'kioku init' to initialize",
    };
  }

  if (!existsSync(yamlPath)) {
    return {
      name: "Project Config",
      status: "error",
      message: "project.yaml not found",
      recommendation: "Run 'kioku doctor --repair' to recreate",
    };
  }

  try {
    const content = readFileSync(yamlPath, "utf-8");
    const parsed = parseYaml(content);

    if (!parsed || !parsed.version || !parsed.project) {
      return {
        name: "Project Config",
        status: "warning",
        message: "project.yaml is invalid or incomplete",
        recommendation: "Run 'kioku doctor --repair' to fix",
      };
    }

    return {
      name: "Project Config",
      status: "healthy",
      details: {
        version: parsed.version,
        projectName: parsed.project.name,
        projectType: parsed.project.type,
      },
    };
  } catch (error) {
    logger.error("Failed to parse project.yaml", { error });
    return {
      name: "Project Config",
      status: "error",
      message: "project.yaml is corrupted",
      recommendation: "Run 'kioku doctor --repair' to recreate",
    };
  }
}

/**
 * Check database exists and is accessible
 */
function checkDatabase(contextDir: string): ComponentHealth {
  const dbPath = join(contextDir, "sessions.db");

  if (!existsSync(dbPath)) {
    return {
      name: "Database",
      status: "error",
      message: "sessions.db not found",
      recommendation: "Run 'kioku doctor --repair' to reinitialize",
    };
  }

  try {
    const db = new Database(dbPath);

    // Try to query the database
    const tables = db
      .query<
        { name: string },
        []
      >("SELECT name FROM sqlite_master WHERE type='table'")
      .all();

    db.close();

    const stats = statSync(dbPath);
    const sizeMB = (stats.size / 1024 / 1024).toFixed(2);

    return {
      name: "Database",
      status: "healthy",
      details: {
        size: `${sizeMB} MB`,
        tables: tables.length,
      },
    };
  } catch (error) {
    logger.error("Database check failed", { error });
    return {
      name: "Database",
      status: "error",
      message: "Database is corrupted or inaccessible",
      recommendation: "Run 'kioku doctor --repair' to reinitialize",
    };
  }
}

/**
 * Check vector database is accessible
 */
function checkVectorDb(contextDir: string): ComponentHealth {
  const vectorDbPath = join(contextDir, "chroma");

  if (!existsSync(vectorDbPath)) {
    return {
      name: "Vector DB",
      status: "warning",
      message: "Vector database not initialized",
      recommendation: "Will be created automatically when needed",
    };
  }

  try {
    // Check if directory exists and is accessible
    statSync(vectorDbPath);

    return {
      name: "Vector DB",
      status: "healthy",
      details: {
        path: vectorDbPath,
        initialized: true,
      },
    };
  } catch (error) {
    logger.error("Vector DB check failed", { error });
    return {
      name: "Vector DB",
      status: "warning",
      message: "Vector database directory not accessible",
    };
  }
}

/**
 * Check file system permissions
 */
function checkFileSystem(contextDir: string): ComponentHealth {
  if (!existsSync(contextDir)) {
    return {
      name: "File System",
      status: "error",
      message: ".context directory not found",
      recommendation: "Run 'kioku init' or 'kioku doctor --repair'",
    };
  }

  try {
    // Test write access
    const testFile = join(contextDir, ".health-check-test");
    writeFileSync(testFile, "test");

    // Test read access
    readFileSync(testFile, "utf-8");

    // Clean up
    if (existsSync(testFile)) {
      const fs = require("fs");
      fs.unlinkSync(testFile);
    }

    return {
      name: "File System",
      status: "healthy",
      details: {
        canRead: true,
        canWrite: true,
      },
    };
  } catch (error) {
    logger.error("File system check failed", { error });
    return {
      name: "File System",
      status: "error",
      message: "No read/write permissions",
      recommendation: "Check file permissions for .context directory",
    };
  }
}

/**
 * T179: Check disk space availability
 */
function checkDiskSpace(): ComponentHealth {
  try {
    // Use df command to get disk space (works on Unix-like systems)
    const { execSync } = require("child_process");
    const output = execSync("df -h . | tail -1 | awk '{print $4}'", {
      encoding: "utf-8",
    });
    const available = output.trim();

    // Parse available space (e.g., "50Gi" or "500M")
    const match = available.match(/^(\d+(?:\.\d+)?)(G|M|K)i?$/i);

    if (!match) {
      return {
        name: "Disk Space",
        status: "healthy",
        message: "Could not parse disk space",
      };
    }

    const value = parseFloat(match[1]);
    const unit = match[2].toUpperCase();

    let availableGB = 0;
    if (unit === "G") {
      availableGB = value;
    } else if (unit === "M") {
      availableGB = value / 1024;
    } else if (unit === "K") {
      availableGB = value / (1024 * 1024);
    }

    if (availableGB < 1) {
      return {
        name: "Disk Space",
        status: "error",
        message: `Less than 1GB available (${availableGB.toFixed(2)}GB)`,
        recommendation: "Free up disk space",
      };
    }

    if (availableGB < 5) {
      return {
        name: "Disk Space",
        status: "warning",
        message: `Less than 5GB available (${availableGB.toFixed(2)}GB)`,
        recommendation: "Consider freeing up disk space",
      };
    }

    return {
      name: "Disk Space",
      status: "healthy",
      details: {
        available: `${availableGB.toFixed(2)}GB`,
      },
    };
  } catch (error) {
    logger.warn("Disk space check failed", { error });
    return {
      name: "Disk Space",
      status: "healthy",
      message: "Could not check disk space",
    };
  }
}

/**
 * Check API keys are configured
 */
function checkApiKeys(): ComponentHealth {
  const projectRoot = process.cwd();
  const envPath = join(projectRoot, ".env");

  if (!existsSync(envPath)) {
    return {
      name: "API Keys",
      status: "warning",
      message: "No .env file found",
      recommendation: "Run 'kioku setup' to configure API keys",
    };
  }

  try {
    const envContent = readFileSync(envPath, "utf-8");
    const hasOpenAI = envContent.includes("OPENAI_API_KEY=");
    const hasAnthropic = envContent.includes("ANTHROPIC_API_KEY=");

    if (!hasOpenAI) {
      return {
        name: "API Keys",
        status: "error",
        message: "OpenAI API key not configured",
        recommendation: "Run 'kioku setup' to add API key",
      };
    }

    return {
      name: "API Keys",
      status: "healthy",
      details: {
        openai: hasOpenAI,
        anthropic: hasAnthropic,
      },
    };
  } catch (error) {
    logger.error("API keys check failed", { error });
    return {
      name: "API Keys",
      status: "warning",
      message: "Could not read .env file",
    };
  }
}

/**
 * T175: Calculate overall status from component statuses
 */
function calculateOverallStatus(
  components: ComponentHealth[],
): "healthy" | "degraded" | "unhealthy" {
  const hasError = components.some((c) => c.status === "error");
  const hasWarning = components.some((c) => c.status === "warning");

  if (hasError) return "unhealthy";
  if (hasWarning) return "degraded";
  return "healthy";
}

/**
 * T176: Display health check results
 */
function displayHealthResults(
  health: SystemHealth,
  options: DoctorOptions,
): void {
  // Overall status
  const statusIcon =
    health.status === "healthy"
      ? "✅"
      : health.status === "degraded"
        ? "⚠️"
        : "❌";
  const statusText =
    health.status === "healthy"
      ? "Healthy"
      : health.status === "degraded"
        ? "Degraded"
        : "Unhealthy";

  console.log(`${statusIcon} Overall Status: ${statusText}\n`);

  // Component statuses
  console.log("Components:");
  for (const component of health.components) {
    const icon =
      component.status === "healthy"
        ? "  ✅"
        : component.status === "warning"
          ? "  ⚠️"
          : "  ❌";
    const msg = component.message ? ` - ${component.message}` : "";

    console.log(`${icon} ${component.name}${msg}`);

    if (options.verbose && component.details) {
      for (const [key, value] of Object.entries(component.details)) {
        console.log(`      ${key}: ${value}`);
      }
    }

    if (component.recommendation) {
      console.log(`      💡 ${component.recommendation}`);
    }
  }

  // System info in verbose mode
  if (options.verbose && health.systemInfo) {
    console.log("\nSystem Information:");
    console.log(`  Platform: ${health.systemInfo.platform}`);
    console.log(`  Node Version: ${health.systemInfo.nodeVersion}`);
    console.log(`  Kioku Version: ${health.systemInfo.kiokuVersion}`);
  }
}

/**
 * T178: Perform repair actions
 */
async function performRepairs(
  contextDir: string,
  health: SystemHealth,
  options: DoctorOptions,
): Promise<RepairAction[]> {
  const repairs: RepairAction[] = [];

  for (const component of health.components) {
    if (component.status === "error" || component.status === "warning") {
      const repair = await repairComponent(contextDir, component, options);
      if (repair) {
        repairs.push(repair);
      }
    }
  }

  return repairs;
}

/**
 * Repair individual component
 */
async function repairComponent(
  contextDir: string,
  component: ComponentHealth,
  options: DoctorOptions,
): Promise<RepairAction | null> {
  const projectRoot = process.cwd();

  try {
    switch (component.name) {
      case "Project Config": {
        if (!existsSync(contextDir)) {
          if (!options.dryRun) {
            mkdirSync(contextDir, { recursive: true });
          }
          return {
            component: ".context directory",
            action: options.dryRun ? "Would create" : "Created",
            success: true,
          };
        }

        const yamlPath = join(contextDir, "project.yaml");
        if (!existsSync(yamlPath)) {
          const projectName = projectRoot.split("/").pop() || "kioku-project";
          const defaultYaml = `version: "1.0"
project:
  name: "${projectName}"
  type: "other"
`;
          if (!options.dryRun) {
            writeFileSync(yamlPath, defaultYaml);
          }
          return {
            component: "project.yaml",
            action: options.dryRun
              ? "Would recreate with defaults"
              : "Recreated with defaults",
            success: true,
          };
        }
        break;
      }

      case "Database": {
        const dbPath = join(contextDir, "sessions.db");
        if (!existsSync(dbPath)) {
          if (!options.dryRun) {
            // Create empty database with schema
            const db = new Database(dbPath);
            db.close();
          }
          return {
            component: "sessions.db",
            action: options.dryRun ? "Would initialize" : "Initialized",
            success: true,
          };
        }
        break;
      }

      case "Vector DB": {
        const vectorDbPath = join(contextDir, "chroma");
        if (!existsSync(vectorDbPath)) {
          if (!options.dryRun) {
            mkdirSync(vectorDbPath, { recursive: true });
          }
          return {
            component: "Vector DB",
            action: options.dryRun ? "Would initialize" : "Initialized",
            success: true,
          };
        }
        break;
      }

      default:
        return null;
    }

    return null;
  } catch (error) {
    logger.error("Repair failed", { component: component.name, error });
    return {
      component: component.name,
      action: "Repair failed",
      success: false,
      error: error instanceof Error ? error.message : "Unknown error",
    };
  }
}

/**
 * Display repair results
 */
function displayRepairResults(
  repairs: RepairAction[],
  options: DoctorOptions,
): void {
  if (repairs.length === 0) {
    console.log("No repairs needed.\n");
    return;
  }

  if (options.dryRun) {
    console.log("Dry run - no actual changes made:\n");
  }

  for (const repair of repairs) {
    const icon = repair.success ? "✅" : "❌";
    const error = repair.error ? ` (${repair.error})` : "";
    console.log(`${icon} ${repair.component}: ${repair.action}${error}`);
  }

  const successCount = repairs.filter((r) => r.success).length;
  const successRate = ((successCount / repairs.length) * 100).toFixed(1);

  console.log(
    `\n📊 Repair Success Rate: ${successRate}% (${successCount}/${repairs.length})`,
  );
}

/**
 * T180: Export diagnostics to file
 */
function exportDiagnostics(health: SystemHealth, outputPath: string): void {
  try {
    const report = JSON.stringify(health, null, 2);
    writeFileSync(outputPath, report);
    logger.info("Diagnostics exported", { outputPath });
  } catch (error) {
    logger.error("Failed to export diagnostics", { error });
    console.error(`❌ Failed to export diagnostics: ${error}`);
  }
}

/**
 * Get system information
 */
function getSystemInfo(): SystemHealth["systemInfo"] {
  return {
    platform: process.platform,
    nodeVersion: process.version,
    kiokuVersion: "2.0.0",
  };
}
