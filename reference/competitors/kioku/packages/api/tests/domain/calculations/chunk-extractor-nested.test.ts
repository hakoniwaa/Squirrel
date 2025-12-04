import { describe, it, expect } from "vitest";
import { extractChunks } from "../../../src/domain/calculations/chunk-extractor";
import { ChunkType } from "../../../src/domain/models/CodeChunk";

describe("chunk-extractor - nested functions and scope handling", () => {
  const testFilePath = "/test/nested.ts";

  describe("nesting level calculation", () => {
    it("should set nestingLevel 0 for top-level functions", () => {
      const code = `function topLevel() { return true; }`;

      const chunks = extractChunks(code, testFilePath);

      expect(chunks[0].nestingLevel).toBe(0);
    });

    it("should set nestingLevel 1 for functions nested in functions", () => {
      const code = `
function outer() {
  function inner() {
    return true;
  }
  return inner;
}
      `.trim();

      const chunks = extractChunks(code, testFilePath);

      const innerChunk = chunks.find((c) => c.name === "inner");
      expect(innerChunk?.nestingLevel).toBe(1);
    });

    it("should set nestingLevel 1 for class methods", () => {
      const code = `
class Service {
  process() {
    return true;
  }
}
      `.trim();

      const chunks = extractChunks(code, testFilePath);

      const methodChunk = chunks.find((c) => c.name === "process");
      expect(methodChunk?.nestingLevel).toBe(1);
    });

    it("should set nestingLevel 2 for functions inside methods", () => {
      const code = `
class Service {
  process() {
    function helper() {
      return true;
    }
    return helper;
  }
}
      `.trim();

      const chunks = extractChunks(code, testFilePath);

      const helperChunk = chunks.find((c) => c.name === "helper");
      expect(helperChunk?.nestingLevel).toBe(2);
    });

    it("should set nestingLevel 3 for deeply nested functions", () => {
      const code = `
function level0() {
  function level1() {
    function level2() {
      function level3() {
        return true;
      }
      return level3;
    }
    return level2;
  }
  return level1;
}
      `.trim();

      const chunks = extractChunks(code, testFilePath);

      const level3Chunk = chunks.find((c) => c.name === "level3");
      expect(level3Chunk?.nestingLevel).toBe(3);
    });
  });

  describe("nesting depth limits (maxNestingDepth)", () => {
    it("should create separate chunks for nesting <= maxNestingDepth", () => {
      const code = `
function outer() {
  function middle() {
    function inner() {
      return true;
    }
    return inner;
  }
  return middle;
}
      `.trim();

      const chunks = extractChunks(code, testFilePath, { maxDepth: 3 });

      // All 3 functions should be separate chunks
      expect(chunks).toHaveLength(3);
      expect(chunks.map((c) => c.name)).toContain("outer");
      expect(chunks.map((c) => c.name)).toContain("middle");
      expect(chunks.map((c) => c.name)).toContain("inner");
    });

    it("should merge deeply nested functions into parent when exceeding maxNestingDepth", () => {
      const code = `
function level0() {
  function level1() {
    function level2() {
      function level3() {
        function level4() {
          return true;
        }
        return level4;
      }
      return level3;
    }
    return level2;
  }
  return level1;
}
      `.trim();

      const chunks = extractChunks(code, testFilePath, { maxDepth: 2 });

      // Only level0, level1, level2 should be separate chunks
      // level3 and level4 should be merged into level2
      expect(chunks).toHaveLength(3);
      expect(chunks.map((c) => c.name)).toEqual(
        expect.arrayContaining(["level0", "level1", "level2"]),
      );
      expect(chunks.map((c) => c.name)).not.toContain("level3");
      expect(chunks.map((c) => c.name)).not.toContain("level4");

      // level2's code should include level3 and level4
      const level2Chunk = chunks.find((c) => c.name === "level2");
      expect(level2Chunk?.code).toContain("function level3");
      expect(level2Chunk?.code).toContain("function level4");
    });

    it("should respect default maxNestingDepth of 3", () => {
      const code = `
function a() {
  function b() {
    function c() {
      function d() {
        function e() {
          return 5;
        }
        return e;
      }
      return d;
    }
    return c;
  }
  return b;
}
      `.trim();

      // No options provided, should use default maxNestingDepth: 3
      const chunks = extractChunks(code, testFilePath);

      // a, b, c, d should be separate (levels 0-3)
      // e (level 4) should be merged into d
      expect(chunks).toHaveLength(4);
      expect(chunks.map((c) => c.name)).toContain("d");
      expect(chunks.map((c) => c.name)).not.toContain("e");
    });
  });

  describe("minimum lines threshold (minLines)", () => {
    it("should create separate chunk for small function if nesting level is 0", () => {
      const code = `
function tiny() {
  return 1;
}
      `.trim();

      const chunks = extractChunks(code, testFilePath);

      // Top-level functions always get separate chunks regardless of size
      expect(chunks).toHaveLength(1);
      expect(chunks[0].name).toBe("tiny");
    });

    it("should merge small nested function into parent", () => {
      const code = `
function parent() {
  const x = 1;

  function tinyHelper() {
    return x + 1;
  }

  return tinyHelper();
}
      `.trim();

      const chunks = extractChunks(code, testFilePath);

      // tinyHelper is < 5 lines and nested, should be merged into parent
      expect(chunks).toHaveLength(1);
      expect(chunks[0].name).toBe("parent");
      expect(chunks[0].code).toContain("function tinyHelper");
    });

    it("should create separate chunk for nested function >= minLines", () => {
      const code = `
function parent() {
  function largeHelper() {
    const a = 1;
    const b = 2;
    const c = 3;
    const d = 4;
    const e = 5;
    const f = 6;
    return a + b + c + d + e + f;
  }
  return largeHelper();
}
      `.trim();

      const chunks = extractChunks(code, testFilePath);

      // largeHelper is >= 5 lines, should be separate chunk
      expect(chunks).toHaveLength(2);
      expect(chunks.map((c) => c.name)).toContain("parent");
      expect(chunks.map((c) => c.name)).toContain("largeHelper");
    });

    it("should use default minLines of 5", () => {
      const code = `
function outer() {
  function tiny() {
    return 1;
  }
  return tiny();
}
      `.trim();

      // No options, should use default minLines: 5
      const chunks = extractChunks(code, testFilePath);

      // tiny is < 5 lines, should be merged
      expect(chunks).toHaveLength(1);
      expect(chunks[0].name).toBe("outer");
    });
  });

  describe("parent-child relationships", () => {
    it("should set parentChunkId for nested function", () => {
      const code = `
function parent() {
  function child() {
    const x = 1;
    const y = 2;
    const z = 3;
    return x + y + z;
  }
  return child;
}
      `.trim();

      const chunks = extractChunks(code, testFilePath);

      const parentChunk = chunks.find((c) => c.name === "parent");
      const childChunk = chunks.find((c) => c.name === "child");

      expect(childChunk?.parentChunkId).toBe(parentChunk?.id);
    });

    it("should set parentChunkId for class methods", () => {
      const code = `
class Service {
  process() {
    return true;
  }
}
      `.trim();

      const chunks = extractChunks(code, testFilePath);

      const classChunk = chunks.find(
        (c) => c.type === ChunkType.CLASS_DECLARATION,
      );
      const methodChunk = chunks.find((c) => c.name === "process");

      expect(methodChunk?.parentChunkId).toBe(classChunk?.id);
    });

    it("should chain parentChunkId for multi-level nesting", () => {
      const code = `
function level0() {
  function level1() {
    const x = 1;
    const y = 2;
    const z = 3;
    function level2() {
      const a = 4;
      const b = 5;
      const c = 6;
      return a + b + c;
    }
    return level2;
  }
  return level1;
}
      `.trim();

      const chunks = extractChunks(code, testFilePath);

      const level0Chunk = chunks.find((c) => c.name === "level0");
      const level1Chunk = chunks.find((c) => c.name === "level1");
      const level2Chunk = chunks.find((c) => c.name === "level2");

      expect(level0Chunk?.parentChunkId).toBeUndefined();
      expect(level1Chunk?.parentChunkId).toBe(level0Chunk?.id);
      expect(level2Chunk?.parentChunkId).toBe(level1Chunk?.id);
    });

    it("should not set parentChunkId for top-level siblings", () => {
      const code = `
function first() { return 1; }
function second() { return 2; }
      `.trim();

      const chunks = extractChunks(code, testFilePath);

      expect(chunks[0].parentChunkId).toBeUndefined();
      expect(chunks[1].parentChunkId).toBeUndefined();
    });
  });

  describe("scope path construction", () => {
    it("should build scope path for single-level nesting", () => {
      const code = `
function outer() {
  function inner() {
    return true;
  }
  return inner;
}
      `.trim();

      const chunks = extractChunks(code, testFilePath);

      const innerChunk = chunks.find((c) => c.name === "inner");
      expect(innerChunk?.scopePath).toEqual(["outer", "inner"]);
    });

    it("should build scope path for class -> method", () => {
      const code = `
class UserService {
  findUser() {
    return null;
  }
}
      `.trim();

      const chunks = extractChunks(code, testFilePath);

      const methodChunk = chunks.find((c) => c.name === "findUser");
      expect(methodChunk?.scopePath).toEqual(["UserService", "findUser"]);
    });

    it("should build scope path for class -> method -> closure", () => {
      const code = `
class DataProcessor {
  process() {
    const transform = () => {
      return {};
    };
    return transform;
  }
}
      `.trim();

      const chunks = extractChunks(code, testFilePath);

      const transformChunk = chunks.find((c) => c.name === "transform");
      expect(transformChunk?.scopePath).toEqual([
        "DataProcessor",
        "process",
        "transform",
      ]);
    });

    it("should build deep scope paths correctly", () => {
      const code = `
function a() {
  function b() {
    function c() {
      function d() {
        return 4;
      }
      return d;
    }
    return c;
  }
  return b;
}
      `.trim();

      const chunks = extractChunks(code, testFilePath);

      expect(chunks.find((c) => c.name === "a")?.scopePath).toEqual(["a"]);
      expect(chunks.find((c) => c.name === "b")?.scopePath).toEqual(["a", "b"]);
      expect(chunks.find((c) => c.name === "c")?.scopePath).toEqual([
        "a",
        "b",
        "c",
      ]);
      expect(chunks.find((c) => c.name === "d")?.scopePath).toEqual([
        "a",
        "b",
        "c",
        "d",
      ]);
    });
  });

  describe("arrow functions and closures", () => {
    it("should extract arrow function as separate chunk if >= minLines", () => {
      const code = `
function parent() {
  const helper = (x: number) => {
    const a = x * 2;
    const b = a + 1;
    const c = b * 3;
    const d = c - 5;
    return d;
  };
  return helper;
}
      `.trim();

      const chunks = extractChunks(code, testFilePath);

      expect(chunks).toHaveLength(2);
      expect(chunks.map((c) => c.name)).toContain("helper");
    });

    it("should merge small arrow function into parent", () => {
      const code = `
function parent() {
  const tiny = () => 1;
  return tiny();
}
      `.trim();

      const chunks = extractChunks(code, testFilePath);

      expect(chunks).toHaveLength(1);
      expect(chunks[0].name).toBe("parent");
    });

    it("should handle immediately invoked function expressions (IIFE)", () => {
      const code = `
const result = (function() {
  const x = 1;
  const y = 2;
  const z = 3;
  return x + y + z;
})();
      `.trim();

      const chunks = extractChunks(code, testFilePath);

      // IIFE should be extracted if >= minLines
      expect(chunks.length).toBeGreaterThanOrEqual(1);
    });
  });

  describe("complex nesting scenarios", () => {
    it("should handle class with nested method containing closure", () => {
      const code = `
export class EventHandler {
  constructor(private logger: Logger) {}

  handleEvent(event: Event): void {
    const validator = (data: any): boolean => {
      const line1 = true;
      const line2 = true;
      const line3 = true;
      const line4 = true;
      return line1 && line2 && line3 && line4;
    };

    if (validator(event.data)) {
      this.logger.log("Valid event");
    }
  }
}
      `.trim();

      const chunks = extractChunks(code, testFilePath);

      const classChunk = chunks.find(
        (c) => c.type === ChunkType.CLASS_DECLARATION,
      );
      const constructorChunk = chunks.find((c) => c.name === "constructor");
      const handleEventChunk = chunks.find((c) => c.name === "handleEvent");
      const validatorChunk = chunks.find((c) => c.name === "validator");

      expect(classChunk).toBeDefined();
      expect(constructorChunk).toBeDefined();
      expect(handleEventChunk).toBeDefined();
      expect(validatorChunk).toBeDefined();

      expect(constructorChunk?.parentChunkId).toBe(classChunk?.id);
      expect(handleEventChunk?.parentChunkId).toBe(classChunk?.id);
      expect(validatorChunk?.parentChunkId).toBe(handleEventChunk?.id);

      expect(validatorChunk?.scopePath).toEqual([
        "EventHandler",
        "handleEvent",
        "validator",
      ]);
    });

    it("should handle multiple nested functions in same parent", () => {
      const code = `
function parent() {
  function helper1() {
    const a = 1;
    const b = 2;
    const c = 3;
    return a + b + c;
  }

  function helper2() {
    const x = 4;
    const y = 5;
    const z = 6;
    return x + y + z;
  }

  return helper1() + helper2();
}
      `.trim();

      const chunks = extractChunks(code, testFilePath);

      expect(chunks).toHaveLength(3);

      const parentChunk = chunks.find((c) => c.name === "parent");
      const helper1Chunk = chunks.find((c) => c.name === "helper1");
      const helper2Chunk = chunks.find((c) => c.name === "helper2");

      expect(helper1Chunk?.parentChunkId).toBe(parentChunk?.id);
      expect(helper2Chunk?.parentChunkId).toBe(parentChunk?.id);
    });

    it("should handle function returning function (higher-order)", () => {
      const code = `
function createMultiplier(factor: number) {
  return function multiply(value: number): number {
    const step1 = value * factor;
    const step2 = step1 + 1;
    const step3 = step2 * 2;
    return step3;
  };
}
      `.trim();

      const chunks = extractChunks(code, testFilePath);

      expect(chunks).toHaveLength(2);

      const outerChunk = chunks.find((c) => c.name === "createMultiplier");
      const innerChunk = chunks.find((c) => c.name === "multiply");

      expect(innerChunk?.parentChunkId).toBe(outerChunk?.id);
      expect(innerChunk?.scopePath).toEqual(["createMultiplier", "multiply"]);
    });
  });
});
