/**
 * Setup Command - Guided onboarding wizard
 *
 * Implements T168-T174: Interactive setup wizard with API key validation,
 * MCP config generation, and automatic initialization.
 */

import prompts from "prompts";
import { existsSync, mkdirSync, writeFileSync, readFileSync } from "fs";
import { join } from "path";
import { homedir } from "os";
import { initCommand } from "./init";
import { logger } from "../logger";

export interface SetupOptions {
  projectType?: string;
  openaiKey?: string;
  anthropicKey?: string;
  editor?: "claude" | "zed";
  skipPrompts?: boolean;
}

interface SetupConfig {
  projectType: string;
  openaiKey: string;
  anthropicKey?: string;
  editor: "claude" | "zed";
}

/**
 * T168: Main setup command entry point
 */
export async function setupCommand(options: SetupOptions = {}): Promise<void> {
  const startTime = Date.now();

  logger.info("Starting Kioku setup wizard...");
  console.log("\n🚀 Welcome to Kioku Setup!\n");
  console.log("This wizard will help you configure Kioku for your project.\n");

  // T173: Detect existing setup
  const existingSetup = await detectExistingSetup();
  if (existingSetup && !options.skipPrompts) {
    const { reconfigure } = await prompts({
      type: "confirm",
      name: "reconfigure",
      message: "Kioku is already configured. Do you want to reconfigure?",
      initial: false,
    });

    if (!reconfigure) {
      console.log(
        "\n✅ Setup cancelled. Your existing configuration is unchanged.",
      );
      return;
    }
  }

  // T169: Interactive prompts (or use provided options)
  const config = await gatherConfiguration(options);

  // T170: Validate API keys
  console.log("\n🔑 Validating API keys...");
  const openaiValid = await validateApiKey(config.openaiKey, "openai");
  if (!openaiValid) {
    console.error(
      "❌ OpenAI API key validation failed. Please check your key and try again.",
    );
    process.exit(1);
  }
  console.log("✅ OpenAI API key validated");

  if (config.anthropicKey) {
    const anthropicValid = await validateApiKey(
      config.anthropicKey,
      "anthropic",
    );
    if (!anthropicValid) {
      console.error(
        "❌ Anthropic API key validation failed. Please check your key and try again.",
      );
      process.exit(1);
    }
    console.log("✅ Anthropic API key validated");
  }

  // T171: Generate MCP config
  console.log("\n📝 Generating MCP configuration...");
  await generateMcpConfig(config);
  console.log(
    `✅ ${config.editor === "claude" ? "Claude Desktop" : "Zed"} configuration created`,
  );

  // Save API keys to environment file
  await saveEnvironmentFile(config);

  // T172: Run init command
  console.log("\n🔧 Initializing Kioku for this project...");
  await initCommand();

  // T174: Display success message
  const duration = ((Date.now() - startTime) / 1000).toFixed(2);
  console.log("\n✨ Setup complete!");
  console.log(`\n📊 Setup completed in ${duration}s\n`);
  displaySuccessMessage(config);

  logger.info("Setup wizard completed successfully", {
    duration: `${duration}s`,
  });
}

/**
 * T169: Gather configuration through interactive prompts or options
 */
