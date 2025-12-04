/**
 * Show Command
 *
 * Displays project context overview, usage stats, and current session info.
 */

import { YAMLHandler, SQLiteAdapter, PruneContext } from "@kioku/api";
import { join } from "path";
import { existsSync } from "fs";
import { logger } from "../logger";

export async function showCommand(): Promise<void> {
  const projectPath = process.cwd();
  const contextDir = join(projectPath, ".context");
  const yamlPath = join(contextDir, "project.yaml");
  const dbPath = join(contextDir, "sessions.db");

  // Check if project is initialized
  if (!existsSync(contextDir)) {
    console.warn("❌ Kioku not initialized in this directory.");
    console.warn("   Run `kioku init` first.\n");
    process.exit(1);
  }

  try {
    // Load project context
    const context = YAMLHandler.loadProjectContext(yamlPath);
    const sqliteAdapter = new SQLiteAdapter(dbPath);

    // Calculate context window usage
    const pruner = new PruneContext(sqliteAdapter);
    const usage = await pruner.calculateUsage();

    // Get active session
    const activeSession = sqliteAdapter.getActiveSession(context.project.name);

    // Get discovery stats
    const discoveries = sqliteAdapter.getAllDiscoveries();
    const discoveryStats = {
      total: discoveries.length,
      byType: discoveries.reduce(
        (acc, d) => {
          acc[d.type] = (acc[d.type] || 0) + 1;
          return acc;
        },
        {} as Record<string, number>,
      ),
    };

    // Display output
    console.log("\n📊 Kioku Status\n");
    console.log("━".repeat(60));

    // Project info
    console.log("\n🏗️  Project");
    console.log(`   Name:         ${context.project.name}`);
    console.log(`   Type:         ${context.project.type}`);
    console.log(`   Path:         ${context.project.path}`);

    // Tech stack
    console.log("\n⚙️  Tech Stack");
    console.log(`   Stack:        ${context.tech.stack.join(", ")}`);
    console.log(`   Runtime:      ${context.tech.runtime}`);
    console.log(`   Package Mgr:  ${context.tech.packageManager}`);

    // Architecture
    console.log("\n🏛️  Architecture");
    console.log(`   Pattern:      ${context.architecture.pattern}`);
    console.log(`   Description:  ${context.architecture.description}`);

    // Modules
    console.log("\n📦 Modules");
    const moduleCount = Object.keys(context.modules).length;
    console.log(`   Total:        ${moduleCount} modules`);

    if (moduleCount > 0) {
      const moduleList = Object.keys(context.modules).slice(0, 5);
      console.log(`   Modules:      ${moduleList.join(", ")}`);
      if (moduleCount > 5) {
        console.log(`                 ... and ${moduleCount - 5} more`);
      }
    }

    // Context window usage
    console.log("\n💾 Context Window");
    const usagePercent = (usage * 100).toFixed(1);
    const usageBar = createProgressBar(usage);
    console.log(`   Usage:        ${usageBar} ${usagePercent}%`);

    const threshold = 80;
    if (usage >= 0.8) {
      console.log(`   Status:       ⚠️  High (pruning will activate)`);
    } else if (usage >= 0.6) {
      console.log(`   Status:       ⚡ Moderate`);
    } else {
      console.log(`   Status:       ✅ Healthy`);
    }

    console.log(`   Threshold:    ${threshold}% (prune at this level)`);

    // Active session
    console.log("\n🔄 Current Session");
    if (activeSession) {
      const duration = calculateDuration(activeSession.startedAt);
      console.log(`   Status:       🟢 Active`);
      console.log(`   Duration:     ${duration}`);
      console.log(
        `   Files:        ${activeSession.filesAccessed.length} accessed`,
      );
      console.log(
        `   Topics:       ${activeSession.topics.join(", ") || "None"}`,
      );
    } else {
      console.log(`   Status:       ⚪ No active session`);
    }

    // Discoveries
    console.log("\n🔍 Discoveries");
    console.log(`   Total:        ${discoveryStats.total} items`);
    if (discoveryStats.total > 0) {
      const types = Object.entries(discoveryStats.byType)
        .map(([type, count]) => `${type}: ${count}`)
        .join(", ");
      console.log(`   By Type:      ${types}`);
    }

    // Metadata
    console.log("\n📅 Metadata");
    console.log(`   Created:      ${formatDate(context.metadata.createdAt)}`);
    console.log(`   Updated:      ${formatDate(context.metadata.updatedAt)}`);
    console.log(`   Last Scan:    ${formatDate(context.metadata.lastScanAt)}`);

    console.log("\n" + "━".repeat(60) + "\n");

    sqliteAdapter.close();
  } catch (error) {
    logger.error("Failed to show context information", { error });
    console.log("\n❌ Failed to load context information.");
    console.log(
      `   ${error instanceof Error ? error.message : String(error)}\n`,
    );
    process.exit(1);
  }
}

/**
 * Create a progress bar for usage percentage
 */
function createProgressBar(usage: number, width = 20): string {
  const filled = Math.round(usage * width);
  const empty = width - filled;

  let bar = "[";
  bar += "█".repeat(filled);
  bar += "░".repeat(empty);
  bar += "]";

  return bar;
}

/**
 * Calculate duration from start time
 */
function calculateDuration(startedAt: Date): string {
  const now = new Date();
  const diff = now.getTime() - startedAt.getTime();

  const seconds = Math.floor(diff / 1000);
  const minutes = Math.floor(seconds / 60);
  const hours = Math.floor(minutes / 60);

  if (hours > 0) {
    return `${hours}h ${minutes % 60}m`;
  } else if (minutes > 0) {
    return `${minutes}m ${seconds % 60}s`;
  } else {
    return `${seconds}s`;
  }
}

/**
 * Format date for display
 */
function formatDate(date: Date): string {
  const now = new Date();
  const diff = now.getTime() - date.getTime();
  const seconds = Math.floor(diff / 1000);
  const minutes = Math.floor(seconds / 60);
  const hours = Math.floor(minutes / 60);
  const days = Math.floor(hours / 24);

  if (days > 0) {
    return `${days} day${days > 1 ? "s" : ""} ago`;
  } else if (hours > 0) {
    return `${hours} hour${hours > 1 ? "s" : ""} ago`;
  } else if (minutes > 0) {
    return `${minutes} minute${minutes > 1 ? "s" : ""} ago`;
  } else {
    return "just now";
  }
}
