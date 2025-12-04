/**
 * Status Command
 *
 * Displays system health, diagnostics, and operational status.
 */

import { SQLiteAdapter } from "@kioku/api";
import { join } from "path";
import { existsSync, statSync, readdirSync } from "fs";
import { logger } from "../logger";

export async function statusCommand(): Promise<void> {
  const projectPath = process.cwd();
  const contextDir = join(projectPath, ".context");
  const yamlPath = join(contextDir, "project.yaml");
  const dbPath = join(contextDir, "sessions.db");
  const chromaPath = join(contextDir, "chroma");

  // Check if project is initialized
  if (!existsSync(contextDir)) {
    console.warn("❌ Kioku not initialized in this directory.");
    console.warn("   Run `kioku init` first.\n");
    process.exit(1);
  }

  try {
    console.log("\n🏥 Kioku System Health\n");
    console.log("━".repeat(60));

    // 1. Initialization Status
    console.log("\n📋 Initialization");
    const projectYamlExists = existsSync(yamlPath);
    const dbExists = existsSync(dbPath);
    const chromaExists = existsSync(chromaPath);

    console.log(
      `   Project YAML:    ${projectYamlExists ? "✅ Found" : "❌ Missing"}`,
    );
    console.log(`   Database:        ${dbExists ? "✅ Found" : "❌ Missing"}`);
    console.log(
      `   Vector DB:       ${chromaExists ? "✅ Found" : "❌ Missing"}`,
    );

    if (!projectYamlExists || !dbExists) {
      console.log("\n⚠️  System not fully initialized. Run `kioku init`.\n");
      process.exit(1);
    }

    // 2. Database Statistics
    console.log("\n💾 Database");
    const dbSize = statSync(dbPath).size;
    console.log(`   Size:            ${formatBytes(dbSize)}`);

    const sqliteAdapter = new SQLiteAdapter(dbPath);

    // Session stats
    const allSessions = sqliteAdapter.getAllSessions();
    const activeSession = allSessions.find((s) => s.status === "active");
    const completedSessions = allSessions.filter(
      (s) => s.status === "completed",
    );
    const recentSessions = allSessions.filter((s) => {
      const sevenDaysAgo = new Date();
      sevenDaysAgo.setDate(sevenDaysAgo.getDate() - 7);
      return s.startedAt >= sevenDaysAgo;
    });

    console.log(`   Total Sessions:  ${allSessions.length}`);
    console.log(
      `   Active:          ${activeSession ? "🟢 1 session" : "⚪ None"}`,
    );
    console.log(`   Last 7 days:     ${recentSessions.length}`);

    // Discovery stats
    const discoveries = sqliteAdapter.getAllDiscoveries();
    console.log(`   Discoveries:     ${discoveries.length} total`);

    // 3. Context Window
    console.log("\n📊 Context Window");
    const contextItems = sqliteAdapter.getAllContextItems();
    const activeItems = contextItems.filter((item) => item.status === "active");
    const archivedItems = contextItems.filter(
      (item) => item.status === "archived",
    );

    const totalTokens = activeItems.reduce((sum, item) => sum + item.tokens, 0);
    const maxTokens = 100000; // Default context window
    const usage = totalTokens / maxTokens;
    const usagePercent = (usage * 100).toFixed(1);

    console.log(`   Active Items:    ${activeItems.length}`);
    console.log(`   Archived Items:  ${archivedItems.length}`);
    console.log(
      `   Token Usage:     ${totalTokens.toLocaleString()} / ${maxTokens.toLocaleString()}`,
    );
    console.log(`   Capacity:        ${usagePercent}%`);

    if (usage >= 0.8) {
      console.log(`   Status:          ⚠️  High (pruning active)`);
    } else if (usage >= 0.6) {
      console.log(`   Status:          ⚡ Moderate`);
    } else {
      console.log(`   Status:          ✅ Healthy`);
    }

    // 4. Background Services
    console.log("\n⚙️  Background Services");
    console.log(`   Context Scorer:  ℹ️  Runs every 5 minutes`);
    console.log(`   Context Pruner:  ℹ️  Activates at 80% capacity`);
    console.log(`   Discovery Ext:   ℹ️  Runs after each session`);
    console.log(`   Embeddings Gen:  ℹ️  Processes new discoveries`);

    // 5. API Keys
    console.log("\n🔑 API Configuration");
    const openaiKey = process.env.OPENAI_API_KEY;
    const anthropicKey = process.env.ANTHROPIC_API_KEY;

    console.log(
      `   OpenAI Key:      ${openaiKey ? "✅ Configured" : "❌ Missing"}`,
    );
    console.log(
      `   Anthropic Key:   ${anthropicKey ? "✅ Configured" : "⚠️  Optional"}`,
    );

    if (!openaiKey) {
      console.log(
        "\n⚠️  OpenAI API key required for embeddings. Set OPENAI_API_KEY env var.",
      );
    }

    // 6. Storage Size
    console.log("\n💿 Storage");
    const chromaSize = chromaExists ? getDirectorySize(chromaPath) : 0;
    console.log(`   Database:        ${formatBytes(dbSize)}`);
    console.log(`   Vector DB:       ${formatBytes(chromaSize)}`);
    console.log(`   Total:           ${formatBytes(dbSize + chromaSize)}`);

    // 7. Recent Activity
    console.log("\n🕐 Recent Activity");
    if (activeSession) {
      const duration = Math.floor(
        (new Date().getTime() - activeSession.startedAt.getTime()) / 1000 / 60,
      );
      console.log(`   Active Session:  ${duration} minutes ago`);
      console.log(`   Files Accessed:  ${activeSession.filesAccessed.length}`);
    } else {
      const lastSession = completedSessions.sort(
        (a, b) => b.startedAt.getTime() - a.startedAt.getTime(),
      )[0];
      if (lastSession) {
        const lastSessionTime = formatTimeAgo(lastSession.startedAt);
        console.log(`   Last Session:    ${lastSessionTime}`);
      } else {
        console.log(`   Last Session:    Never`);
      }
    }

    console.log("\n" + "━".repeat(60));
    console.log("\n✅ System operational\n");

    sqliteAdapter.close();
  } catch (error) {
    logger.error("Failed to show status", { error });
    console.log("\n❌ Failed to retrieve system status.");
    console.log(
      `   ${error instanceof Error ? error.message : String(error)}\n`,
    );
    process.exit(1);
  }
}

/**
 * Format bytes to human-readable size
 */
function formatBytes(bytes: number): string {
  if (bytes === 0) return "0 B";

  const k = 1024;
  const sizes = ["B", "KB", "MB", "GB"];
  const i = Math.floor(Math.log(bytes) / Math.log(k));

  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(2))} ${sizes[i]}`;
}

/**
 * Get total size of directory recursively
 */
function getDirectorySize(dirPath: string): number {
  if (!existsSync(dirPath)) return 0;

  let totalSize = 0;
  const files = readdirSync(dirPath, { withFileTypes: true });

  for (const file of files) {
    const filePath = join(dirPath, file.name);
    if (file.isDirectory()) {
      totalSize += getDirectorySize(filePath);
    } else {
      totalSize += statSync(filePath).size;
    }
  }

  return totalSize;
}

/**
 * Format time ago
 */
function formatTimeAgo(date: Date): string {
  const now = new Date();
  const diff = now.getTime() - date.getTime();
  const minutes = Math.floor(diff / 1000 / 60);
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
