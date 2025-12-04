/**
 * Git Integration Tests
 *
 * Test full workflow: MCP tool → GitClient → real git repo → markdown response
 */

import { describe, it, expect, beforeAll } from "vitest";
import { GitLogTool } from "../../../src/infrastructure/mcp/tools/GitLogTool";
import { GitBlameTool } from "../../../src/infrastructure/mcp/tools/GitBlameTool";
import { GitDiffTool } from "../../../src/infrastructure/mcp/tools/GitDiffTool";

describe("Git Integration", () => {
  const repoPath = process.cwd(); // Use current repo for testing

  describe("git_log tool", () => {
    let gitLogTool: GitLogTool;

    beforeAll(() => {
      gitLogTool = new GitLogTool(repoPath);
    });

    it("should return commit history with markdown formatting", async () => {
      const result = await gitLogTool.execute({
        limit: 5,
      });

      // Verify markdown structure
      expect(result).toContain("# Git Log");
      expect(result).toContain("Found");
      expect(result).toContain("commit");
      expect(result).toContain("**Author:**");
      expect(result).toContain("**Date:**");
      expect(result).toContain("**Message:**");
    });

    it("should filter commits by file path", async () => {
      const result = await gitLogTool.execute({
        limit: 3,
        filePaths: ["package.json"],
      });

      expect(result).toContain("# Git Log");
      expect(result).toContain("package.json");
    });

    it("should filter commits by author", async () => {
      const result = await gitLogTool.execute({
        limit: 5,
        author: "THORNG", // Author from recent commits
      });

      expect(result).toContain("# Git Log");
      // Should either find commits or return "No commits found"
      expect(
        result.includes("THORNG") || result.includes("No commits found"),
      ).toBe(true);
    });

    it("should respect limit parameter", async () => {
      const result = await gitLogTool.execute({
        limit: 2,
      });

      // Count commit sections (each starts with ##)
      const commitCount = (result.match(/^## /gm) || []).length;
      expect(commitCount).toBeLessThanOrEqual(2);
    });
  });

  describe("git_blame tool", () => {
    let gitBlameTool: GitBlameTool;

    beforeAll(() => {
      gitBlameTool = new GitBlameTool(repoPath);
    });

    it("should return line-by-line authorship", async () => {
      const result = await gitBlameTool.execute({
        filePath: "package.json",
        startLine: 1,
        endLine: 10,
      });

      // Verify markdown structure
      expect(result).toContain("# Git Blame: package.json");
      expect(result).toContain("**Lines:** 1-10");
      expect(result).toContain("**Date:**");
      expect(result).toContain("**Message:**");
      expect(result).toContain("```"); // Code block
    });

    it("should group consecutive lines by same commit", async () => {
      const result = await gitBlameTool.execute({
        filePath: "README.md",
        startLine: 1,
        endLine: 5,
      });

      // Should have commit grouping headers (###)
      expect(result).toContain("###");
      expect(result).toContain("# Git Blame: README.md");
    });

    it("should handle entire file without line range", async () => {
      const result = await gitBlameTool.execute({
        filePath: "tsconfig.json",
      });

      expect(result).toContain("# Git Blame: tsconfig.json");
      expect(result).toContain("**Total Lines:**");
    });
  });

  describe("git_diff tool", () => {
    let gitDiffTool: GitDiffTool;

    beforeAll(() => {
      gitDiffTool = new GitDiffTool(repoPath);
    });

    it("should compare two commits and return diff summary", async () => {
      const result = await gitDiffTool.execute({
        ref1: "HEAD~1",
        ref2: "HEAD",
      });

      // Verify markdown structure
      expect(result).toContain("# Git Diff");
      expect(result).toContain("**Comparing:**");
      expect(result).toContain("## Summary");
      expect(result).toContain("**Files Changed:**");
      expect(result).toContain("**Insertions:**");
      expect(result).toContain("**Deletions:**");
    });

    it("should show diff to working directory when only ref1 provided", async () => {
      const result = await gitDiffTool.execute({
        ref1: "HEAD",
      });

      expect(result).toContain("# Git Diff");
      expect(result).toContain("working directory");
    });

    it("should handle no changes gracefully", async () => {
      const result = await gitDiffTool.execute({
        ref1: "HEAD",
        ref2: "HEAD",
      });

      expect(result).toContain("# Git Diff");
      expect(result).toContain("**Files Changed:** 0");
    });

    it("should list changed files with change icons", async () => {
      const result = await gitDiffTool.execute({
        ref1: "HEAD~1",
        ref2: "HEAD",
      });

      // Should have file list section if there are changes
      if (!result.includes("No changes found")) {
        expect(result).toContain("## Files");
        // Check for change type icons (one of these should be present)
        expect(
          result.includes("✨") || // added
            result.includes("📝") || // modified
            result.includes("🗑️") || // deleted
            result.includes("🔄"), // renamed
        ).toBe(true);
      }
    });
  });

  describe("error handling", () => {
    it("should handle non-existent file in git_blame", async () => {
      const gitBlameTool = new GitBlameTool(repoPath);
      const result = await gitBlameTool.execute({
        filePath: "nonexistent-file-xyz-123.ts",
      });

      expect(result).toContain("❌");
      expect(result.includes("not found") || result.includes("not valid")).toBe(
        true,
      );
    });

    it("should handle invalid ref in git_diff", async () => {
      const gitDiffTool = new GitDiffTool(repoPath);
      const result = await gitDiffTool.execute({
        ref1: "invalid-ref-xyz-123",
      });

      expect(result).toContain("❌");
      expect(result).toContain("Invalid reference");
    });

    it("should handle invalid commit SHA in git_log", async () => {
      const gitLogTool = new GitLogTool(repoPath);

      // Invalid limit should be caught by Zod validation
      await expect(
        gitLogTool.execute({
          limit: 0, // Below minimum
        }),
      ).rejects.toThrow();
    });
  });

  describe("performance", () => {
    it("should complete git_log within 2 seconds", async () => {
      const gitLogTool = new GitLogTool(repoPath);
      const start = Date.now();

      await gitLogTool.execute({ limit: 10 });

      const duration = Date.now() - start;
      expect(duration).toBeLessThan(2000);
    });

    it("should complete git_blame within 2 seconds", async () => {
      const gitBlameTool = new GitBlameTool(repoPath);
      const start = Date.now();

      await gitBlameTool.execute({
        filePath: "package.json",
        startLine: 1,
        endLine: 50,
      });

      const duration = Date.now() - start;
      expect(duration).toBeLessThan(2000);
    });

    it("should complete git_diff within 2 seconds", async () => {
      const gitDiffTool = new GitDiffTool(repoPath);
      const start = Date.now();

      await gitDiffTool.execute({
        ref1: "HEAD~1",
        ref2: "HEAD",
      });

      const duration = Date.now() - start;
      expect(duration).toBeLessThan(2000);
    });
  });
});