async function gatherConfiguration(
  options: SetupOptions,
): Promise<SetupConfig> {
  if (options.skipPrompts) {
    // Non-interactive mode - use provided options
    if (!options.projectType || !options.openaiKey || !options.editor) {
      throw new Error(
        "Non-interactive mode requires: --project-type, --openai-key, and --editor",
      );
    }

    const result: SetupConfig = {
      projectType: options.projectType,
      openaiKey: options.openaiKey,
      editor: options.editor,
    };

    // Only add anthropicKey if it's provided
    if (options.anthropicKey && options.anthropicKey.length > 0) {
      result.anthropicKey = options.anthropicKey;
    }

    return result;
  }

  // Interactive mode - prompt user
  const questions: prompts.PromptObject[] = [
    {
      type: "select",
      name: "projectType",
      message: "What type of project is this?",
      choices: [
        { title: "Web Application", value: "web-app" },
        { title: "API Server", value: "api" },
        { title: "Full-Stack Application", value: "fullstack" },
        { title: "Library/Package", value: "library" },
        { title: "Other", value: "other" },
      ],
      initial: 0,
    },
    {
      type: "text",
      name: "openaiKey",
      message: "Enter your OpenAI API key (required for embeddings):",
      validate: (value: string) =>
        value.length > 0 ? true : "API key is required",
    },
    {
      type: "text",
      name: "anthropicKey",
      message:
        "Enter your Anthropic API key (optional, for AI-powered discovery refinement):",
      initial: "",
    },
    {
      type: "select",
      name: "editor",
      message: "Which AI editor do you use?",
      choices: [
        { title: "Claude Desktop", value: "claude" },
        { title: "Zed", value: "zed" },
      ],
      initial: 0,
    },
  ];

  const answers = await prompts(questions, {
    onCancel: () => {
      console.log("\n❌ Setup cancelled by user");
      process.exit(0);
    },
  });

  // Build result with proper optional property handling
  const result: SetupConfig = {
    projectType: options.projectType || answers.projectType,
    openaiKey: options.openaiKey || answers.openaiKey,
    editor: options.editor || answers.editor,
  };

  // Only add anthropicKey if it's provided
  const anthropicKey = options.anthropicKey || answers.anthropicKey;
  if (anthropicKey && anthropicKey.length > 0) {
    result.anthropicKey = anthropicKey;
  }

  return result;
}

/**
 * T170: Validate API key by making a test request
 */
export async function validateApiKey(
  apiKey: string,
  provider: "openai" | "anthropic",
): Promise<boolean> {
  if (!apiKey || apiKey.length === 0) {
    return false;
  }

  try {
    if (provider === "openai") {
      // Validate OpenAI key format (starts with sk-)
      if (!apiKey.startsWith("sk-")) {
        logger.warn("OpenAI API key validation failed: invalid format");
        return false;
      }

      // Make a test request to OpenAI API
      const response = await fetch("https://api.openai.com/v1/models", {
        method: "GET",
        headers: {
          Authorization: `Bearer ${apiKey}`,
        },
      });

      if (!response.ok) {
        logger.warn("OpenAI API key validation failed", {
          status: response.status,
        });
        return false;
      }

      return true;
    } else if (provider === "anthropic") {
      // Validate Anthropic key format (starts with sk-ant-)
      if (!apiKey.startsWith("sk-ant-")) {
        logger.warn("Anthropic API key validation failed: invalid format");
        return false;
      }

      // Make a test request to Anthropic API (we'll use the messages endpoint with a minimal request)
      const response = await fetch("https://api.anthropic.com/v1/messages", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "x-api-key": apiKey,
          "anthropic-version": "2023-06-01",
        },
        body: JSON.stringify({
          model: "claude-3-haiku-20240307",
          max_tokens: 1,
          messages: [{ role: "user", content: "test" }],
        }),
      });

      // Accept both 200 (success) and 400 (bad request but key is valid)
      // 401/403 means invalid key
      if (response.status === 401 || response.status === 403) {
        logger.warn("Anthropic API key validation failed", {
          status: response.status,
        });
        return false;
      }

      return true;
    }

    return false;
  } catch (error) {
    logger.error("API key validation error", { provider, error });
    return false;
  }
}

/**
 * T171: Generate MCP configuration file for Claude Desktop or Zed
 */
