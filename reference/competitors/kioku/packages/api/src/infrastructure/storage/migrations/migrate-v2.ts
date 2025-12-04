/**
 * Migration script: v1.0 → v2.0
 *
 * Purpose: Upgrade database schema from v1.0 to v2.0 while preserving existing data.
 *
 * @module infrastructure/storage/migrations
 */

import { Database } from "bun:sqlite";
import { readFileSync } from "fs";
import { join, dirname } from "path";
import { fileURLToPath } from "url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

export interface MigrationResult {
  success: boolean;
  version: string;
  migrationsApplied: string[];
  errors: string[];
}

/**
 * Run all v2.0 migrations on the database
 */
export async function migrateToV2(dbPath: string): Promise<MigrationResult> {
  const result: MigrationResult = {
    success: false,
    version: "2.0.0",
    migrationsApplied: [],
    errors: [],
  };

  let db: Database | null = null;

  try {
    // Open database
    db = new Database(dbPath);

    // Check current version - first check if metadata table exists
    const metadataExists = db
      .query(
        `
      SELECT name FROM sqlite_master
      WHERE type='table' AND name='metadata'
    `,
      )
      .get();

    let currentVersion: string | undefined;

    if (metadataExists) {
      const versionRow = db
        .query("SELECT value FROM metadata WHERE key = ?")
        .get("schema_version") as { value: string } | undefined;
      currentVersion = versionRow?.value;
    }

    if (currentVersion === "2.0.0") {
      console.log("Database already at v2.0.0, skipping migration");
      result.success = true;
      return result;
    }

    console.log(
      `Migrating database from ${currentVersion || "unknown"} to 2.0.0`,
    );

    // Start transaction
    db.exec("BEGIN TRANSACTION");

    // Run migrations in order
    const migrations = [
      "001-create-chunks-table.sql",
      "002-create-change-events-table.sql",
      "003-create-refined-discoveries-table.sql",
      "004-create-linked-projects-table.sql",
      "005-extend-sessions-table.sql",
    ];

    for (const migration of migrations) {
      try {
        console.log(`Applying migration: ${migration}`);
        const sql = readFileSync(join(__dirname, migration), "utf-8");

        // Execute entire migration file (Bun's exec handles multiple statements)
        db.exec(sql);

        result.migrationsApplied.push(migration);
        console.log(`✓ Applied: ${migration}`);
      } catch (error) {
        const errorMsg = `Failed to apply ${migration}: ${error instanceof Error ? error.message : String(error)}`;
        console.error(errorMsg);
        result.errors.push(errorMsg);
        throw error; // Rollback transaction
      }
    }

    // Update schema version (create metadata table if needed)
    if (!metadataExists) {
      db.exec(`
        CREATE TABLE IF NOT EXISTS metadata (
          key TEXT PRIMARY KEY,
          value TEXT NOT NULL
        )
      `);
      db.query("INSERT INTO metadata (key, value) VALUES (?, ?)").run(
        "schema_version",
        "2.0.0",
      );
    } else {
      db.query("UPDATE metadata SET value = ? WHERE key = ?").run(
        "2.0.0",
        "schema_version",
      );
    }

    // Commit transaction
    db.exec("COMMIT");

    result.success = true;
    console.log("✓ Migration to v2.0.0 complete");
  } catch (error) {
    // Rollback on error
    if (db) {
      try {
        db.exec("ROLLBACK");
        console.log("⚠ Transaction rolled back due to error");
      } catch (rollbackError) {
        console.error("Failed to rollback:", rollbackError);
      }
    }

    const errorMsg = `Migration failed: ${error instanceof Error ? error.message : String(error)}`;
    console.error(errorMsg);
    result.errors.push(errorMsg);
    result.success = false;
  } finally {
    // Close database
    if (db) {
      db.close();
    }
  }

  return result;
}

/**
 * CLI entry point for running migrations manually
 */
if (import.meta.url === `file://${process.argv[1]}`) {
  const dbPath = process.argv[2] || ".context/sessions.db";

  console.log(`Running migrations on: ${dbPath}`);

  migrateToV2(dbPath)
    .then((result) => {
      if (result.success) {
        console.log("\n✓ Migration successful");
        console.log(`Migrations applied: ${result.migrationsApplied.length}`);
        process.exit(0);
      } else {
        console.error("\n✗ Migration failed");
        console.error("Errors:", result.errors);
        process.exit(1);
      }
    })
    .catch((error) => {
      console.error("Unexpected error:", error);
      process.exit(1);
    });
}
