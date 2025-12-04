/**
 * Project Resource
 *
 * MCP resource that provides project overview context.
 * URI: context://project/overview
 */

import type { ProjectContext } from "domain/models/ProjectContext";

// eslint-disable-next-line @typescript-eslint/no-extraneous-class -- Utility class for formatting, keeping as class for consistency
export class ProjectResource {
  static formatAsMarkdown(context: ProjectContext): string {
    const { project, tech, architecture, modules, metadata } = context;

    return `# ${project.name}

## Project Information
- **Type**: ${project.type}
- **Path**: ${project.path}

## Technology Stack
${tech.stack.length > 0 ? tech.stack.map((t) => `- ${t}`).join("\n") : "- No frameworks detected"}

**Runtime**: ${tech.runtime}
**Package Manager**: ${tech.packageManager}

## Architecture
- **Pattern**: ${architecture.pattern}
- **Description**: ${architecture.description}

## Modules
${
  Object.keys(modules).length > 0
    ? Object.entries(modules)
        .map(([name, mod]) => `- **${name}**: ${mod.description}`)
        .join("\n")
    : "- No modules identified"
}

## Metadata
- **Created**: ${metadata.createdAt.toISOString()}
- **Last Updated**: ${metadata.updatedAt.toISOString()}
- **Last Scanned**: ${metadata.lastScanAt.toISOString()}
`;
  }
}
