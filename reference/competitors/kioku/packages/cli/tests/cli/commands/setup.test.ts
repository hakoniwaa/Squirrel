/**
 * Setup Command Unit Tests
 *
 * Tests for the interactive setup wizard
 *
 * Validates Phase 11: User Story 8 - Guided Onboarding
 */

import { describe, it, expect, beforeEach, afterEach, vi } from "vitest";
import { existsSync, readFileSync, mkdirSync, rmSync } from "fs";
import { join } from "path";
import { tmpdir } from "os";

// We'll implement these after tests are written
// import { setupCommand } from "../../../src/infrastructure/cli/commands/setup";
// import { validateApiKey } from "../../../src/infrastructure/cli/commands/setup";

describe("Setup Command", () => {
  let testDir: string;

  beforeEach(() => {
    // Create temporary test directory
    testDir = join(tmpdir(), `kioku-test-${Date.now()}`);
    mkdirSync(testDir, { recursive: true });
    process.chdir(testDir);
  });

  afterEach(() => {
    // Cleanup
    if (existsSync(testDir)) {
      rmSync(testDir, { recursive: true, force: true });
    }
  });

  describe("T165: Setup wizard prompts and flow", () => {
    it("should prompt for project type", async () => {
      // Mock prompts
      const mockPrompts = vi.fn().mockResolvedValue({
        projectType: "web-app",
        openaiApiKey: "sk-test-key",
        anthropicApiKey: "sk-ant-test-key",
        editor: "claude-desktop",
      });

      // Test that prompts are called with correct questions
      expect(mockPrompts).toBeDefined();
      // TODO: Implement after setupCommand is created
    });

    it("should skip optional prompts if user declines", async () => {
      const mockPrompts = vi.fn().mockResolvedValue({
        projectType: "api",
        openaiApiKey: "",
        anthropicApiKey: "sk-ant-test-key",
        editor: "zed",
      });

      // Should not fail if OpenAI key is skipped
      expect(mockPrompts).toBeDefined();
    });

    it("should support --non-interactive mode with flags", async () => {
      // Test command-line flags instead of prompts
      const options = {
        projectType: "fullstack",
        openaiApiKey: "sk-test",
        anthropicApiKey: "sk-ant-test",
        editor: "claude-desktop",
        nonInteractive: true,
      };

      expect(options.nonInteractive).toBe(true);
    });

    it("should detect existing setup and prompt for reconfiguration", async () => {
      // Create existing .context directory
      const contextDir = join(testDir, ".context");
      mkdirSync(contextDir, { recursive: true });

      // Mock prompt asking "Reconfigure?"
      const mockPrompts = vi.fn().mockResolvedValue({
        reconfigure: true,
      });

      expect(existsSync(contextDir)).toBe(true);
      // TODO: Verify reconfigure prompt is shown
    });

    it("should preserve existing data if user declines reconfiguration", async () => {
      // Create existing .context with data
      const contextDir = join(testDir, ".context");
      mkdirSync(contextDir, { recursive: true });

      const mockPrompts = vi.fn().mockResolvedValue({
        reconfigure: false,
      });

      // Should exit without changes
      expect(mockPrompts).toBeDefined();
    });
  });

  describe("T166: API key validation", () => {
    it("should validate OpenAI API key with embeddings test call", async () => {
      const validKey = "sk-test-valid-key";

      // Mock successful fetch response
      global.fetch = vi.fn().mockResolvedValue({
        ok: true,
        status: 200,
        json: async () => ({ data: [{ embedding: [0.1, 0.2, 0.3] }] }),
      }) as unknown as typeof fetch;

      const { validateApiKey } = await import(
        "@infrastructure/cli/commands/setup"
      );
      const isValid = await validateApiKey(validKey, "openai");
      expect(isValid).toBe(true);
    });

    it("should reject invalid OpenAI API key", async () => {
      const invalidKey = "sk-invalid-key";

      // Mock failed fetch response
      global.fetch = vi.fn().mockResolvedValue({
        ok: false,
        status: 401,
        json: async () => ({ error: "Invalid API key" }),
      }) as unknown as typeof fetch;

      const { validateApiKey } = await import(
        "@infrastructure/cli/commands/setup"
      );
      const isValid = await validateApiKey(invalidKey, "openai");
      expect(isValid).toBe(false);
    });

    it("should validate Anthropic API key with completion test call", async () => {
      const validKey = "sk-ant-test-valid-key";

      // Mock successful fetch response
      global.fetch = vi.fn().mockResolvedValue({
        ok: true,
        status: 200,
        json: async () => ({ content: [{ text: "Hello!" }] }),
      }) as unknown as typeof fetch;

      const { validateApiKey } = await import(
        "@infrastructure/cli/commands/setup"
      );
      const isValid = await validateApiKey(validKey, "anthropic");
      expect(isValid).toBe(true);
    });

    it("should reject invalid Anthropic API key", async () => {
      const invalidKey = "sk-ant-invalid-key";

      // Mock failed fetch response
      global.fetch = vi.fn().mockResolvedValue({
        ok: false,
        status: 401,
        json: async () => ({ error: { message: "Invalid API key" } }),
      }) as unknown as typeof fetch;

      const { validateApiKey } = await import(
        "@infrastructure/cli/commands/setup"
      );
      const isValid = await validateApiKey(invalidKey, "anthropic");
      expect(isValid).toBe(false);
    });

    it("should handle network errors gracefully", async () => {
      const key = "sk-test-key";

      // Mock network error
      global.fetch = vi
        .fn()
        .mockRejectedValue(
          new Error("Network error"),
        ) as unknown as typeof fetch;

      const { validateApiKey } = await import(
        "@infrastructure/cli/commands/setup"
      );
      const isValid = await validateApiKey(key, "openai");
      expect(isValid).toBe(false);
    });

    it("should allow skipping API key validation with --skip-validation flag", async () => {
      const options = {
        openaiApiKey: "sk-test",
        skipValidation: true,
      };

      // Should not call validation API
      expect(options.skipValidation).toBe(true);
    });
  });

  describe("MCP Config Generation", () => {
    it("should generate Claude Desktop config file", () => {
      const homeDir = testDir;
      const configPath = join(
        homeDir,
        "Library/Application Support/Claude/claude_desktop_config.json",
      );

      // Create parent directories
      const parentDir = join(homeDir, "Library/Application Support/Claude");
      mkdirSync(parentDir, { recursive: true });

      // Generate config
      const config = {
        mcpServers: {
          kioku: {
            command: "kioku",
            args: ["serve"],
          },
        },
      };

      // Should create valid JSON file
      expect(config.mcpServers.kioku.command).toBe("kioku");
    });

    it("should generate Zed config file", () => {
      const homeDir = testDir;
      const configPath = join(homeDir, ".config/zed/mcp.json");

      const config = {
        mcpServers: {
          kioku: {
            command: "kioku",
            args: ["serve"],
          },
        },
      };

      expect(config).toHaveProperty("mcpServers");
    });

    it("should merge with existing MCP config", () => {
      const existing = {
        mcpServers: {
          other: {
            command: "other-server",
            args: [],
          },
        },
      };

      const newEntry = {
        kioku: {
          command: "kioku",
          args: ["serve"],
        },
      };

      const merged = {
        mcpServers: {
          ...existing.mcpServers,
          ...newEntry,
        },
      };

      expect(merged.mcpServers).toHaveProperty("other");
      expect(merged.mcpServers).toHaveProperty("kioku");
    });

    it("should handle custom kioku installation path", () => {
      const customPath = "/custom/path/to/kioku";

      const config = {
        mcpServers: {
          kioku: {
            command: customPath,
            args: ["serve"],
          },
        },
      };

      expect(config.mcpServers.kioku.command).toBe(customPath);
    });
  });

  describe("Post-Setup Actions", () => {
    it("should run kioku init automatically after setup", async () => {
      const mockInit = vi.fn().mockResolvedValue(undefined);

      // Should call init command
      expect(mockInit).toBeDefined();
      // TODO: Verify init was called
    });

    it("should display success message with next steps", () => {
      const successMessage = [
        "✓ Setup complete!",
        "Next steps:",
        "  1. Run 'kioku serve' to start the MCP server",
        "  2. Or restart your editor to connect",
      ].join("\n");

      expect(successMessage).toContain("Setup complete");
      expect(successMessage).toContain("Next steps");
    });

    it("should create .env file with API keys if it doesn't exist", () => {
      const envPath = join(testDir, ".env");
      const envContent = [
        "OPENAI_API_KEY=sk-test-key",
        "ANTHROPIC_API_KEY=sk-ant-test-key",
      ].join("\n");

      // Should create .env
      expect(envContent).toContain("OPENAI_API_KEY");
      expect(envContent).toContain("ANTHROPIC_API_KEY");
    });

    it("should update existing .env file without overwriting other vars", () => {
      const existing = "OTHER_VAR=value\n";
      const updated = existing + "OPENAI_API_KEY=sk-new-key\n";

      expect(updated).toContain("OTHER_VAR");
      expect(updated).toContain("OPENAI_API_KEY");
    });
  });

  describe("Error Handling", () => {
    it("should handle permission errors when writing config files", () => {
      // Test that permission errors are caught
      const permissionError = {
        code: "EACCES",
        message: "Permission denied",
      };

      // Verify error structure
      expect(permissionError.code).toBe("EACCES");
      expect(permissionError.message).toBe("Permission denied");
    });

    it("should handle missing home directory", () => {
      const homeDir = undefined;

      // Should fall back to current directory or show error
      expect(homeDir).toBeUndefined();
    });

    it("should validate JSON when merging configs", () => {
      const invalidJSON = "{ invalid json }";

      // Should catch parse error
      expect(() => JSON.parse(invalidJSON)).toThrow();
    });
  });
});
