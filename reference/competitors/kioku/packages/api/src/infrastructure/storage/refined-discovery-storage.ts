/**
 * RefinedDiscoveryStorage - SQLite storage for AI-refined discoveries
 *
 * Purpose: CRUD operations for refined_discoveries table.
 * Layer: Infrastructure (database adapter)
 * Used by: AIDiscoveryService, background services
 *
 * @module infrastructure/storage
 */

import { Database } from "bun:sqlite";
import type { RefinedDiscovery } from "domain/models/RefinedDiscovery";
import type { DiscoveryType } from "domain/models/RefinedDiscovery";
import { StorageError } from "@kioku/shared";
import { logger } from "../cli/logger";
import { randomUUID } from "crypto";

export class RefinedDiscoveryStorage {
  private db: Database;

  constructor(dbPath: string) {
    try {
      this.db = new Database(dbPath, { create: true });
      this.db.exec("PRAGMA journal_mode = WAL");
      this.db.exec("PRAGMA foreign_keys = ON");
      this.initializeTable();
      logger.info("RefinedDiscoveryStorage initialized", { dbPath });
    } catch (error) {
      throw new StorageError(
        "Failed to initialize RefinedDiscoveryStorage",
        error as Error,
      );
    }
  }

  private initializeTable(): void {
    // Read and execute migration
    const migrationSQL = `
      CREATE TABLE IF NOT EXISTS refined_discoveries (
        id TEXT PRIMARY KEY,
        session_id TEXT NOT NULL,
        raw_content TEXT NOT NULL,
        refined_content TEXT NOT NULL,
        type TEXT NOT NULL,
        confidence REAL NOT NULL,
        supporting_evidence TEXT NOT NULL,
        suggested_module TEXT,
        ai_model TEXT NOT NULL,
        tokens_used INTEGER NOT NULL,
        processing_time INTEGER NOT NULL,
        accepted BOOLEAN NOT NULL DEFAULT 0,
        applied_at INTEGER,
        created_at INTEGER NOT NULL,
        updated_at INTEGER NOT NULL
      );

      CREATE INDEX IF NOT EXISTS idx_refined_discoveries_session ON refined_discoveries(session_id);
      CREATE INDEX IF NOT EXISTS idx_refined_discoveries_confidence ON refined_discoveries(confidence);
      CREATE INDEX IF NOT EXISTS idx_refined_discoveries_accepted ON refined_discoveries(accepted);
      CREATE INDEX IF NOT EXISTS idx_refined_discoveries_created ON refined_discoveries(created_at);
    `;

    this.db.exec(migrationSQL);
  }

  /**
   * Save a refined discovery
   */
  async save(
    discovery: Omit<RefinedDiscovery, "id" | "createdAt" | "updatedAt">,
  ): Promise<RefinedDiscovery> {
    try {
      const id = randomUUID();
      const now = Date.now();

      const stmt = this.db.prepare(`
        INSERT INTO refined_discoveries (
          id, session_id, raw_content, refined_content, type,
          confidence, supporting_evidence, suggested_module,
          ai_model, tokens_used, processing_time, accepted,
          applied_at, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
      `);

      stmt.run(
        id,
        discovery.sessionId,
        discovery.rawContent,
        discovery.refinedContent,
        discovery.type,
        discovery.confidence,
        discovery.supportingEvidence,
        discovery.suggestedModule || null,
        discovery.aiModel,
        discovery.tokensUsed,
        discovery.processingTime,
        discovery.accepted ? 1 : 0,
        discovery.appliedAt ? discovery.appliedAt.getTime() : null,
        now,
        now,
      );

      logger.debug("Refined discovery saved", {
        id,
        sessionId: discovery.sessionId,
        type: discovery.type,
        confidence: discovery.confidence,
      });

      return {
        id,
        ...discovery,
        createdAt: new Date(now),
        updatedAt: new Date(now),
      };
    } catch (error) {
      logger.error("Failed to save refined discovery", { error });
      throw new StorageError(
        "Failed to save refined discovery",
        error as Error,
      );
    }
  }

  /**
   * Find discovery by ID
   */
  async findById(id: string): Promise<RefinedDiscovery | null> {
    try {
      const stmt = this.db.prepare(`
        SELECT * FROM refined_discoveries WHERE id = ?
      `);

      const row = stmt.get(id) as Record<string, unknown> | undefined;

      if (!row) {
        return null;
      }

      return this.mapRowToDiscovery(row);
    } catch (error) {
      logger.error("Failed to find refined discovery by id", { error, id });
      throw new StorageError(
        "Failed to find refined discovery",
        error as Error,
      );
    }
  }

