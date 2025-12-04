import { describe, expect, test, beforeEach, afterEach } from "bun:test";
import { mkdtempSync, rmSync } from "fs";
import { join } from "path";
import { tmpdir } from "os";
import * as lancedb from "@lancedb/lancedb";
import { tools } from "../src/mcp/tools";
import {
  handleToolCall,
  handleStoreMemory,
  handleDeleteMemory,
  handleSearchMemories,
  handleGetMemory,
} from "../src/mcp/handlers";
import { createServer } from "../src/mcp/server";
import { connectToDatabase } from "../src/db/connection";
import { MemoryRepository } from "../src/db/memory.repository";
import { EmbeddingsService } from "../src/services/embeddings.service";
import { MemoryService } from "../src/services/memory.service";

describe("mcp", () => {
  let db: lancedb.Connection;
  let service: MemoryService;
  let tmpDir: string;

  beforeEach(async () => {
    tmpDir = mkdtempSync(join(tmpdir(), "vector-memory-mcp-test-"));
    const dbPath = join(tmpDir, "test.lancedb");
    db = await connectToDatabase(dbPath);
    const repository = new MemoryRepository(db);
    const embeddings = new EmbeddingsService("Xenova/all-MiniLM-L6-v2", 384);
    service = new MemoryService(repository, embeddings);
  });

  afterEach(() => {
    rmSync(tmpDir, { recursive: true });
  });

  describe("tools", () => {
    test("exports 4 tools", () => {
      expect(tools).toBeArray();
      expect(tools.length).toBe(4);
    });

    test("has store_memory tool", () => {
      const tool = tools.find((t) => t.name === "store_memory");
      expect(tool).toBeDefined();
      expect(tool!.inputSchema.required).toContain("content");
    });

    test("has delete_memory tool", () => {
      const tool = tools.find((t) => t.name === "delete_memory");
      expect(tool).toBeDefined();
      expect(tool!.inputSchema.required).toContain("id");
    });

    test("has search_memories tool", () => {
      const tool = tools.find((t) => t.name === "search_memories");
      expect(tool).toBeDefined();
      expect(tool!.inputSchema.required).toContain("query");
    });

    test("has get_memory tool", () => {
      const tool = tools.find((t) => t.name === "get_memory");
      expect(tool).toBeDefined();
      expect(tool!.inputSchema.required).toContain("id");
    });
  });

  describe("handleStoreMemory", () => {
    test("stores memory and returns ID", async () => {
      const response = await handleStoreMemory({ content: "test content" }, service);

      expect(response.content).toBeArray();
      expect(response.content[0].type).toBe("text");
      expect(response.content[0].text).toMatch(/Memory stored with ID: .+/);
    });

    test("stores memory with metadata", async () => {
      const response = await handleStoreMemory(
        { content: "test", metadata: { key: "value" } },
        service
      );

      expect(response.content[0].text).toMatch(/Memory stored with ID:/);

      const idMatch = response.content[0].text.match(/Memory stored with ID: (.+)/);
      const memory = await service.get(idMatch![1]);
      expect(memory!.metadata).toEqual({ key: "value" });
    });
  });

  describe("handleDeleteMemory", () => {
    test("deletes existing memory", async () => {
      const mem = await service.store("test");

      const response = await handleDeleteMemory({ id: mem.id }, service);

      expect(response.content[0].text).toBe(`Memory ${mem.id} deleted successfully`);
    });

    test("returns not found for non-existent ID", async () => {
      const response = await handleDeleteMemory({ id: "non-existent" }, service);

      expect(response.content[0].text).toBe("Memory non-existent not found");
    });
  });

  describe("handleSearchMemories", () => {
    test("returns matching memories", async () => {
      await service.store("Python programming language");
      await service.store("JavaScript web development");

      const response = await handleSearchMemories({ query: "programming" }, service);

      expect(response.content[0].text).toContain("Python");
    });

    test("returns no memories message when empty", async () => {
      const response = await handleSearchMemories({ query: "nonexistent" }, service);

      expect(response.content[0].text).toBe("No memories found matching your query.");
    });

    test("respects limit parameter", async () => {
      await service.store("Memory 1");
      await service.store("Memory 2");
      await service.store("Memory 3");

      const response = await handleSearchMemories(
        { query: "memory", limit: 1 },
        service
      );

      expect(response.content[0].text).not.toContain("---");
    });

    test("includes metadata in results", async () => {
      await service.store("Test memory", { tag: "important" });

      const response = await handleSearchMemories({ query: "test" }, service);

      expect(response.content[0].text).toContain("Metadata:");
      expect(response.content[0].text).toContain("important");
    });

    test("separates multiple results with ---", async () => {
      await service.store("First memory");
      await service.store("Second memory");

      const response = await handleSearchMemories(
        { query: "memory", limit: 2 },
        service
      );

      expect(response.content[0].text).toContain("---");
    });
  });

  describe("handleGetMemory", () => {
    test("returns memory details", async () => {
      const mem = await service.store("test content", { key: "value" });

      const response = await handleGetMemory({ id: mem.id }, service);

      const text = response.content[0].text;
      expect(text).toContain(`ID: ${mem.id}`);
      expect(text).toContain("Content: test content");
      expect(text).toContain("Metadata:");
      expect(text).toContain("Created:");
      expect(text).toContain("Updated:");
    });

    test("returns not found for non-existent ID", async () => {
      const response = await handleGetMemory({ id: "non-existent" }, service);

      expect(response.content[0].text).toBe("Memory non-existent not found");
    });

    test("includes supersededBy when set", async () => {
      const mem = await service.store("test");
      await service.delete(mem.id);

      const response = await handleGetMemory({ id: mem.id }, service);

      expect(response.content[0].text).toContain("Superseded by: DELETED");
    });

    test("omits metadata line when empty", async () => {
      const mem = await service.store("test");

      const response = await handleGetMemory({ id: mem.id }, service);

      expect(response.content[0].text).not.toContain("Metadata:");
    });
  });

  describe("handleToolCall", () => {
    test("routes to store_memory", async () => {
      const response = await handleToolCall(
        "store_memory",
        { content: "test" },
        service
      );
      expect(response.content[0].text).toMatch(/Memory stored with ID:/);
    });

    test("routes to delete_memory", async () => {
      const mem = await service.store("test");
      const response = await handleToolCall("delete_memory", { id: mem.id }, service);
      expect(response.content[0].text).toContain("deleted successfully");
    });

    test("routes to search_memories", async () => {
      await service.store("test content");
      const response = await handleToolCall(
        "search_memories",
        { query: "test" },
        service
      );
      expect(response.content[0].text).toContain("test content");
    });

    test("routes to get_memory", async () => {
      const mem = await service.store("test");
      const response = await handleToolCall("get_memory", { id: mem.id }, service);
      expect(response.content[0].text).toContain(mem.id);
    });

    test("returns error for unknown tool", async () => {
      const response = await handleToolCall("unknown_tool", {}, service);

      expect(response.content[0].text).toBe("Unknown tool: unknown_tool");
      expect(response.isError).toBe(true);
    });
  });

  describe("createServer", () => {
    test("creates server instance", () => {
      const server = createServer(service);
      expect(server).toBeDefined();
    });
  });
});
