/**
 * Module Resource
 *
 * MCP resource that provides detailed module context.
 * URI: context://module/{moduleName}
 */

import type { ModuleContext } from "domain/models/ProjectContext";

// eslint-disable-next-line @typescript-eslint/no-extraneous-class -- Utility class for formatting, keeping as class for consistency
export class ModuleResource {
  static formatAsMarkdown(moduleName: string, module: ModuleContext): string {
    return `# Module: ${moduleName}

## Description
${module.description}

## Key Files
${
  module.keyFiles.length > 0
    ? module.keyFiles
        .map(
          (f) =>
            `- **${f.path}** (${f.role})${f.description ? `: ${f.description}` : ""}`,
        )
        .join("\n")
    : "- No key files identified yet"
}

## Patterns
${
  module.patterns.length > 0
    ? module.patterns.map((p) => `- ${p}`).join("\n")
    : "- No patterns discovered yet"
}

## Business Rules
${
  module.businessRules.length > 0
    ? module.businessRules.map((r) => `- ${r}`).join("\n")
    : "- No business rules documented yet"
}

## Common Issues
${
  module.commonIssues.length > 0
    ? module.commonIssues
        .map(
          (issue) => `
### ${issue.description}
**Solution**: ${issue.solution}
**Discovered**: ${issue.discoveredAt.toISOString()} (Session: ${issue.sessionId})
`,
        )
        .join("\n")
    : "- No common issues documented yet"
}

## Dependencies
${
  module.dependencies.length > 0
    ? module.dependencies.map((d) => `- ${d}`).join("\n")
    : "- No dependencies identified yet"
}
`;
  }

  static getModuleNames(modules: Record<string, ModuleContext>): string[] {
    return Object.keys(modules);
  }
}
