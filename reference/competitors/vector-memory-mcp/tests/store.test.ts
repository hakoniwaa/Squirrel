import { describe, expect, test, beforeEach, afterEach } from "bun:test";
import { mkdtempSync, rmSync } from "fs";
import { join } from "path";
import { tmpdir } from "os";
import * as lancedb from "@lancedb/lancedb";
import { connectToDatabase } from "../src/db/connection";
import { MemoryRepository } from "../src/db/memory.repository";
import { EmbeddingsService } from "../src/services/embeddings.service";
import { MemoryService } from "../src/services/memory.service";
import { DELETED_TOMBSTONE } from "../src/types/memory";
import { TABLE_NAME } from "../src/db/schema";

describe("MemoryService", () => {
  let db: lancedb.Connection;
  let repository: MemoryRepository;
  let embeddings: EmbeddingsService;
  let service: MemoryService;
  let tmpDir: string;
  let dbPath: string;

  beforeEach(async () => {
    tmpDir = mkdtempSync(join(tmpdir(), "vector-memory-mcp-test-"));
    dbPath = join(tmpDir, "test.lancedb");
    db = await connectToDatabase(dbPath);
    repository = new MemoryRepository(db);
    embeddings = new EmbeddingsService("Xenova/all-MiniLM-L6-v2", 384);
    service = new MemoryService(repository, embeddings);
  });

  afterEach(() => {
    rmSync(tmpDir, { recursive: true });
  });

  describe("createDatabase", () => {
    test("creates database directory", async () => {
      // connectToDatabase was called in beforeEach
      const file = Bun.file(dbPath);
      // LanceDB creates a directory
      expect(await file.exists()).toBe(false); // It's a directory, not a file, wait Bun.file checks files?
      // Check directory existence using fs
      const { existsSync, statSync } = await import("fs");
      expect(existsSync(dbPath)).toBe(true);
      expect(statSync(dbPath).isDirectory()).toBe(true);
    });
  });

  describe("store", () => {
    test("creates memory with generated UUID", async () => {
      const memory = await service.store("test content");
      expect(memory.id).toMatch(
        /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/
      );
    });

    test("stores content correctly", async () => {
      const memory = await service.store("test content");
      expect(memory.content).toBe("test content");
    });

    test("stores metadata correctly", async () => {
      const metadata = { key: "value", nested: { a: 1 } };
      const memory = await service.store("test", metadata);
      expect(memory.metadata).toEqual(metadata);
    });

    test("defaults to empty metadata", async () => {
      const memory = await service.store("test");
      expect(memory.metadata).toEqual({});
    });

    test("generates embedding", async () => {
      const memory = await service.store("test content");
      expect(memory.embedding).toBeArray();
      expect(memory.embedding.length).toBe(384);
    });

    test("sets timestamps", async () => {
      const before = new Date();
      const memory = await service.store("test");
      const after = new Date();

      // Allow slight timing differences (1s)
      expect(memory.createdAt.getTime()).toBeGreaterThanOrEqual(before.getTime() - 1000);
      expect(memory.createdAt.getTime()).toBeLessThanOrEqual(after.getTime() + 1000);
    });

    test("sets supersededBy to null", async () => {
      const memory = await service.store("test");
      expect(memory.supersededBy).toBeNull();
    });
  });

  describe("get", () => {
    test("retrieves stored memory", async () => {
      const stored = await service.store("test content", { key: "value" });
      const retrieved = await service.get(stored.id);

      expect(retrieved).not.toBeNull();
      expect(retrieved!.id).toBe(stored.id);
      expect(retrieved!.content).toBe("test content");
      expect(retrieved!.metadata).toEqual({ key: "value" });
    });

    test("retrieves embedding", async () => {
      const stored = await service.store("test content");
      const retrieved = await service.get(stored.id);

      expect(retrieved!.embedding).toBeArray();
      expect(retrieved!.embedding.length).toBe(384);
      for (let i = 0; i < 10; i++) {
        expect(retrieved!.embedding[i]).toBeCloseTo(stored.embedding[i], 5);
      }
    });

    test("returns null for non-existent ID", async () => {
      const retrieved = await service.get("non-existent-id");
      expect(retrieved).toBeNull();
    });

    test("retrieves deleted memory (with supersededBy set)", async () => {
      const stored = await service.store("test");
      await service.delete(stored.id);

      const retrieved = await service.get(stored.id);
      expect(retrieved).not.toBeNull();
      expect(retrieved!.supersededBy).toBe(DELETED_TOMBSTONE);
    });
  });

  describe("delete", () => {
    test("soft-deletes memory by setting supersededBy", async () => {
      const stored = await service.store("test");
      const success = await service.delete(stored.id);

      expect(success).toBe(true);
      const retrieved = await service.get(stored.id);
      expect(retrieved!.supersededBy).toBe(DELETED_TOMBSTONE);
    });

    test("returns false for non-existent ID", async () => {
      const success = await service.delete("non-existent-id");
      expect(success).toBe(false);
    });

    test("can delete already deleted memory", async () => {
      const stored = await service.store("test");
      await service.delete(stored.id);
      const success = await service.delete(stored.id);
      expect(success).toBe(true);
    });
  });

  describe("search", () => {
    test("finds semantically similar memories", async () => {
      await service.store("Python is a programming language");
      await service.store("JavaScript runs in web browsers");
      await service.store("Cats are furry animals");

      const results = await service.search("coding and software development");

      expect(results.length).toBeGreaterThan(0);
      const contents = results.map((r) => r.content);
      expect(
        contents.some(c => c.includes("Python") || c.includes("JavaScript"))
      ).toBe(true);
    });

    test("respects limit parameter", async () => {
      await service.store("Memory 1");
      await service.store("Memory 2");
      await service.store("Memory 3");

      const results = await service.search("memory", 2);
      expect(results.length).toBe(2);
    });

    test("defaults to limit of 10", async () => {
      // Increase limit to verify default
      const embeddings = new EmbeddingsService("Xenova/all-MiniLM-L6-v2", 384);
      // Mock embeddings to be fast? No, using real ones for integration test
      
      for (let i = 0; i < 12; i++) {
        await service.store(`Memory ${i}`);
      }

      const results = await service.search("memory");
      expect(results.length).toBe(10);
    });

    test("excludes deleted memories", async () => {
      const mem1 = await service.store("Python programming");
      await service.store("JavaScript programming");

      await service.delete(mem1.id);

      const results = await service.search("programming");
      const contents = results.map(r => r.content);
      expect(contents).toContain("JavaScript programming");
      expect(contents).not.toContain("Python programming");
    });

    test("returns empty array when no matches", async () => {
      const results = await service.search("nonexistent query");
      // Depending on implementation, strict empty array check might fail if everything matches slightly
      // But with few docs, it might return empty if threshold (if any) or just returns 0
      // Actually vector search always returns closest. But we only have 0 docs here?
      // No, previous tests added docs. `beforeEach` resets DB.
      expect(results).toBeArray();
      expect(results.length).toBe(0);
    });

    test("excludes superseded memories but follows chain to head", async () => {
      const mem1 = await service.store("Original content about cats");
      const mem2 = await service.store("Updated content about cats");

      // Manually supersede
      const table = await db.openTable(TABLE_NAME);
      await table.update({ where: `id = '${mem1.id}'`, values: { superseded_by: mem2.id } });

      const results = await service.search("cats");
      expect(results.length).toBe(1);
      expect(results[0].id).toBe(mem2.id);
    });

    test("avoids duplicate results from supersession chains", async () => {
      const mem1 = await service.store("Cats are pets");
      const mem2 = await service.store("Cats are furry pets");
      const mem3 = await service.store("Cats are furry friendly pets");

      const table = await db.openTable(TABLE_NAME);
      await table.update({ where: `id = '${mem1.id}'`, values: { superseded_by: mem2.id } });
      await table.update({ where: `id = '${mem2.id}'`, values: { superseded_by: mem3.id } });

      const results = await service.search("cats pets", 10);
      const ids = results.map((r) => r.id);
      const uniqueIds = [...new Set(ids)];
      expect(ids.length).toBe(uniqueIds.length);
      expect(uniqueIds).toContain(mem3.id);
      expect(uniqueIds).not.toContain(mem1.id);
      expect(uniqueIds).not.toContain(mem2.id);
    });
  });
});

describe("MemoryRepository", () => {
  let db: lancedb.Connection;
  let repository: MemoryRepository;
  let tmpDir: string;

  beforeEach(async () => {
    tmpDir = mkdtempSync(join(tmpdir(), "vector-memory-mcp-test-"));
    const dbPath = join(tmpDir, "test.lancedb");
    db = await connectToDatabase(dbPath);
    repository = new MemoryRepository(db);
  });

  afterEach(() => {
    rmSync(tmpDir, { recursive: true });
  });

  describe("findSimilar", () => {
    test("returns empty array when no memories", async () => {
      const results = await repository.findSimilar(new Array(384).fill(0), 10);
      expect(results).toBeArray();
      expect(results.length).toBe(0);
    });
  });
});