  /**
   * Find all discoveries for a session
   */
  async findBySessionId(sessionId: string): Promise<RefinedDiscovery[]> {
    try {
      const stmt = this.db.prepare(`
        SELECT * FROM refined_discoveries
        WHERE session_id = ?
        ORDER BY created_at DESC
      `);

      const rows = stmt.all(sessionId) as Record<string, unknown>[];

      return rows.map((row) => this.mapRowToDiscovery(row));
    } catch (error) {
      logger.error("Failed to find discoveries by session", {
        error,
        sessionId,
      });
      throw new StorageError(
        "Failed to find discoveries by session",
        error as Error,
      );
    }
  }

  /**
   * Find discoveries above confidence threshold
   */
  async findByConfidenceThreshold(
    threshold: number,
  ): Promise<RefinedDiscovery[]> {
    try {
      const stmt = this.db.prepare(`
        SELECT * FROM refined_discoveries
        WHERE confidence >= ?
        ORDER BY confidence DESC, created_at DESC
      `);

      const rows = stmt.all(threshold) as Record<string, unknown>[];

      return rows.map((row) => this.mapRowToDiscovery(row));
    } catch (error) {
      logger.error("Failed to find discoveries by confidence", {
        error,
        threshold,
      });
      throw new StorageError(
        "Failed to find discoveries by confidence",
        error as Error,
      );
    }
  }

  /**
   * Mark discovery as accepted
   */
  async markAsAccepted(id: string): Promise<void> {
    try {
      const stmt = this.db.prepare(`
        UPDATE refined_discoveries
        SET accepted = 1, updated_at = ?
        WHERE id = ?
      `);

      stmt.run(Date.now(), id);

      logger.debug("Discovery marked as accepted", { id });
    } catch (error) {
      logger.error("Failed to mark discovery as accepted", { error, id });
      throw new StorageError(
        "Failed to mark discovery as accepted",
        error as Error,
      );
    }
  }

  /**
   * Mark discovery as applied to project.yaml
   */
  async markAsApplied(id: string, appliedAt: Date): Promise<void> {
    try {
      const stmt = this.db.prepare(`
        UPDATE refined_discoveries
        SET applied_at = ?, updated_at = ?
        WHERE id = ?
      `);

      stmt.run(appliedAt.getTime(), Date.now(), id);

      logger.debug("Discovery marked as applied", { id, appliedAt });
    } catch (error) {
      logger.error("Failed to mark discovery as applied", { error, id });
      throw new StorageError(
        "Failed to mark discovery as applied",
        error as Error,
      );
    }
  }

  /**
   * Count discoveries for a session
   */
  async countBySession(sessionId: string): Promise<number> {
    try {
      const stmt = this.db.prepare(`
        SELECT COUNT(*) as count
        FROM refined_discoveries
        WHERE session_id = ?
      `);

      const result = stmt.get(sessionId) as { count: number };

      return result.count;
    } catch (error) {
      logger.error("Failed to count discoveries", { error, sessionId });
      throw new StorageError("Failed to count discoveries", error as Error);
    }
  }

  /**
   * Close database connection
   */
  close(): void {
    this.db.close();
    logger.debug("RefinedDiscoveryStorage closed");
  }

  /**
   * Map database row to RefinedDiscovery domain model
   */
  private mapRowToDiscovery(row: Record<string, unknown>): RefinedDiscovery {
    const discovery: RefinedDiscovery = {
      id: row.id as string,
      sessionId: row.session_id as string,
      rawContent: row.raw_content as string,
      refinedContent: row.refined_content as string,
      type: row.type as DiscoveryType,
      confidence: row.confidence as number,
      supportingEvidence: row.supporting_evidence as string,
      aiModel: row.ai_model as string,
      tokensUsed: row.tokens_used as number,
      processingTime: row.processing_time as number,
      accepted: Boolean(row.accepted),
      createdAt: new Date(row.created_at as string),
      updatedAt: new Date(row.updated_at as string),
    };

    // Only set optional fields if they exist
    if (row.suggested_module) {
      discovery.suggestedModule = row.suggested_module as string;
    }

    if (row.applied_at) {
      discovery.appliedAt = new Date(row.applied_at as string);
    }

    return discovery;
  }
}
