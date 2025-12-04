/**
 * File Watcher Integration Tests
 *
 * Tests the full workflow: file change → detection → re-chunk → re-embed → search
 * This validates that real-time context updates work end-to-end
 */

import { describe, it, expect, beforeEach, afterEach } from "vitest";
import { FileWatcherService } from "../../../src/infrastructure/file-watcher/FileWatcherService";
import { ChunkingService } from "../../../src/application/services/ChunkingService";
import { ChunkStorage } from "@kioku/api/infrastructure/storage/chunk-storage";
import { EmbeddingService } from "../../../src/application/services/EmbeddingService";
import { FileEventType } from "../../../src/domain/models/ChangeEvent";
import type { ChangeEvent } from "../../../src/domain/models/ChangeEvent";
import * as fs from "fs/promises";
import * as path from "path";
import * as os from "os";

describe("File Watcher Integration", () => {
  let watcher: FileWatcherService;
  let chunkingService: ChunkingService;
  let chunkStorage: ChunkStorage;
  let embeddingService: EmbeddingService;
  let testDir: string;
  let dbPath: string;

  beforeEach(async () => {
    // Create temporary test directory
    testDir = await fs.mkdtemp(path.join(os.tmpdir(), "kioku-watcher-test-"));

    // Initialize database path
    dbPath = path.join(testDir, "test.db");

    // Create chunks table manually (since ChunkStorage doesn't auto-create it)
    const { Database } = await import("bun:sqlite");
    const db = new Database(dbPath);
    db.exec(`
      CREATE TABLE IF NOT EXISTS chunks (
        id TEXT PRIMARY KEY,
        file_path TEXT NOT NULL,
        type TEXT NOT NULL,
        name TEXT NOT NULL,
        start_line INTEGER NOT NULL,
        end_line INTEGER NOT NULL,
        content_start_line INTEGER NOT NULL,
        content_end_line INTEGER NOT NULL,
        code TEXT NOT NULL,
        content_hash TEXT NOT NULL,
        parent_chunk_id TEXT,
        nesting_level INTEGER NOT NULL,
        scope_path TEXT NOT NULL,
        metadata TEXT NOT NULL,
        embedding_id TEXT,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
      )
    `);
    db.close();

    // Initialize services
    chunkStorage = new ChunkStorage(dbPath);
    embeddingService = new EmbeddingService();
    chunkingService = new ChunkingService(chunkStorage, embeddingService);
    watcher = new FileWatcherService();
  });

  afterEach(async () => {
    if (watcher) {
      await watcher.stop();
    }

    // Clean up test directory
    try {
      await fs.rm(testDir, { recursive: true, force: true });
    } catch {
      // Ignore cleanup errors
    }
  });

  describe("T079: Full workflow - save file → detect change → re-chunk → re-embed → search", () => {
    it("should detect file addition and process it", async () => {
      const processedFiles: string[] = [];

      // Register handler to process new files
      watcher.on(FileEventType.ADD, async (event: ChangeEvent) => {
        const code = await fs.readFile(event.filePath, "utf-8");
        await chunkingService.processFile(event.filePath, code);
        processedFiles.push(event.filePath);
      });

      // Start watching
      await watcher.start(testDir);

      // Create a new TypeScript file
      const testFile = path.join(testDir, "new-module.ts");
      const code = `
export function calculateTotal(items: number[]): number {
  return items.reduce((sum, item) => sum + item, 0);
}

export function formatCurrency(amount: number): string {
  return \`$\${amount.toFixed(2)}\`;
}
      `.trim();

      await fs.writeFile(testFile, code);

      // Wait for file to be processed
      await new Promise((resolve) => setTimeout(resolve, 1000));

      // Verify file was detected and processed
      expect(processedFiles.length).toBe(1);
      expect(processedFiles[0]).toBe(testFile);

      // Verify chunks were created
      const chunks = await chunkStorage.getChunksByFile(testFile);
      expect(chunks.length).toBe(2); // calculateTotal and formatCurrency
      expect(chunks.some((c) => c.name === "calculateTotal")).toBe(true);
      expect(chunks.some((c) => c.name === "formatCurrency")).toBe(true);

      // Verify embeddings were generated
      expect(chunks.every((c) => c.embeddingId)).toBe(true);
    });

    it("should detect file changes and update chunks", async () => {
      // Create initial file
      const testFile = path.join(testDir, "module.ts");
      const initialCode = `
export function oldFunction(): void {
  console.log("old");
}
      `.trim();

      await fs.writeFile(testFile, initialCode);

      // Process initial file
      await chunkingService.processFile(testFile, initialCode);

      const initialChunks = await chunkStorage.getChunksByFile(testFile);
      expect(initialChunks.length).toBe(1);
      expect(initialChunks[0].name).toBe("oldFunction");

      // Register handler for file changes
      watcher.on(FileEventType.CHANGE, async (event: ChangeEvent) => {
        const code = await fs.readFile(event.filePath, "utf-8");
        await chunkingService.processFile(event.filePath, code);
      });

      // Start watching
      await watcher.start(testDir);

      // Modify the file
      const updatedCode = `
export function newFunction(): void {
  console.log("new");
}
      `.trim();

      await fs.writeFile(testFile, updatedCode);

      // Wait for change to be detected and processed
      await new Promise((resolve) => setTimeout(resolve, 1000));

      // Verify chunks were updated
      const updatedChunks = await chunkStorage.getChunksByFile(testFile);
      expect(updatedChunks.length).toBe(1);
      expect(updatedChunks[0].name).toBe("newFunction");
      expect(updatedChunks[0].code).toContain("new");
    });

    it("should detect file deletion and remove chunks", async () => {
      // Create and process initial file
      const testFile = path.join(testDir, "to-delete.ts");
      const code = `export function temp(): void {}`;

      await fs.writeFile(testFile, code);
      await chunkingService.processFile(testFile, code);

      // Verify chunks exist
      const initialChunks = await chunkStorage.getChunksByFile(testFile);
      expect(initialChunks.length).toBe(1);

      // Register handler for file deletion
      watcher.on(FileEventType.UNLINK, async (event: ChangeEvent) => {
        await chunkingService.deleteChunksForFile(event.filePath);
      });

      // Start watching
      await watcher.start(testDir);

      // Delete the file
      await fs.unlink(testFile);

      // Wait for deletion to be detected and processed
      await new Promise((resolve) => setTimeout(resolve, 1000));

      // Verify chunks were deleted
      const remainingChunks = await chunkStorage.getChunksByFile(testFile);
      expect(remainingChunks.length).toBe(0);
    });

    it("should handle rapid file changes with debouncing", async () => {
      const processedVersions: string[] = [];

      // Register handler
      watcher.on(FileEventType.CHANGE, async (event: ChangeEvent) => {
        // Only process .ts files (ignore .db and other files)
        if (!event.filePath.endsWith(".ts")) {
          return;
        }

        const code = await fs.readFile(event.filePath, "utf-8");
        await chunkingService.processFile(event.filePath, code);

        // Track which version was processed
        const chunks = await chunkStorage.getChunksByFile(event.filePath);
        if (chunks.length > 0) {
          processedVersions.push(chunks[0].name);
        }
      });

      // Start watching with 400ms debounce
      await watcher.start(testDir, { debounceMs: 400 });

      // Create initial file with a function (so it creates chunks)
      const testFile = path.join(testDir, "rapid.ts");
      const initialCode = `export function version1(): void { console.log("v1"); }`;
      await fs.writeFile(testFile, initialCode);
      await chunkingService.processFile(testFile, initialCode);

      // Wait for initial add to settle
      await new Promise((resolve) => setTimeout(resolve, 600));

      processedVersions.length = 0; // Reset tracking

      // Rapid successive changes
      await fs.writeFile(
        testFile,
        `export function version2(): void { console.log("v2"); }`,
      );
      await new Promise((resolve) => setTimeout(resolve, 50));
      await fs.writeFile(
        testFile,
        `export function version3(): void { console.log("v3"); }`,
      );
      await new Promise((resolve) => setTimeout(resolve, 50));
      await fs.writeFile(
        testFile,
        `export function version4(): void { console.log("v4"); }`,
      );

      // Wait for all processing to complete
      await new Promise((resolve) => setTimeout(resolve, 1000));

      // Verify final state has the last change (debouncing ensures we get final stable version)
      const chunks = await chunkStorage.getChunksByFile(testFile);
      expect(chunks.length).toBe(1);
      expect(chunks[0].name).toBe("version4");

      // The last processed version should be version4
      expect(processedVersions[processedVersions.length - 1]).toBe("version4");
    });

    it("should ignore files in excluded directories", async () => {
      let eventsDetected = 0;

      watcher.on("all", async () => {
        eventsDetected++;
      });

      // Start watching with default excludes
      await watcher.start(testDir);

      // Create node_modules directory and file
      const nodeModulesDir = path.join(testDir, "node_modules");
      await fs.mkdir(nodeModulesDir);

      await new Promise((resolve) => setTimeout(resolve, 600));
      eventsDetected = 0; // Reset after directory event

      await fs.writeFile(path.join(nodeModulesDir, "package.json"), "{}");

      // Wait for events
      await new Promise((resolve) => setTimeout(resolve, 600));

      // Should not detect files in node_modules
      expect(eventsDetected).toBe(0);

      // Reset counter
      eventsDetected = 0;

      // Create file in watched directory (should be detected)
      await fs.writeFile(path.join(testDir, "app.ts"), "code");

      await new Promise((resolve) => setTimeout(resolve, 600));

      // Should detect file in root
      expect(eventsDetected).toBe(1);
    });

    it("should update embeddings when chunk content changes", async () => {
      const testFile = path.join(testDir, "embed-test.ts");
      const initialCode = `export function v1(): void { console.log("v1"); }`;

      // Create and process initial file
      await fs.writeFile(testFile, initialCode);
      await chunkingService.processFile(testFile, initialCode);

      const initialChunks = await chunkStorage.getChunksByFile(testFile);
      const initialEmbeddingId = initialChunks[0].embeddingId;
      expect(initialEmbeddingId).toBeDefined();

      // Register change handler
      watcher.on(FileEventType.CHANGE, async (event: ChangeEvent) => {
        const code = await fs.readFile(event.filePath, "utf-8");
        await chunkingService.processFile(event.filePath, code);
      });

      await watcher.start(testDir);

      // Modify file
      const updatedCode = `export function v2(): void { console.log("v2"); }`;
      await fs.writeFile(testFile, updatedCode);

      // Wait for processing
      await new Promise((resolve) => setTimeout(resolve, 1000));

      // Verify embedding was updated
      const updatedChunks = await chunkStorage.getChunksByFile(testFile);
      expect(updatedChunks.length).toBe(1);
      expect(updatedChunks[0].embeddingId).toBeDefined();
      expect(updatedChunks[0].embeddingId).not.toBe(initialEmbeddingId);
    });

    it("should handle multiple files being modified concurrently", async () => {
      const processedFiles = new Set<string>();

      watcher.on(FileEventType.CHANGE, async (event: ChangeEvent) => {
        // Only process TypeScript/JavaScript files
        if (!event.filePath.match(/\.(ts|tsx|js|jsx)$/)) {
          return;
        }
        const code = await fs.readFile(event.filePath, "utf-8");
        await chunkingService.processFile(event.filePath, code);
        processedFiles.add(event.filePath);
      });

      await watcher.start(testDir);

      // Create multiple files
      const file1 = path.join(testDir, "file1.ts");
      const file2 = path.join(testDir, "file2.ts");
      const file3 = path.join(testDir, "file3.ts");

      await fs.writeFile(file1, "export const a = 1;");
      await fs.writeFile(file2, "export const b = 2;");
      await fs.writeFile(file3, "export const c = 3;");

      await chunkingService.processFile(file1, "export const a = 1;");
      await chunkingService.processFile(file2, "export const b = 2;");
      await chunkingService.processFile(file3, "export const c = 3;");

      // Wait for initial processing
      await new Promise((resolve) => setTimeout(resolve, 1000));

      processedFiles.clear();

      // Modify all files concurrently
      await Promise.all([
        fs.writeFile(file1, "export const a = 10;"),
        fs.writeFile(file2, "export const b = 20;"),
        fs.writeFile(file3, "export const c = 30;"),
      ]);

      // Wait for all changes to be processed
      await new Promise((resolve) => setTimeout(resolve, 1500));

      // All files should have been processed
      expect(processedFiles.size).toBe(3);
      expect(processedFiles.has(file1)).toBe(true);
      expect(processedFiles.has(file2)).toBe(true);
      expect(processedFiles.has(file3)).toBe(true);
    });

    it("should maintain correct event order during rapid changes", async () => {
      const events: string[] = [];

      watcher.on("all", async (event: ChangeEvent) => {
        events.push(`${event.eventType}:${path.basename(event.filePath)}`);
      });

      await watcher.start(testDir);

      const testFile = path.join(testDir, "order-test.ts");

      // Sequence of operations
      await fs.writeFile(testFile, "v1");
      await new Promise((resolve) => setTimeout(resolve, 600));

      await fs.writeFile(testFile, "v2");
      await new Promise((resolve) => setTimeout(resolve, 600));

      await fs.unlink(testFile);
      await new Promise((resolve) => setTimeout(resolve, 600));

      // Verify event order
      expect(events).toEqual([
        "add:order-test.ts",
        "change:order-test.ts",
        "unlink:order-test.ts",
      ]);
    });
  });

  describe("Error handling and resilience", () => {
    it("should continue watching after processing errors", async () => {
      let errorCount = 0;
      let successCount = 0;

      watcher.on(FileEventType.ADD, async (event: ChangeEvent) => {
        try {
          const code = await fs.readFile(event.filePath, "utf-8");

          // Simulate error on first file
          if (event.filePath.includes("error")) {
            throw new Error("Processing error");
          }

          await chunkingService.processFile(event.filePath, code);
          successCount++;
        } catch {
          errorCount++;
        }
      });

      await watcher.start(testDir);

      // Create file that will error
      await fs.writeFile(path.join(testDir, "error-file.ts"), "code");
      await new Promise((resolve) => setTimeout(resolve, 600));

      // Create file that will succeed
      await fs.writeFile(path.join(testDir, "success-file.ts"), "code");
      await new Promise((resolve) => setTimeout(resolve, 600));

      expect(errorCount).toBe(1);
      expect(successCount).toBe(1);
      expect(watcher.isWatching()).toBe(true);
    });
  });
});