async function generateMcpConfig(config: SetupConfig): Promise<void> {
  const projectRoot = process.cwd();
  const contextDir = join(projectRoot, ".context");

  if (config.editor === "claude") {
    // Claude Desktop config location
    const configDir = join(
      homedir(),
      "Library",
      "Application Support",
      "Claude",
    );
    const configPath = join(configDir, "claude_desktop_config.json");

    // Ensure config directory exists
    if (!existsSync(configDir)) {
      mkdirSync(configDir, { recursive: true });
    }

    // Read existing config or create new
    let existingConfig: Record<string, unknown> = {};
    if (existsSync(configPath)) {
      try {
        const content = readFileSync(configPath, "utf-8");
        existingConfig = JSON.parse(content);
      } catch (error) {
        logger.warn(
          "Failed to parse existing Claude Desktop config, will create new",
          { error },
        );
      }
    }

    // Merge with Kioku MCP server config
    const mcpServers =
      (existingConfig.mcpServers as Record<string, unknown>) || {};
    mcpServers.kioku = {
      command: "bun",
      args: [
        "run",
        join(projectRoot, "src", "infrastructure", "cli", "index.ts"),
        "serve",
      ],
      env: {
        CONTEXT_DIR: contextDir,
        OPENAI_API_KEY: config.openaiKey,
        ...(config.anthropicKey
          ? { ANTHROPIC_API_KEY: config.anthropicKey }
          : {}),
      },
    };

    existingConfig.mcpServers = mcpServers;

    // Write config file
    writeFileSync(configPath, JSON.stringify(existingConfig, null, 2), "utf-8");
    logger.info("Claude Desktop config updated", { configPath });
  } else if (config.editor === "zed") {
    // Zed config location
    const configDir = join(homedir(), ".config", "zed");
    const configPath = join(configDir, "settings.json");

    // Ensure config directory exists
    if (!existsSync(configDir)) {
      mkdirSync(configDir, { recursive: true });
    }

    // Read existing config or create new
    let existingConfig: Record<string, unknown> = {};
    if (existsSync(configPath)) {
      try {
        const content = readFileSync(configPath, "utf-8");
        existingConfig = JSON.parse(content);
      } catch (error) {
        logger.warn("Failed to parse existing Zed config, will create new", {
          error,
        });
      }
    }

    // Merge with Kioku MCP server config
    const contextServers =
      (existingConfig.context_servers as Record<string, unknown>) || {};
    contextServers.kioku = {
      command: {
        path: "bun",
        args: [
          "run",
          join(projectRoot, "src", "infrastructure", "cli", "index.ts"),
          "serve",
        ],
        env: {
          CONTEXT_DIR: contextDir,
          OPENAI_API_KEY: config.openaiKey,
          ...(config.anthropicKey
            ? { ANTHROPIC_API_KEY: config.anthropicKey }
            : {}),
        },
      },
    };

    existingConfig.context_servers = contextServers;

    // Write config file
    writeFileSync(configPath, JSON.stringify(existingConfig, null, 2), "utf-8");
    logger.info("Zed config updated", { configPath });
  }
}

/**
 * Save API keys to .env file in project root
 */
async function saveEnvironmentFile(config: SetupConfig): Promise<void> {
  const projectRoot = process.cwd();
  const envPath = join(projectRoot, ".env");

  let envContent = "";

  // Read existing .env if it exists
  if (existsSync(envPath)) {
    try {
      envContent = readFileSync(envPath, "utf-8");
    } catch (error) {
      logger.warn("Failed to read existing .env file", { error });
    }
  }

  // Update or add API keys
  const lines = envContent.split("\n");
  const updatedLines: string[] = [];
  let openaiKeyFound = false;
  let anthropicKeyFound = false;

  for (const line of lines) {
    if (line.startsWith("OPENAI_API_KEY=")) {
      updatedLines.push(`OPENAI_API_KEY=${config.openaiKey}`);
      openaiKeyFound = true;
    } else if (line.startsWith("ANTHROPIC_API_KEY=")) {
      if (config.anthropicKey) {
        updatedLines.push(`ANTHROPIC_API_KEY=${config.anthropicKey}`);
      } else {
        // Remove line if no Anthropic key provided
        continue;
      }
      anthropicKeyFound = true;
    } else {
      updatedLines.push(line);
    }
  }

  // Add keys if not found in existing file
  if (!openaiKeyFound) {
    updatedLines.push(`OPENAI_API_KEY=${config.openaiKey}`);
  }
  if (!anthropicKeyFound && config.anthropicKey) {
    updatedLines.push(`ANTHROPIC_API_KEY=${config.anthropicKey}`);
  }

  // Write updated .env file
  writeFileSync(envPath, updatedLines.join("\n"), "utf-8");
  logger.info(".env file updated", { envPath });

  // Ensure .env is in .gitignore
  await ensureGitignoreEntry(projectRoot, ".env");
}

