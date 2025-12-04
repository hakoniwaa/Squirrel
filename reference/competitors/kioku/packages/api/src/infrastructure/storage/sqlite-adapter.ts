import { Database } from "bun:sqlite";
import type { Session } from "domain/models/Session";
import type { Discovery } from "domain/models/Discovery";
import type { ContextItem } from "domain/models/ContextItem";
import { StorageError } from "@kioku/shared";
import { logger } from "../cli/logger";

export class SQLiteAdapter {
  private db: Database;

  constructor(dbPath: string) {
    try {
      this.db = new Database(dbPath, { create: true });
      this.db.exec("PRAGMA journal_mode = WAL");
      this.db.exec("PRAGMA foreign_keys = ON");
      this.initializeTables();
      logger.info("SQLite database initialized", { dbPath });
    } catch (error) {
      throw new StorageError(
        "Failed to initialize SQLite database",
        error as Error,
      );
    }
  }

  private initializeTables(): void {
    // Sessions table
    this.db.exec(`
      CREATE TABLE IF NOT EXISTS sessions (
        id TEXT PRIMARY KEY,
        project_id TEXT NOT NULL,
        started_at INTEGER NOT NULL,
        ended_at INTEGER,
        status TEXT NOT NULL CHECK(status IN ('active', 'completed', 'archived')),
        files_accessed TEXT NOT NULL DEFAULT '[]',
        topics TEXT NOT NULL DEFAULT '[]',
        metadata TEXT NOT NULL DEFAULT '{}',
        created_at INTEGER NOT NULL DEFAULT (unixepoch() * 1000),
        updated_at INTEGER NOT NULL DEFAULT (unixepoch() * 1000)
      )
    `);

    this.db.exec(`
      CREATE INDEX IF NOT EXISTS idx_sessions_project ON sessions(project_id)
    `);
    this.db.exec(`
      CREATE INDEX IF NOT EXISTS idx_sessions_status ON sessions(status)
    `);
    this.db.exec(`
      CREATE INDEX IF NOT EXISTS idx_sessions_started ON sessions(started_at DESC)
    `);

    // Discoveries table
    this.db.exec(`
      CREATE TABLE IF NOT EXISTS discoveries (
        id TEXT PRIMARY KEY,
        session_id TEXT NOT NULL,
        type TEXT NOT NULL CHECK(type IN ('pattern', 'rule', 'decision', 'issue')),
        content TEXT NOT NULL,
        module TEXT,
        context_json TEXT NOT NULL DEFAULT '{}',
        embedding_id TEXT,
        embedding_model TEXT,
        created_at INTEGER NOT NULL DEFAULT (unixepoch() * 1000),
        FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE
      )
    `);

    this.db.exec(`
      CREATE INDEX IF NOT EXISTS idx_discoveries_session ON discoveries(session_id)
    `);
    this.db.exec(`
      CREATE INDEX IF NOT EXISTS idx_discoveries_type ON discoveries(type)
    `);
    this.db.exec(`
      CREATE INDEX IF NOT EXISTS idx_discoveries_module ON discoveries(module)
    `);
    this.db.exec(`
      CREATE INDEX IF NOT EXISTS idx_discoveries_created ON discoveries(created_at DESC)
    `);

    // Context items table
    this.db.exec(`
      CREATE TABLE IF NOT EXISTS context_items (
        id TEXT PRIMARY KEY,
        type TEXT NOT NULL CHECK(type IN ('file', 'module', 'discovery', 'session')),
        content TEXT NOT NULL,
        metadata_json TEXT NOT NULL DEFAULT '{}',
        score REAL NOT NULL DEFAULT 0.0,
        recency_factor REAL NOT NULL DEFAULT 0.0,
        access_factor REAL NOT NULL DEFAULT 0.0,
        last_accessed_at INTEGER NOT NULL,
        access_count INTEGER NOT NULL DEFAULT 0,
        tokens INTEGER NOT NULL DEFAULT 0,
        status TEXT NOT NULL CHECK(status IN ('active', 'archived')),
        created_at INTEGER NOT NULL DEFAULT (unixepoch() * 1000),
        updated_at INTEGER NOT NULL DEFAULT (unixepoch() * 1000)
      )
    `);

    this.db.exec(`
      CREATE INDEX IF NOT EXISTS idx_context_items_type ON context_items(type)
    `);
    this.db.exec(`
      CREATE INDEX IF NOT EXISTS idx_context_items_status ON context_items(status)
    `);
    this.db.exec(`
      CREATE INDEX IF NOT EXISTS idx_context_items_score ON context_items(score DESC)
    `);
    this.db.exec(`
      CREATE INDEX IF NOT EXISTS idx_context_items_last_accessed ON context_items(last_accessed_at DESC)
    `);
  }

