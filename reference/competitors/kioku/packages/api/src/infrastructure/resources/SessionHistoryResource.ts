import type { SQLiteAdapter } from "infrastructure/storage/sqlite-adapter";
import type { Session } from "domain/models/Session";

export class SessionHistoryResource {
  constructor(private sqliteAdapter: SQLiteAdapter) {}

  getUri(): string {
    return "context://sessions/history";
  }

  getName(): string {
    return "Session History";
  }

  getDescription(): string {
    return "Recent coding sessions with metadata";
  }

  getMimeType(): string {
    return "text/markdown";
  }

  async read(): Promise<string> {
    const sessions = this.getRecentSessions();

    if (sessions.length === 0) {
      return this.formatEmptyHistory();
    }

    return this.formatSessionHistory(sessions);
  }

  private getRecentSessions(): Session[] {
    // Get all sessions and sort by startedAt descending
    const allSessions: Session[] = [];

    // We need to query the database directly since there's no getAllSessions method
    // For now, we'll try to get active sessions and query the database
    // eslint-disable-next-line @typescript-eslint/no-explicit-any -- MVP: Direct database access, will refactor to proper adapter method post-MVP
    const db = (this.sqliteAdapter as any).db;

    if (!db) {
      return [];
    }

    const rows = db
      .query(
        `
      SELECT * FROM sessions
      ORDER BY started_at DESC
      LIMIT 50
    `,
      )
      .all();

    for (const row of rows) {
      allSessions.push(this.rowToSession(row));
    }

    return allSessions;
  }

  // eslint-disable-next-line @typescript-eslint/no-explicit-any -- MVP: Database row type not strongly typed, will add proper types post-MVP
  private rowToSession(row: any): Session {
    return {
      id: row.id,
      projectId: row.project_id,
      startedAt: new Date(row.started_at),
      ...(row.ended_at !== null && { endedAt: new Date(row.ended_at) }),
      status: row.status,
      filesAccessed: JSON.parse(row.files_accessed),
      topics: JSON.parse(row.topics),
      metadata: JSON.parse(row.metadata),
    };
  }

  private formatEmptyHistory(): string {
    return `# Session History

No sessions found.

Start a session by connecting Claude Desktop to this MCP server.
`;
  }

  private formatSessionHistory(sessions: Session[]): string {
    let markdown = `# Session History

Showing ${sessions.length} recent sessions:

---

`;

    for (const session of sessions) {
      markdown += this.formatSession(session);
      markdown += "\n---\n\n";
    }

    return markdown;
  }

  private formatSession(session: Session): string {
    const duration = this.formatDuration(session);
    const discoveryCount = session.metadata.discoveryCount || 0;
    const toolCallsCount = session.metadata.toolCallsCount || 0;
    const startedAtFormatted = session.startedAt.toISOString().split("T")[0];
    const endedAtFormatted = session.endedAt
      ? session.endedAt.toISOString().split("T")[0]
      : "in progress";
    const topics =
      session.topics.length > 0 ? session.topics.join(", ") : "none";

    return `## Session: ${session.id}

**Project:** ${session.projectId}
**Status:** ${session.status}
**Started:** ${startedAtFormatted}
**Ended:** ${endedAtFormatted}
**Duration:** ${duration}
**Topics:** ${topics}
**Tool Calls:** ${toolCallsCount}
**Discoveries:** ${discoveryCount} discoveries
`;
  }

  private formatDuration(session: Session): string {
    if (!session.endedAt) {
      return "in progress";
    }

    const durationMs = session.endedAt.getTime() - session.startedAt.getTime();
    const durationMinutes = Math.round(durationMs / 1000 / 60);

    if (durationMinutes < 60) {
      return `${durationMinutes} minutes`;
    }

    const hours = Math.floor(durationMinutes / 60);
    const minutes = durationMinutes % 60;

    if (minutes === 0) {
      return `${hours} hours`;
    }

    return `${hours} hours ${minutes} minutes`;
  }
}
