/**
 * Session Manager Use Case
 *
 * Manages coding session lifecycle: start, track activity, auto-save.
 */


import { SQLiteAdapter } from "infrastructure/storage/sqlite-adapter";
// eslint-disable-next-line boundaries/element-types -- MVP: Direct infrastructure usage, will refactor to ports/adapters pattern post-MVP
import { logger } from "../../infrastructure/cli/logger";
import { basename } from "path";
import { randomUUID, createHash } from "crypto";
import type { Session, FileAccess } from "domain/models/Session";
import type { ContextItem } from "domain/models/ContextItem";
import { calculateContextScore, calculateRecencyFactor, normalizeAccessCount } from "domain/calculations/context-scoring";

// Internal session representation with proper FileAccess tracking
interface SimpleSession {
  id: string;
  projectId: string;
  status: "active" | "completed";
  startedAt: Date;
  endedAt?: Date;
  lastActivityAt: Date; // Track last activity for inactivity timeout
  filesAccessed: Map<string, FileAccess>; // Track full FileAccess objects with timestamps
  topics: string[];
  metadata: Record<string, unknown>;
}

export class SessionManager {
  private projectPath: string;
  private projectId: string;
  private sqliteAdapter: SQLiteAdapter;
  private currentSession: SimpleSession | null = null;
  private static readonly INACTIVITY_TIMEOUT_MS = 30 * 60 * 1000; // 30 minutes

  constructor(projectPath: string, sqliteAdapter: SQLiteAdapter) {
    this.projectPath = projectPath;
    this.projectId = basename(projectPath);
    this.sqliteAdapter = sqliteAdapter;
  }

  /**
   * Convert SimpleSession to domain Session format
   * Transforms Map<string, FileAccess> to FileAccess[]
   */
  private toSessionDomain(session: SimpleSession): Session {
    const filesAccessed: FileAccess[] = Array.from(session.filesAccessed.values());

    return {
      id: session.id,
      projectId: session.projectId,
      status: session.status,
      startedAt: session.startedAt,
      ...(session.endedAt !== undefined && { endedAt: session.endedAt }),
      filesAccessed,
      topics: session.topics,
      metadata: {
        toolCallsCount: 0,
        discoveryCount: 0,
        ...(session.metadata as { duration?: number }),
      },
    } as Session;
  }

  async startSession(): Promise<SimpleSession> {
    logger.info("Starting new session", { projectPath: this.projectPath });

    // End any existing active session first
    if (this.currentSession) {
      await this.endSession();
    }

    // Create new session
    const now = new Date();
    const session: SimpleSession = {
      id: randomUUID(),
      projectId: this.projectId,
      status: "active",
      startedAt: now,
      lastActivityAt: now,
      filesAccessed: new Map(),
      topics: [],
      metadata: {},
    };

    // Save to database (convert to domain Session format)
    this.sqliteAdapter.saveSession(this.toSessionDomain(session));

    this.currentSession = session;

    logger.info("Session started", {
      sessionId: session.id,
      timestamp: session.startedAt.toISOString(),
    });

    return session;
  }

  async trackFileAccess(filePath: string): Promise<void> {
    if (!this.currentSession) {
      throw new Error("No active session. Call startSession() first.");
    }

    logger.debug("Tracking file access", {
      filePath,
      sessionId: this.currentSession.id,
    });

    const now = new Date();

    // Update last activity timestamp
    this.currentSession.lastActivityAt = now;

    // Get existing file access or create new one
    const existingAccess = this.currentSession.filesAccessed.get(filePath);

    if (existingAccess) {
      // File already accessed - increment count and update last accessed time
      existingAccess.accessCount += 1;
      existingAccess.lastAccessedAt = now;
    } else {
      // First access to this file
      this.currentSession.filesAccessed.set(filePath, {
        path: filePath,
        accessCount: 1,
        firstAccessedAt: now,
        lastAccessedAt: now,
      });
    }

    // Save to database with updated FileAccess data
    this.sqliteAdapter.saveSession(this.toSessionDomain(this.currentSession));

    // Create/update context item for scoring and pruning
    const fileAccess = this.currentSession.filesAccessed.get(filePath)!;
    await this.createOrUpdateContextItem(filePath, fileAccess);

    logger.debug("File access tracked", {
      filePath,
      accessCount: this.currentSession.filesAccessed.get(filePath)?.accessCount
    });
  }

  async trackTopic(topic: string): Promise<void> {
    if (!this.currentSession) {
      throw new Error("No active session. Call startSession() first.");
    }

    logger.debug("Tracking topic", {
      topic,
      sessionId: this.currentSession.id,
    });

    // Update last activity timestamp
    this.currentSession.lastActivityAt = new Date();

    // Add topic if not already present
    if (!this.currentSession.topics.includes(topic)) {
      this.currentSession.topics.push(topic);
    }

    // Save to database
    this.sqliteAdapter.saveSession(this.toSessionDomain(this.currentSession));

    logger.debug("Topic tracked", { topic });
  }

