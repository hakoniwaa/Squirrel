/**
 * Session Resource
 *
 * MCP resource that provides current session information.
 * URI: context://session/current
 */

import type { Session } from "domain/models/Session";

// eslint-disable-next-line @typescript-eslint/no-extraneous-class -- Utility class for formatting, keeping as class for consistency
export class SessionResource {
  static formatAsMarkdown(session: Session | null): string {
    if (!session) {
      return `# Current Session

No active session found.

Start using Context Tool to begin tracking your coding session.
`;
    }

    const duration = session.endedAt
      ? Math.floor(
          (session.endedAt.getTime() - session.startedAt.getTime()) / 1000 / 60,
        )
      : Math.floor(
          (new Date().getTime() - session.startedAt.getTime()) / 1000 / 60,
        );

    return `# Current Session

## Session Information
- **ID**: ${session.id}
- **Status**: ${session.status}
- **Started**: ${session.startedAt.toISOString()}
${session.endedAt ? `- **Ended**: ${session.endedAt.toISOString()}` : ""}
- **Duration**: ${duration} minutes

## Files Accessed
${
  session.filesAccessed.length > 0
    ? session.filesAccessed
        .sort((a, b) => b.accessCount - a.accessCount)
        .slice(0, 10)
        .map(
          (f) =>
            `- **${f.path}** (${f.accessCount} accesses, last: ${f.lastAccessedAt.toISOString()})`,
        )
        .join("\n")
    : "- No files accessed yet"
}

## Topics
${
  session.topics.length > 0
    ? session.topics.map((t) => `- ${t}`).join("\n")
    : "- No topics identified yet"
}

## Metadata
- **Tool Calls**: ${session.metadata.toolCallsCount}
- **Discoveries**: ${session.metadata.discoveryCount}
`;
  }
}