  // Session methods
  saveSession(session: Session): void {
    try {
      const stmt = this.db.prepare(`
        INSERT OR REPLACE INTO sessions
        (id, project_id, started_at, ended_at, status, files_accessed, topics, metadata, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
      `);

      stmt.run(
        session.id,
        session.projectId,
        session.startedAt.getTime(),
        session.endedAt?.getTime() || null,
        session.status,
        JSON.stringify(session.filesAccessed),
        JSON.stringify(session.topics),
        JSON.stringify(session.metadata),
        Date.now(),
      );

      logger.debug("Session saved", { sessionId: session.id });
    } catch (error) {
      throw new StorageError("Failed to save session", error as Error);
    }
  }

  getSession(id: string): Session | undefined {
    try {
      const stmt = this.db.prepare(`
        SELECT * FROM sessions WHERE id = ?
      `);

      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      const row = stmt.get(id) as any;
      if (!row) return undefined;

      return {
        id: row.id,
        projectId: row.project_id,
        startedAt: new Date(row.started_at),
        endedAt: row.ended_at ? new Date(row.ended_at) : undefined,
        status: row.status,
        filesAccessed: JSON.parse(row.files_accessed),
        topics: JSON.parse(row.topics),
        metadata: JSON.parse(row.metadata),
      } as Session;
    } catch (error) {
      throw new StorageError("Failed to get session", error as Error);
    }
  }

  getActiveSession(projectId: string): Session | undefined {
    try {
      const stmt = this.db.prepare(`
        SELECT * FROM sessions
        WHERE project_id = ? AND status = 'active'
        ORDER BY started_at DESC
        LIMIT 1
      `);

      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      const row = stmt.get(projectId) as any;
      if (!row) return undefined;

      return {
        id: row.id,
        projectId: row.project_id,
        startedAt: new Date(row.started_at),
        endedAt: row.ended_at ? new Date(row.ended_at) : undefined,
        status: row.status,
        filesAccessed: JSON.parse(row.files_accessed),
        topics: JSON.parse(row.topics),
        metadata: JSON.parse(row.metadata),
      } as Session;
    } catch (error) {
      throw new StorageError("Failed to get active session", error as Error);
    }
  }

  getAllSessions(): Session[] {
    try {
      const stmt = this.db.prepare(`
        SELECT * FROM sessions
        ORDER BY started_at DESC
      `);

      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      const rows = stmt.all() as any[];

      return rows.map(
        (row) =>
          ({
            id: row.id,
            projectId: row.project_id,
            startedAt: new Date(row.started_at),
            endedAt: row.ended_at ? new Date(row.ended_at) : undefined,
            status: row.status,
            filesAccessed: JSON.parse(row.files_accessed),
            topics: JSON.parse(row.topics),
            metadata: JSON.parse(row.metadata),
          }) as Session,
      );
    } catch (error) {
      throw new StorageError("Failed to get all sessions", error as Error);
    }
  }

  // Discovery methods
  saveDiscovery(discovery: Discovery): void {
    try {
      const stmt = this.db.prepare(`
        INSERT INTO discoveries
        (id, session_id, type, content, module, context_json, embedding_id, embedding_model)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
      `);

      stmt.run(
        discovery.id,
        discovery.sessionId,
        discovery.type,
        discovery.content,
        discovery.module || null,
        JSON.stringify(discovery.context),
        discovery.embedding?.id || null,
        discovery.embedding?.model || null,
      );

      logger.debug("Discovery saved", {
        discoveryId: discovery.id,
        type: discovery.type,
      });
    } catch (error) {
      throw new StorageError("Failed to save discovery", error as Error);
    }
  }

  getDiscoveriesBySession(sessionId: string): Discovery[] {
    try {
      const stmt = this.db.prepare(`
        SELECT * FROM discoveries WHERE session_id = ?
      `);

      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      const rows = stmt.all(sessionId) as any[];

      return rows.map((row) => ({
        id: row.id,
        sessionId: row.session_id,
        type: row.type,
        content: row.content,
        module: row.module || undefined,
        context: JSON.parse(row.context_json),
        embedding: row.embedding_id
          ? {
              id: row.embedding_id,
              model: row.embedding_model,
              dimensions: 1536,
            }
          : undefined,
        createdAt: new Date(row.created_at),
      })) as Discovery[];
    } catch (error) {
      throw new StorageError("Failed to get discoveries", error as Error);
    }
  }

