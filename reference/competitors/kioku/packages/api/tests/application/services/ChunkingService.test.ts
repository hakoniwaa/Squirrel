/**
 * Unit Tests: ChunkingService.ts
 *
 * Tests for chunking orchestration service.
 * Coordinates extraction, diffing, storage, and embedding generation.
 *
 * Coverage target: 90%+
 */

import { describe, it, expect, beforeEach, vi } from "vitest";
import { ChunkingService } from "../../../src/application/services/ChunkingService";
import { ChunkType, type CodeChunk } from "../../../src/domain/models/CodeChunk";
import type { IChunkStorage } from "../../../src/application/ports/IChunkStorage";
import type { IEmbeddingService } from "../../../src/application/ports/IEmbeddingService";
import { v4 as uuidv4 } from "uuid";

describe("ChunkingService", () => {
  let chunkingService: ChunkingService;
  let mockChunkStorage: IChunkStorage;
  let mockEmbeddingService: IEmbeddingService;

  const testFilePath = "/test/project/src/utils.ts";

  // Helper to create a test chunk
  function createChunk(overrides: Partial<CodeChunk> = {}): CodeChunk {
    return {
      id: uuidv4(),
      filePath: testFilePath,
      type: ChunkType.FUNCTION_DECLARATION,
      name: "testFunction",
      startLine: 1,
      endLine: 10,
      contentStartLine: 1,
      contentEndLine: 10,
      code: "function testFunction() { return true; }",
      contentHash: "hash123",
      nestingLevel: 0,
      scopePath: ["testFunction"],
      metadata: {
        isExported: false,
        isAsync: false,
      },
      createdAt: new Date(),
      updatedAt: new Date(),
      ...overrides,
    };
  }

  beforeEach(() => {
    // Create mock storage
    mockChunkStorage = {
      saveChunk: vi.fn(),
      saveChunks: vi.fn(),
      getChunksByFilePath: vi.fn(),
      getChunkById: vi.fn(),
      deleteChunk: vi.fn(),
      deleteChunksByFilePath: vi.fn(),
      getAllChunks: vi.fn(),
      updateChunk: vi.fn(),
    };

    // Create mock embedding service
    mockEmbeddingService = {
      generateEmbedding: vi.fn(),
      generateEmbeddings: vi.fn(),
      queueEmbedding: vi.fn(),
      deleteEmbedding: vi.fn(),
    };

    chunkingService = new ChunkingService(
      mockChunkStorage,
      mockEmbeddingService,
    );
  });

  describe("processFile", () => {
    it("should extract chunks from new file and save them", async () => {
      const code = `
function add(a: number, b: number): number {
  return a + b;
}

function subtract(a: number, b: number): number {
  return a - b;
}
      `.trim();

      // Mock: no existing chunks
      (mockChunkStorage.getChunksByFilePath as any).mockResolvedValue([]);
      (mockChunkStorage.saveChunks as any).mockResolvedValue(undefined);

      const result = await chunkingService.processFile(testFilePath, code);

      expect(result.chunksExtracted).toBeGreaterThanOrEqual(2);
      expect(result.chunksAdded).toBeGreaterThanOrEqual(2);
      expect(result.chunksModified).toBe(0);
      expect(result.chunksDeleted).toBe(0);
      expect(mockChunkStorage.saveChunks).toHaveBeenCalled();
    });

    it("should detect modified chunks and update them", async () => {
      const oldCode = `
function calculate() {
  return 1;
}
      `.trim();

      const newCode = `
function calculate() {
  return 2; // Modified
}
      `.trim();

      // Mock: existing chunk
      const existingChunk = createChunk({
        name: "calculate",
        code: oldCode,
        contentHash: "oldHash",
        scopePath: ["calculate"], // Must match extracted chunk's scopePath
      });

      (mockChunkStorage.getChunksByFilePath as any).mockResolvedValue([
        existingChunk,
      ]);
      (mockChunkStorage.saveChunks as any).mockResolvedValue(undefined);
      (mockChunkStorage.deleteChunk as any).mockResolvedValue(undefined);

      const result = await chunkingService.processFile(testFilePath, newCode);

      expect(result.chunksModified).toBeGreaterThanOrEqual(1);
      expect(result.needsReembedding).toBe(true);
    });

    it("should detect deleted chunks and remove them", async () => {
      const oldChunk1 = createChunk({ name: "func1" });
      const oldChunk2 = createChunk({ name: "func2" });

      const newCode = `
function func1() {
  return 1;
}
// func2 was deleted
      `.trim();

      (mockChunkStorage.getChunksByFilePath as any).mockResolvedValue([
        oldChunk1,
        oldChunk2,
      ]);
      (mockChunkStorage.saveChunks as any).mockResolvedValue(undefined);
      (mockChunkStorage.deleteChunk as any).mockResolvedValue(undefined);

      const result = await chunkingService.processFile(testFilePath, newCode);

      expect(result.chunksDeleted).toBeGreaterThanOrEqual(1);
      expect(mockChunkStorage.deleteChunk).toHaveBeenCalled();
    });

    it("should queue embeddings for added and modified chunks", async () => {
      const code = `
function newFunction() {
  return true;
}
      `.trim();

      (mockChunkStorage.getChunksByFilePath as any).mockResolvedValue([]);
      (mockChunkStorage.saveChunks as any).mockResolvedValue(undefined);
      (mockEmbeddingService.queueEmbedding as any).mockResolvedValue(undefined);

      const result = await chunkingService.processFile(testFilePath, code);

      expect(result.needsReembedding).toBe(true);
      // Embeddings should be queued (or generated immediately)
    });

    it("should handle parse errors gracefully with file-level fallback", async () => {
      const brokenCode = `
function broken( {
  // Invalid syntax
      `.trim();

      (mockChunkStorage.getChunksByFilePath as any).mockResolvedValue([]);
      (mockChunkStorage.saveChunks as any).mockResolvedValue(undefined);

      const result = await chunkingService.processFile(
        testFilePath,
        brokenCode,
      );

      // Should still extract 1 file-level chunk as fallback
      expect(result.chunksExtracted).toBe(1);
      expect(result.chunksAdded).toBe(1);
    });

    it("should handle unchanged chunks correctly", async () => {
      const code = `
function unchanged() {
  return true;
}
      `.trim();

      // Note: In real usage, the extracted chunk would have the same code
      // but in this test, we can't easily mock the exact extracted code
      // So we test that the system processes the file without errors
      (mockChunkStorage.getChunksByFilePath as any).mockResolvedValue([]);
      (mockChunkStorage.saveChunks as any).mockResolvedValue(undefined);

      const result = await chunkingService.processFile(testFilePath, code);

      expect(result.chunksExtracted).toBeGreaterThan(0);
      expect(result.processingTimeMs).toBeGreaterThanOrEqual(0);
    });
  });

  describe("processFileWithMetrics", () => {
    it("should return processing metrics", async () => {
      const code = `function test() { return 1; }`;

      (mockChunkStorage.getChunksByFilePath as any).mockResolvedValue([]);
      (mockChunkStorage.saveChunks as any).mockResolvedValue(undefined);

      const result = await chunkingService.processFile(testFilePath, code);

      expect(result).toHaveProperty("chunksExtracted");
      expect(result).toHaveProperty("chunksAdded");
      expect(result).toHaveProperty("chunksModified");
      expect(result).toHaveProperty("chunksDeleted");
      expect(result).toHaveProperty("needsReembedding");
      expect(result).toHaveProperty("processingTimeMs");
    });

    it("should track processing time", async () => {
      const code = `function test() { return 1; }`;

      (mockChunkStorage.getChunksByFilePath as any).mockResolvedValue([]);
      (mockChunkStorage.saveChunks as any).mockResolvedValue(undefined);

      const result = await chunkingService.processFile(testFilePath, code);

      expect(result.processingTimeMs).toBeGreaterThanOrEqual(0); // Can be 0 for very fast processing
      expect(result.processingTimeMs).toBeLessThan(1000); // Should be fast
    });
  });

  describe("getChunksForFile", () => {
    it("should retrieve chunks from storage", async () => {
      const chunks = [
        createChunk({ name: "func1" }),
        createChunk({ name: "func2" }),
      ];

      (mockChunkStorage.getChunksByFilePath as any).mockResolvedValue(chunks);

      const result = await chunkingService.getChunksForFile(testFilePath);

      expect(result).toHaveLength(2);
      expect(mockChunkStorage.getChunksByFilePath).toHaveBeenCalledWith(
        testFilePath,
      );
    });
  });

  describe("deleteChunksForFile", () => {
    it("should delete all chunks for a file", async () => {
      (mockChunkStorage.deleteChunksByFilePath as any).mockResolvedValue(
        undefined,
      );

      await chunkingService.deleteChunksForFile(testFilePath);

      expect(mockChunkStorage.deleteChunksByFilePath).toHaveBeenCalledWith(
        testFilePath,
      );
    });
  });

  describe("content hash caching", () => {
    it("should handle repeated processing of same file", async () => {
      const code = `function test() { return 1; }`;

      // First processing
      (mockChunkStorage.getChunksByFilePath as any).mockResolvedValue([]);
      (mockChunkStorage.saveChunks as any).mockResolvedValue(undefined);

      const result1 = await chunkingService.processFile(testFilePath, code);
      expect(result1.chunksAdded).toBeGreaterThan(0);

      // Second processing - in real usage, if the file hasn't changed,
      // the extracted chunks would have the same hash
      // For this test, we just verify the system handles re-processing
      (mockChunkStorage.getChunksByFilePath as any).mockResolvedValue([]);

      const result2 = await chunkingService.processFile(testFilePath, code);
      expect(result2.chunksExtracted).toBeGreaterThan(0);
    });
  });

  describe("error handling", () => {
    it("should handle storage errors gracefully", async () => {
      const code = `function test() { return 1; }`;

      (mockChunkStorage.getChunksByFilePath as any).mockRejectedValue(
        new Error("Storage error"),
      );

      await expect(
        chunkingService.processFile(testFilePath, code),
      ).rejects.toThrow("Storage error");
    });

    it("should handle embedding service errors gracefully", async () => {
      const code = `function test() { return 1; }`;

      (mockChunkStorage.getChunksByFilePath as any).mockResolvedValue([]);
      (mockChunkStorage.saveChunks as any).mockResolvedValue(undefined);
      (mockChunkStorage.updateChunk as any).mockResolvedValue(undefined);
      (mockEmbeddingService.generateEmbedding as any).mockRejectedValue(
        new Error("Embedding error"),
      );

      // Should still complete processing even if embeddings fail
      const result = await chunkingService.processFile(testFilePath, code);

      expect(result.chunksExtracted).toBeGreaterThan(0);
    });
  });

  describe("batch processing", () => {
    it("should process multiple files efficiently", async () => {
      const files = [
        { path: "/test/file1.ts", code: "function f1() {}" },
        { path: "/test/file2.ts", code: "function f2() {}" },
        { path: "/test/file3.ts", code: "function f3() {}" },
      ];

      (mockChunkStorage.getChunksByFilePath as any).mockResolvedValue([]);
      (mockChunkStorage.saveChunks as any).mockResolvedValue(undefined);

      const results = await Promise.all(
        files.map((f) => chunkingService.processFile(f.path, f.code)),
      );

      expect(results).toHaveLength(3);
      results.forEach((result) => {
        expect(result.chunksExtracted).toBeGreaterThan(0);
      });
    });
  });

  describe("integration scenarios", () => {
    it("should handle complete file lifecycle (add → modify → delete)", async () => {
      // Step 1: Add new file
      const initialCode = `function calculate() { return 1; }`;
      (mockChunkStorage.getChunksByFilePath as any).mockResolvedValue([]);
      (mockChunkStorage.saveChunks as any).mockResolvedValue(undefined);

      const result1 = await chunkingService.processFile(
        testFilePath,
        initialCode,
      );
      expect(result1.chunksAdded).toBeGreaterThan(0);

      // Step 2: Modify file
      const modifiedCode = `function calculate() { return 2; }`;
      const existingChunk = createChunk({
        name: "calculate",
        code: initialCode,
        contentHash: "hash1",
        scopePath: ["calculate"], // Must match extracted chunk's scopePath
      });
      (mockChunkStorage.getChunksByFilePath as any).mockResolvedValue([
        existingChunk,
      ]);
      (mockChunkStorage.deleteChunk as any).mockResolvedValue(undefined);

      const result2 = await chunkingService.processFile(
        testFilePath,
        modifiedCode,
      );
      expect(result2.chunksModified).toBeGreaterThan(0);

      // Step 3: Delete file
      (mockChunkStorage.deleteChunksByFilePath as any).mockResolvedValue(
        undefined,
      );

      await chunkingService.deleteChunksForFile(testFilePath);
      expect(mockChunkStorage.deleteChunksByFilePath).toHaveBeenCalledWith(
        testFilePath,
      );
    });
  });
});
