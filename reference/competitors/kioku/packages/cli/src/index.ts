#!/usr/bin/env bun

/**
 * Kioku CLI Entry Point
 *
 * Command-line interface for Kioku operations.
 */

import { initCommand } from "./commands/init";
import { serveCommand } from "./commands/serve";
import { showCommand } from "./commands/show";
import { statusCommand } from "./commands/status";
import { dashboardCommand } from "./commands/dashboard";
import { setupCommand } from "./commands/setup";
import { doctorCommand } from "./commands/doctor";
import { logger } from "./logger";

async function main(): Promise<void> {
  const command = process.argv[2];
  const args = process.argv.slice(3);

  try {
    switch (command) {
      case "setup": {
        // Parse setup options
        const options: {
          projectType?: string;
          openaiKey?: string;
          anthropicKey?: string;
          editor?: "claude" | "zed";
          skipPrompts?: boolean;
        } = {};

        for (let i = 0; i < args.length; i++) {
          const arg = args[i];
          const nextArg = args[i + 1];

          if (arg === "--project-type" && nextArg) {
            options.projectType = nextArg;
            i++;
          } else if (arg === "--openai-key" && nextArg) {
            options.openaiKey = nextArg;
            i++;
          } else if (arg === "--anthropic-key" && nextArg) {
            options.anthropicKey = nextArg;
            i++;
          } else if (arg === "--editor" && nextArg) {
            if (nextArg === "claude" || nextArg === "zed") {
              options.editor = nextArg;
            }
            i++;
          } else if (arg === "--skip-prompts" || arg === "-y") {
            options.skipPrompts = true;
          }
        }

        await setupCommand(options);
        break;
      }

      case "init":
        await initCommand();
        break;

      case "serve":
        await serveCommand();
        break;

      case "show":
        await showCommand();
        break;

      case "status":
        await statusCommand();
        break;

      case "doctor": {
        // Parse doctor options
        const options: {
          repair?: boolean;
          dryRun?: boolean;
          verbose?: boolean;
          export?: string;
          quick?: boolean;
          check?: string;
        } = {};

        for (let i = 0; i < args.length; i++) {
          const arg = args[i];
          const nextArg = args[i + 1];

          if (arg === "--repair") {
            options.repair = true;
          } else if (arg === "--dry-run") {
            options.dryRun = true;
          } else if (arg === "--verbose" || arg === "-v") {
            options.verbose = true;
          } else if (arg === "--export" && nextArg) {
            options.export = nextArg;
            i++;
          } else if (arg === "--quick") {
            options.quick = true;
          } else if (arg === "--check" && nextArg) {
            options.check = nextArg;
            i++;
          }
        }

        await doctorCommand(options);
        break;
      }

      case "dashboard": {
        // Parse dashboard options
        const options: {
          port?: number;
          apiPort?: number;
          noBrowser?: boolean;
        } = {};

        for (let i = 0; i < args.length; i++) {
          const arg = args[i];
          const nextArg = args[i + 1];

          if (arg === "--port" && nextArg) {
            options.port = parseInt(nextArg, 10);
            i++;
          } else if (arg === "--api-port" && nextArg) {
            options.apiPort = parseInt(nextArg, 10);
            i++;
          } else if (arg === "--no-browser") {
            options.noBrowser = true;
          }
        }

        await dashboardCommand(options);
        break;
      }

      case "help":
      case "--help":
      case "-h":
        showHelp();
        break;

      default:
         
        console.log("Unknown command:", command || "(none)");
         
        console.log("Run 'kioku help' for usage information.\n");
        showHelp();
        process.exit(1);
    }
  } catch (error) {
    logger.error("Command failed", { command, error });
    process.exit(1);
  }
}

function showHelp(): void {
   
  console.log(`
Kioku - AI-Powered Context Memory for Developers

Usage: kioku <command> [options]

Commands:
  setup         Interactive setup wizard (recommended for first-time users)
  init          Initialize Kioku in the current project
  serve         Start MCP server to serve context to AI assistants
  show          Display context status and usage information
  status        Show system health and diagnostics
  doctor        Run health checks and auto-repair system issues
  dashboard     Start visual dashboard web interface
  help          Show this help message

Setup Options:
  --project-type <type>      Project type (web-app, api, fullstack, library, other)
  --openai-key <key>         OpenAI API key (required)
  --anthropic-key <key>      Anthropic API key (optional)
  --editor <editor>          AI editor (claude, zed)
  --skip-prompts, -y         Non-interactive mode (requires all options)

Doctor Options:
  --repair                   Auto-repair detected issues
  --dry-run                  Show what would be repaired without making changes
  --verbose, -v              Show detailed diagnostics
  --export <path>            Export diagnostics report to JSON file
  --quick                    Run quick health check (skip expensive checks)
  --check <component>        Check specific component only

Dashboard Options:
  --port <number>            Dashboard port (default: 3456)
  --api-port <number>        API port (default: 9090)
  --no-browser               Don't auto-open browser

Examples:
  kioku setup                                    # Interactive setup wizard
  kioku setup -y --project-type web-app \\       # Non-interactive setup
    --openai-key sk-xxx --editor claude
  kioku init                                     # Initialize in current directory
  kioku serve                                    # Start MCP server
  kioku show                                     # Show context status
  kioku status                                   # Show system health
  kioku doctor                                   # Run health check
  kioku doctor --repair                          # Run health check and auto-repair
  kioku doctor --dry-run                         # Preview repairs without applying
  kioku doctor --verbose --export report.json    # Detailed diagnostics + export
  kioku dashboard                                # Start dashboard (auto-opens browser)
  kioku dashboard --no-browser                   # Start dashboard without opening browser
  kioku dashboard --port 8080                    # Start dashboard on custom port

For more information, visit: https://github.com/sanzoku-labs/kioku
`);
}

main();