  getAllDiscoveries(): Discovery[] {
    try {
      const stmt = this.db.prepare(`
        SELECT * FROM discoveries ORDER BY created_at DESC
      `);

      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      const rows = stmt.all() as any[];

      return rows.map((row) => ({
        id: row.id,
        sessionId: row.session_id,
        type: row.type,
        content: row.content,
        module: row.module || undefined,
        context: JSON.parse(row.context_json),
        embedding: row.embedding_id
          ? {
              id: row.embedding_id,
              model: row.embedding_model,
              dimensions: 1536,
            }
          : undefined,
        createdAt: new Date(row.created_at),
      })) as Discovery[];
    } catch (error) {
      throw new StorageError("Failed to get all discoveries", error as Error);
    }
  }

  // Context item methods
  saveContextItem(item: ContextItem): void {
    try {
      const stmt = this.db.prepare(`
        INSERT OR REPLACE INTO context_items
        (id, type, content, metadata_json, score, recency_factor, access_factor,
         last_accessed_at, access_count, tokens, status, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
      `);

      stmt.run(
        item.id,
        item.type,
        item.content,
        JSON.stringify(item.metadata),
        item.scoring.score,
        item.scoring.recencyFactor,
        item.scoring.accessFactor,
        item.scoring.lastAccessedAt.getTime(),
        item.scoring.accessCount,
        item.tokens,
        item.status,
        Date.now(),
      );

      logger.debug("Context item saved", { itemId: item.id, type: item.type });
    } catch (error) {
      throw new StorageError("Failed to save context item", error as Error);
    }
  }

  getContextItemsByStatus(status: "active" | "archived"): ContextItem[] {
    try {
      const stmt = this.db.prepare(`
        SELECT * FROM context_items WHERE status = ? ORDER BY score DESC
      `);

      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      const rows = stmt.all(status) as any[];

      return rows.map((row) => ({
        id: row.id,
        type: row.type,
        content: row.content,
        metadata: JSON.parse(row.metadata_json),
        scoring: {
          score: row.score,
          recencyFactor: row.recency_factor,
          accessFactor: row.access_factor,
          lastAccessedAt: new Date(row.last_accessed_at),
          accessCount: row.access_count,
        },
        tokens: row.tokens,
        status: row.status,
      }));
    } catch (error) {
      throw new StorageError("Failed to get context items", error as Error);
    }
  }

  getAllContextItems(): ContextItem[] {
    try {
      const stmt = this.db.prepare(`
        SELECT * FROM context_items ORDER BY score DESC
      `);

      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      const rows = stmt.all() as any[];

      return rows.map((row) => ({
        id: row.id,
        type: row.type,
        content: row.content,
        metadata: JSON.parse(row.metadata_json),
        scoring: {
          score: row.score,
          recencyFactor: row.recency_factor,
          accessFactor: row.access_factor,
          lastAccessedAt: new Date(row.last_accessed_at),
          accessCount: row.access_count,
        },
        tokens: row.tokens,
        status: row.status,
      }));
    } catch (error) {
      throw new StorageError("Failed to get all context items", error as Error);
    }
  }

  /**
   * Get active sessions older than a specific timestamp
   * Used for cleanup operations
   */
  getActiveSessionsOlderThan(cutoffTime: number): Array<{
    id: string;
    project_id: string;
    started_at: number;
  }> {
    try {
      const query = `
        SELECT id, project_id, started_at
        FROM sessions
        WHERE status = 'active' AND started_at < ?
        ORDER BY started_at ASC
      `;

      const rows = this.db.query(query).all(cutoffTime) as Array<{
        id: string;
        project_id: string;
        started_at: number;
      }>;

      return rows;
    } catch (error) {
      throw new StorageError(`Failed to query old sessions: ${error}`, error as Error);
    }
  }

  /**
   * Mark a session as completed with end time
   * Used for cleanup operations
   */
  completeSession(sessionId: string, endedAt: number, duration: number): void {
    try {
      const updateQuery = `
        UPDATE sessions
        SET
          status = 'completed',
          ended_at = ?,
          metadata = json_set(
            COALESCE(metadata, '{}'),
            '$.duration', ?
          ),
          updated_at = ?
        WHERE id = ?
      `;

      this.db.run(updateQuery, [endedAt, duration, Date.now(), sessionId]);

      logger.debug("Session marked as completed", { sessionId, endedAt, duration });
    } catch (error) {
      throw new StorageError(`Failed to complete session: ${error}`, error as Error);
    }
  }

  close(): void {
    this.db.close();
  }
}