/**
 * Ensure a file is listed in .gitignore
 */
async function ensureGitignoreEntry(
  projectRoot: string,
  entry: string,
): Promise<void> {
  const gitignorePath = join(projectRoot, ".gitignore");

  let gitignoreContent = "";
  if (existsSync(gitignorePath)) {
    try {
      gitignoreContent = readFileSync(gitignorePath, "utf-8");
    } catch (error) {
      logger.warn("Failed to read .gitignore", { error });
    }
  }

  // Check if entry already exists
  if (gitignoreContent.includes(entry)) {
    return;
  }

  // Add entry
  const updatedContent = gitignoreContent.trim() + `\n${entry}\n`;
  writeFileSync(gitignorePath, updatedContent, "utf-8");
  logger.info(".gitignore updated", { entry });
}

/**
 * T173: Detect if Kioku is already configured
 */
async function detectExistingSetup(): Promise<boolean> {
  const projectRoot = process.cwd();
  const contextDir = join(projectRoot, ".context");
  const envPath = join(projectRoot, ".env");

  // Check if .context directory exists
  const hasContextDir = existsSync(contextDir);

  // Check if .env file exists with API keys
  let hasApiKeys = false;
  if (existsSync(envPath)) {
    try {
      const envContent = readFileSync(envPath, "utf-8");
      hasApiKeys = envContent.includes("OPENAI_API_KEY=");
    } catch (error) {
      logger.warn("Failed to read .env file during setup detection", { error });
    }
  }

  return hasContextDir || hasApiKeys;
}

/**
 * T174: Display success message with next steps
 */
function displaySuccessMessage(config: SetupConfig): void {
  const editorName = config.editor === "claude" ? "Claude Desktop" : "Zed";

  console.log("┌─────────────────────────────────────────────────────────┐");
  console.log("│                                                         │");
  console.log("│  ✨ Kioku is ready to use!                             │");
  console.log("│                                                         │");
  console.log("└─────────────────────────────────────────────────────────┘");
  console.log("\n📝 What was configured:");
  console.log(`   • Project type: ${config.projectType}`);
  console.log(`   • OpenAI API key: ${maskApiKey(config.openaiKey)}`);
  if (config.anthropicKey) {
    console.log(`   • Anthropic API key: ${maskApiKey(config.anthropicKey)}`);
  }
  console.log(`   • Editor: ${editorName}`);
  console.log(`   • Context directory: .context/`);
  console.log(`   • Environment file: .env`);

  console.log("\n🚀 Next steps:");
  console.log(`   1. Restart ${editorName} to load the new MCP configuration`);
  console.log("   2. Open your project in the editor");
  console.log(
    "   3. Kioku will automatically provide context to your AI assistant",
  );
  console.log("   4. Run 'kioku dashboard' to view your context state");

  console.log("\n📚 Useful commands:");
  console.log("   • kioku status      - Check system health");
  console.log("   • kioku dashboard   - Open visual dashboard");
  console.log("   • kioku show        - Display current context");

  console.log("\n💡 Tips:");
  console.log("   • Kioku learns from every coding session");
  console.log("   • Context is automatically enriched with discoveries");
  console.log("   • Background services keep your context optimized");

  console.log("\n🔗 Learn more: https://github.com/yourusername/kioku");
  console.log("");
}

/**
 * Mask API key for display (show first 7 chars + ***)
 */
function maskApiKey(apiKey: string): string {
  if (apiKey.length <= 10) {
    return "***";
  }
  return apiKey.substring(0, 7) + "***";
}
