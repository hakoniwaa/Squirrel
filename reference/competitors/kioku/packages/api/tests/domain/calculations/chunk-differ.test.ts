/**
 * Unit Tests: chunk-differ.ts
 *
 * Tests for detecting chunk changes (added, modified, deleted).
 * Used for incremental re-embedding when files change.
 *
 * Coverage target: 90%+
 */

import { describe, it, expect } from "vitest";
import {
  detectChunkChanges,
  type ChunkChange as _ChunkChange,
} from "../../../src/domain/calculations/chunk-differ";
import { ChunkType, type CodeChunk } from "../../../src/domain/models/CodeChunk";
import { v4 as uuidv4 } from "uuid";

describe("detectChunkChanges", () => {
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

  describe("added chunks", () => {
    it("should detect newly added chunks", () => {
      const oldChunks: CodeChunk[] = [];
      const newChunks: CodeChunk[] = [
        createChunk({ name: "newFunction1" }),
        createChunk({ name: "newFunction2" }),
      ];

      const changes = detectChunkChanges(oldChunks, newChunks);

      const addedChanges = changes.filter((c) => c.type === "added");
      expect(addedChanges).toHaveLength(2);
      expect(addedChanges[0]?.newChunk?.name).toBe("newFunction1");
      expect(addedChanges[1]?.newChunk?.name).toBe("newFunction2");
    });

    it("should mark added chunks as needing re-embedding", () => {
      const oldChunks: CodeChunk[] = [];
      const newChunks: CodeChunk[] = [createChunk({ name: "newFunction" })];

      const changes = detectChunkChanges(oldChunks, newChunks);

      expect(changes[0]?.needsReembedding).toBe(true);
    });
  });

  describe("modified chunks", () => {
    it("should detect modified chunks by content hash", () => {
      const chunk1 = createChunk({ name: "func1", contentHash: "hash1" });
      const chunk2 = createChunk({ name: "func1", contentHash: "hash2" }); // Same name, different hash

      const oldChunks = [chunk1];
      const newChunks = [chunk2];

      const changes = detectChunkChanges(oldChunks, newChunks);

      expect(changes).toHaveLength(1);
      expect(changes[0]?.type).toBe("modified");
      expect(changes[0]?.oldChunk?.name).toBe("func1");
      expect(changes[0]?.newChunk?.name).toBe("func1");
    });

    it("should mark modified chunks as needing re-embedding", () => {
      const oldChunk = createChunk({ name: "func", contentHash: "oldHash" });
      const newChunk = createChunk({ name: "func", contentHash: "newHash" });

      const changes = detectChunkChanges([oldChunk], [newChunk]);

      expect(changes[0]?.needsReembedding).toBe(true);
    });

    it("should detect content changes even with same line numbers", () => {
      const oldChunk = createChunk({
        name: "calculate",
        code: "function calculate() { return 1; }",
        contentHash: "hash1",
      });
      const newChunk = createChunk({
        name: "calculate",
        code: "function calculate() { return 2; }",
        contentHash: "hash2",
      });

      const changes = detectChunkChanges([oldChunk], [newChunk]);

      expect(changes).toHaveLength(1);
      expect(changes[0]?.type).toBe("modified");
    });
  });

  describe("deleted chunks", () => {
    it("should detect deleted chunks", () => {
      const oldChunks: CodeChunk[] = [
        createChunk({ name: "deletedFunction1" }),
        createChunk({ name: "deletedFunction2" }),
      ];
      const newChunks: CodeChunk[] = [];

      const changes = detectChunkChanges(oldChunks, newChunks);

      const deletedChanges = changes.filter((c) => c.type === "deleted");
      expect(deletedChanges).toHaveLength(2);
      expect(deletedChanges[0]?.oldChunk?.name).toBe("deletedFunction1");
      expect(deletedChanges[1]?.oldChunk?.name).toBe("deletedFunction2");
    });

    it("should NOT mark deleted chunks as needing re-embedding", () => {
      const oldChunks = [createChunk({ name: "deleted" })];
      const newChunks: CodeChunk[] = [];

      const changes = detectChunkChanges(oldChunks, newChunks);

      expect(changes[0]?.needsReembedding).toBe(false);
    });
  });

  describe("unchanged chunks", () => {
    it("should detect unchanged chunks (same content hash)", () => {
      const chunk = createChunk({ name: "unchanged", contentHash: "sameHash" });
      const oldChunks = [chunk];
      const newChunks = [
        createChunk({ name: "unchanged", contentHash: "sameHash" }),
      ];

      const changes = detectChunkChanges(oldChunks, newChunks);

      const unchangedChanges = changes.filter((c) => c.type === "unchanged");
      expect(unchangedChanges).toHaveLength(1);
      expect(unchangedChanges[0]?.oldChunk?.name).toBe("unchanged");
      expect(unchangedChanges[0]?.newChunk?.name).toBe("unchanged");
    });

    it("should NOT mark unchanged chunks as needing re-embedding", () => {
      const oldChunk = createChunk({ name: "same", contentHash: "hash" });
      const newChunk = createChunk({ name: "same", contentHash: "hash" });

      const changes = detectChunkChanges([oldChunk], [newChunk]);

      expect(changes[0]?.needsReembedding).toBe(false);
    });
  });

  describe("mixed changes", () => {
    it("should detect all types of changes in one diff", () => {
      const oldChunks = [
        createChunk({ name: "unchanged", contentHash: "hash1" }),
        createChunk({ name: "modified", contentHash: "oldHash" }),
        createChunk({ name: "deleted", contentHash: "hash3" }),
      ];

      const newChunks = [
        createChunk({ name: "unchanged", contentHash: "hash1" }),
        createChunk({ name: "modified", contentHash: "newHash" }),
        createChunk({ name: "added", contentHash: "hash4" }),
      ];

      const changes = detectChunkChanges(oldChunks, newChunks);

      expect(changes).toHaveLength(4);
      expect(changes.filter((c) => c.type === "unchanged")).toHaveLength(1);
      expect(changes.filter((c) => c.type === "modified")).toHaveLength(1);
      expect(changes.filter((c) => c.type === "deleted")).toHaveLength(1);
      expect(changes.filter((c) => c.type === "added")).toHaveLength(1);
    });

    it("should correctly count chunks needing re-embedding", () => {
      const oldChunks = [
        createChunk({ name: "unchanged", contentHash: "hash1" }),
        createChunk({ name: "modified", contentHash: "oldHash" }),
        createChunk({ name: "deleted", contentHash: "hash3" }),
      ];

      const newChunks = [
        createChunk({ name: "unchanged", contentHash: "hash1" }),
        createChunk({ name: "modified", contentHash: "newHash" }),
        createChunk({ name: "added", contentHash: "hash4" }),
      ];

      const changes = detectChunkChanges(oldChunks, newChunks);

      const needsReembedding = changes.filter((c) => c.needsReembedding);
      expect(needsReembedding).toHaveLength(2); // modified + added
    });
  });

  describe("chunk matching strategy", () => {
    it("should match chunks by name and scope path", () => {
      const oldChunk = createChunk({
        name: "helper",
        scopePath: ["MyClass", "method1", "helper"],
        contentHash: "hash1",
      });

      const newChunk = createChunk({
        name: "helper",
        scopePath: ["MyClass", "method1", "helper"],
        contentHash: "hash2",
      });

      const changes = detectChunkChanges([oldChunk], [newChunk]);

      expect(changes[0]?.type).toBe("modified");
      expect(changes[0]?.oldChunk?.name).toBe("helper");
    });

    it("should treat chunks with different scope paths as different", () => {
      const oldChunk = createChunk({
        name: "helper",
        scopePath: ["ClassA", "helper"],
      });

      const newChunk = createChunk({
        name: "helper",
        scopePath: ["ClassB", "helper"],
      });

      const changes = detectChunkChanges([oldChunk], [newChunk]);

      // Should detect as deleted + added, not modified
      expect(changes.filter((c) => c.type === "deleted")).toHaveLength(1);
      expect(changes.filter((c) => c.type === "added")).toHaveLength(1);
    });

    it("should match renamed functions as deleted + added", () => {
      const oldChunk = createChunk({ name: "oldName", contentHash: "hash" });
      const newChunk = createChunk({ name: "newName", contentHash: "hash" });

      const changes = detectChunkChanges([oldChunk], [newChunk]);

      // Even with same hash, different names = deleted + added
      expect(changes).toHaveLength(2);
      expect(changes.filter((c) => c.type === "deleted")).toHaveLength(1);
      expect(changes.filter((c) => c.type === "added")).toHaveLength(1);
    });
  });

  describe("edge cases", () => {
    it("should handle empty old chunks (all added)", () => {
      const oldChunks: CodeChunk[] = [];
      const newChunks = [
        createChunk({ name: "func1" }),
        createChunk({ name: "func2" }),
      ];

      const changes = detectChunkChanges(oldChunks, newChunks);

      expect(changes.filter((c) => c.type === "added")).toHaveLength(2);
    });

    it("should handle empty new chunks (all deleted)", () => {
      const oldChunks = [
        createChunk({ name: "func1" }),
        createChunk({ name: "func2" }),
      ];
      const newChunks: CodeChunk[] = [];

      const changes = detectChunkChanges(oldChunks, newChunks);

      expect(changes.filter((c) => c.type === "deleted")).toHaveLength(2);
    });

    it("should handle both arrays empty", () => {
      const changes = detectChunkChanges([], []);

      expect(changes).toHaveLength(0);
    });

    it("should handle chunks with same name but different types", () => {
      const oldChunk = createChunk({
        name: "User",
        type: ChunkType.INTERFACE,
      });

      const newChunk = createChunk({
        name: "User",
        type: ChunkType.CLASS_DECLARATION,
      });

      const changes = detectChunkChanges([oldChunk], [newChunk]);

      // Different types = deleted + added
      expect(changes).toHaveLength(2);
      expect(changes.filter((c) => c.type === "deleted")).toHaveLength(1);
      expect(changes.filter((c) => c.type === "added")).toHaveLength(1);
    });

    it("should handle duplicate chunk names in same file", () => {
      const oldChunks = [
        createChunk({ name: "helper", scopePath: ["ClassA", "helper"] }),
        createChunk({ name: "helper", scopePath: ["ClassB", "helper"] }),
      ];

      const newChunks = [
        createChunk({
          name: "helper",
          scopePath: ["ClassA", "helper"],
          contentHash: "newHash",
        }),
        createChunk({ name: "helper", scopePath: ["ClassB", "helper"] }),
      ];

      const changes = detectChunkChanges(oldChunks, newChunks);

      // Should detect 1 modified (ClassA) and 1 unchanged (ClassB)
      expect(changes.filter((c) => c.type === "modified")).toHaveLength(1);
      expect(changes.filter((c) => c.type === "unchanged")).toHaveLength(1);
    });
  });

  describe("performance", () => {
    it("should handle large chunk arrays efficiently", () => {
      const oldChunks = Array(1000)
        .fill(null)
        .map((_, i) =>
          createChunk({ name: `func${i}`, contentHash: `hash${i}` }),
        );

      const newChunks = Array(1000)
        .fill(null)
        .map((_, i) =>
          createChunk({ name: `func${i}`, contentHash: `hash${i}` }),
        );

      const startTime = Date.now();
      const changes = detectChunkChanges(oldChunks, newChunks);
      const duration = Date.now() - startTime;

      expect(changes).toHaveLength(1000);
      expect(duration).toBeLessThan(100); // Should complete in <100ms
    });
  });

  describe("change metadata", () => {
    it("should include old and new chunks in modified changes", () => {
      const oldChunk = createChunk({ name: "func", contentHash: "old" });
      const newChunk = createChunk({ name: "func", contentHash: "new" });

      const changes = detectChunkChanges([oldChunk], [newChunk]);

      expect(changes[0]?.oldChunk).toBeDefined();
      expect(changes[0]?.newChunk).toBeDefined();
      expect(changes[0]?.oldChunk?.contentHash).toBe("old");
      expect(changes[0]?.newChunk?.contentHash).toBe("new");
    });

    it("should include only new chunk in added changes", () => {
      const newChunk = createChunk({ name: "added" });

      const changes = detectChunkChanges([], [newChunk]);

      expect(changes[0]?.oldChunk).toBeUndefined();
      expect(changes[0]?.newChunk).toBeDefined();
    });

    it("should include only old chunk in deleted changes", () => {
      const oldChunk = createChunk({ name: "deleted" });

      const changes = detectChunkChanges([oldChunk], []);

      expect(changes[0]?.oldChunk).toBeDefined();
      expect(changes[0]?.newChunk).toBeUndefined();
    });
  });
});
