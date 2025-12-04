import { describe, expect, test } from "bun:test";
import {
  DELETED_TOMBSTONE,
  isDeleted,
  isSuperseded,
  memoryToDict,
  type Memory,
} from "../src/types/memory";

describe("types/memory", () => {
  const createMemory = (overrides: Partial<Memory> = {}): Memory => ({
    id: "test-id",
    content: "test content",
    embedding: [0.1, 0.2, 0.3],
    metadata: { key: "value" },
    createdAt: new Date("2024-01-01T00:00:00Z"),
    updatedAt: new Date("2024-01-01T00:00:00Z"),
    supersededBy: null,
    ...overrides,
  });

  describe("DELETED_TOMBSTONE", () => {
    test("should be 'DELETED'", () => {
      expect(DELETED_TOMBSTONE).toBe("DELETED");
    });
  });

  describe("isDeleted", () => {
    test("returns true when supersededBy is DELETED", () => {
      const memory = createMemory({ supersededBy: DELETED_TOMBSTONE });
      expect(isDeleted(memory)).toBe(true);
    });

    test("returns false when supersededBy is null", () => {
      const memory = createMemory({ supersededBy: null });
      expect(isDeleted(memory)).toBe(false);
    });

    test("returns false when supersededBy is another ID", () => {
      const memory = createMemory({ supersededBy: "other-id" });
      expect(isDeleted(memory)).toBe(false);
    });
  });

  describe("isSuperseded", () => {
    test("returns true when supersededBy is set", () => {
      const memory = createMemory({ supersededBy: "other-id" });
      expect(isSuperseded(memory)).toBe(true);
    });

    test("returns true when supersededBy is DELETED", () => {
      const memory = createMemory({ supersededBy: DELETED_TOMBSTONE });
      expect(isSuperseded(memory)).toBe(true);
    });

    test("returns false when supersededBy is null", () => {
      const memory = createMemory({ supersededBy: null });
      expect(isSuperseded(memory)).toBe(false);
    });
  });

  describe("memoryToDict", () => {
    test("converts memory to dictionary with ISO dates", () => {
      const memory = createMemory();
      const dict = memoryToDict(memory);

      expect(dict).toEqual({
        id: "test-id",
        content: "test content",
        metadata: { key: "value" },
        createdAt: "2024-01-01T00:00:00.000Z",
        updatedAt: "2024-01-01T00:00:00.000Z",
        supersededBy: null,
      });
    });

    test("includes supersededBy when set", () => {
      const memory = createMemory({ supersededBy: "other-id" });
      const dict = memoryToDict(memory);

      expect(dict.supersededBy).toBe("other-id");
    });

    test("handles empty metadata", () => {
      const memory = createMemory({ metadata: {} });
      const dict = memoryToDict(memory);

      expect(dict.metadata).toEqual({});
    });
  });
});