  async endSession(): Promise<void> {
    if (!this.currentSession) {
      logger.debug("No active session to end");
      return;
    }

    logger.info("Ending session", { sessionId: this.currentSession.id });

    // Mark as completed
    this.currentSession.status = "completed";
    this.currentSession.endedAt = new Date();

    // Calculate duration
    const duration =
      this.currentSession.endedAt.getTime() -
      this.currentSession.startedAt.getTime();
    this.currentSession.metadata.duration = duration;

    // Save to database
    this.sqliteAdapter.saveSession(this.toSessionDomain(this.currentSession));

    logger.info("Session ended", {
      sessionId: this.currentSession.id,
      duration: `${Math.round(duration / 1000)}s`,
      filesAccessed: this.currentSession.filesAccessed.size,
      topics: this.currentSession.topics.length,
    });

    this.currentSession = null;
  }

  async getCurrentSession(): Promise<SimpleSession | undefined> {
    if (this.currentSession) {
      return this.currentSession;
    }

    // Try to load from database
    const dbSession = this.sqliteAdapter.getActiveSession(this.projectId);
    if (dbSession) {
      // Convert FileAccess[] back to Map<string, FileAccess>
      const filesAccessedMap = new Map<string, FileAccess>(
        dbSession.filesAccessed.map((fa) => [fa.path, fa])
      );

      const session: SimpleSession = {
        id: dbSession.id,
        projectId: dbSession.projectId,
        status: dbSession.status as "active" | "completed",
        startedAt: dbSession.startedAt,
        lastActivityAt: dbSession.startedAt, // Use startedAt as fallback
        ...(dbSession.endedAt !== undefined && { endedAt: dbSession.endedAt }),
        filesAccessed: filesAccessedMap,
        topics: dbSession.topics,
        metadata: dbSession.metadata,
      };
      this.currentSession = session;
      return session;
    }

    return undefined;
  }

  async getFileAccessCount(filePath: string): Promise<number> {
    if (!this.currentSession) {
      return 0;
    }

    // Return count from the filesAccessed map
    return this.currentSession.filesAccessed.get(filePath)?.accessCount || 0;
  }

  /**
   * Check if the current session has been inactive for too long
   * and automatically end it if the inactivity timeout has been exceeded.
   *
   * @returns true if session was ended due to inactivity, false otherwise
   */
  async checkInactivity(): Promise<boolean> {
    if (!this.currentSession) {
      return false;
    }

    const now = Date.now();
    const lastActivity = this.currentSession.lastActivityAt.getTime();
    const inactiveDuration = now - lastActivity;

    if (inactiveDuration >= SessionManager.INACTIVITY_TIMEOUT_MS) {
      const inactiveMinutes = Math.round(inactiveDuration / (60 * 1000));

      logger.info("Session inactive timeout reached, ending session", {
        sessionId: this.currentSession.id,
        inactiveMinutes,
        lastActivityAt: this.currentSession.lastActivityAt.toISOString(),
      });

      await this.endSession();
      return true;
    }

    return false;
  }

  /**
   * Get the inactivity timeout in milliseconds
   */
  static getInactivityTimeout(): number {
    return SessionManager.INACTIVITY_TIMEOUT_MS;
  }

  /**
   * Create or update a context item for file access tracking
   * This populates the context_items table for scoring and pruning
   */
  private async createOrUpdateContextItem(
    filePath: string,
    fileAccess: FileAccess,
  ): Promise<void> {
    if (!this.currentSession) {
      return;
    }

    try {
      // Generate stable ID from file path
      const itemId = createHash("sha256").update(filePath).digest("hex");

      // Extract module from file path (e.g., "src/auth/Service.ts" -> "src/auth")
      const pathParts = filePath.split("/");
      const modulePath = pathParts.length > 1 ? pathParts.slice(0, -1).join("/") : undefined;

      // Calculate scoring factors
      const now = new Date();
      const recencyFactor = calculateRecencyFactor(fileAccess.lastAccessedAt, now);
      const accessFactor = normalizeAccessCount(fileAccess.accessCount);
      const score = calculateContextScore(
        fileAccess.lastAccessedAt,
        fileAccess.accessCount,
        now,
      );

      // Estimate tokens (rough approximation: file path length / 4)
      // In production, this should be calculated from actual file content
      const estimatedTokens = Math.ceil(filePath.length / 4);

      const contextItem: ContextItem = {
        id: itemId,
        type: "file",
        content: filePath,
        metadata: {
          source: "file_access",
          ...(modulePath && { module: modulePath }),
          sessionId: this.currentSession.id,
        },
        scoring: {
          score,
          recencyFactor,
          accessFactor,
          lastAccessedAt: fileAccess.lastAccessedAt,
          accessCount: fileAccess.accessCount,
        },
        tokens: estimatedTokens,
        status: "active",
      };

      // Save to database
      this.sqliteAdapter.saveContextItem(contextItem);

      logger.debug("Context item created/updated", {
        itemId,
        filePath,
        score,
        accessCount: fileAccess.accessCount,
      });
    } catch (error) {
      logger.error("Failed to create/update context item", {
        filePath,
        error,
      });
      // Don't throw - context item creation is non-critical
    }
  }
}
