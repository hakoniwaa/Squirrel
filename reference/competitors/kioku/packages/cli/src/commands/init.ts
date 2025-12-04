/**
 * Init Command
 *
 * Initialize Context Tool in the current project directory.
 */

import { InitializeProject } from "@kioku/api";
import { logger } from "../logger";

export async function initCommand(): Promise<void> {
  const projectPath = process.cwd();

  try {
    console.log("🔍 Scanning project structure...");

    // Execute use case
    const useCase = new InitializeProject();
    const context = await useCase.execute(projectPath);

    console.log(
      "✓ Detected:",
      context.tech.stack.join(", ") || "No frameworks detected",
    );
    console.log("✓ Found", Object.keys(context.modules).length, "modules");
    console.log("✓ Architecture:", context.architecture.pattern);
    console.log("✓ Generated .context/project.yaml");
    console.log("✓ Initialized databases");
    console.log("\n✓ Context initialized! Run 'kioku serve' to start.");

    logger.info("Project initialized", {
      project: context.project.name,
      modules: Object.keys(context.modules).length,
      techStack: context.tech.stack,
    });
  } catch (error) {
    console.error("❌ Failed to initialize project");

    if (error instanceof Error) {
      console.error("Error:", error.message);
      logger.error("Initialization failed", {
        error: error.message,
        stack: error.stack,
      });
    }

    process.exit(1);
  }
}
