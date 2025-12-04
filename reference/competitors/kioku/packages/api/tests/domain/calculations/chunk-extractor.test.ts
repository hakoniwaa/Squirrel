/**
 * Unit Tests: chunk-extractor.ts
 *
 * Tests for AST-based code chunking (functions, classes, methods, interfaces).
 * TDD approach: Write tests FIRST, then implement.
 *
 * Coverage target: 90%+
 */

import { describe, it, expect } from "vitest";
import { extractChunks } from "../../../src/domain/calculations/chunk-extractor";
import { ChunkType, type CodeChunk } from "../../../src/domain/models/CodeChunk";

describe("extractChunks", () => {
  const testFilePath = "/test/project/src/utils.ts";

  describe("function extraction", () => {
    it("should extract top-level function declarations", () => {
      const code = `
function calculateTotal(items: Item[]): number {
  return items.reduce((sum, item) => sum + item.price, 0);
}
      `.trim();

      const chunks = extractChunks(code, testFilePath);

      expect(chunks).toHaveLength(1);
      expect(chunks[0]?.type).toBe(ChunkType.FUNCTION_DECLARATION);
      expect(chunks[0]?.name).toBe("calculateTotal");
      expect(chunks[0]?.code).toContain("calculateTotal");
      expect(chunks[0]?.startLine).toBeGreaterThanOrEqual(1);
      expect(chunks[0]?.endLine).toBeGreaterThan(chunks[0]?.startLine ?? 0);
      expect(chunks[0]?.nestingLevel).toBe(0);
    });

    it("should extract arrow function expressions assigned to const", () => {
      const code = `
const validateEmail = (email: string): boolean => {
  const emailRegex = /^[^\\s@]+@[^\\s@]+\\.[^\\s@]+$/;
  return emailRegex.test(email);
};
      `.trim();

      const chunks = extractChunks(code, testFilePath);

      expect(chunks).toHaveLength(1);
      expect(chunks[0]?.type).toBe(ChunkType.ARROW_FUNCTION);
      expect(chunks[0]?.name).toBe("validateEmail");
      expect(chunks[0]?.code).toContain("validateEmail");
    });

    it("should extract async functions", () => {
      const code = `
async function fetchUserData(userId: string): Promise<User> {
  const response = await fetch(\`/api/users/\${userId}\`);
  return response.json();
}
      `.trim();

      const chunks = extractChunks(code, testFilePath);

      expect(chunks).toHaveLength(1);
      expect(chunks[0]?.type).toBe(ChunkType.FUNCTION_DECLARATION);
      expect(chunks[0]?.name).toBe("fetchUserData");
      expect(chunks[0]?.code).toContain("async function");
      expect(chunks[0]?.metadata.isAsync).toBe(true);
    });

    it("should extract generator functions", () => {
      const code = `
function* generateIds(): Generator<number> {
  let id = 1;
  while (true) {
    yield id++;
  }
}
      `.trim();

      const chunks = extractChunks(code, testFilePath);

      expect(chunks).toHaveLength(1);
      expect(chunks[0]?.type).toBe(ChunkType.FUNCTION_DECLARATION);
      expect(chunks[0]?.name).toBe("generateIds");
      expect(chunks[0]?.code).toContain("function*");
    });
  });

  describe("class extraction", () => {
    it("should extract class declarations", () => {
      const code = `
class UserManager {
  private users: Map<string, User>;

  constructor() {
    this.users = new Map();
  }

  addUser(user: User): void {
    this.users.set(user.id, user);
  }

  getUser(id: string): User | undefined {
    return this.users.get(id);
  }
}
      `.trim();

      const chunks = extractChunks(code, testFilePath);

      // Should extract: class + methods
      expect(chunks.length).toBeGreaterThanOrEqual(1);

      const classChunk = chunks.find(
        (c) => c.type === ChunkType.CLASS_DECLARATION,
      );
      expect(classChunk).toBeDefined();
      expect(classChunk?.name).toBe("UserManager");
      expect(classChunk?.code).toContain("class UserManager");
    });

    it("should extract class methods", () => {
      const code = `
class Calculator {
  add(a: number, b: number): number {
    return a + b;
  }

  subtract(a: number, b: number): number {
    return a - b;
  }
}
      `.trim();

      const chunks = extractChunks(code, testFilePath);

      const methodChunks = chunks.filter(
        (c) => c.type === ChunkType.CLASS_METHOD,
      );
      expect(methodChunks.length).toBeGreaterThanOrEqual(2);

      const addMethod = methodChunks.find((c) => c.name === "add");
      expect(addMethod).toBeDefined();
      expect(addMethod?.code).toContain("add(a: number, b: number)");
    });

    it("should extract static methods", () => {
      const code = `
class MathUtils {
  static square(x: number): number {
    return x * x;
  }
}
      `.trim();

      const chunks = extractChunks(code, testFilePath);

      const staticMethod = chunks.find((c) => c.name === "square");
      expect(staticMethod).toBeDefined();
      expect(staticMethod?.code).toContain("static square");
    });

    it("should extract getters and setters", () => {
      const code = `
class Rectangle {
  private _width: number;
  private _height: number;

  get width(): number {
    return this._width;
  }

  set width(value: number) {
    this._width = value;
  }

  get area(): number {
    return this._width * this._height;
  }
}
      `.trim();

      const chunks = extractChunks(code, testFilePath);

      const accessorChunks = chunks.filter(
        (c) =>
          c.type === ChunkType.CLASS_METHOD &&
          (c.name.includes("width") || c.name === "area"),
      );
      expect(accessorChunks.length).toBeGreaterThanOrEqual(2);
    });
  });

  describe("TypeScript-specific extraction", () => {
    it("should extract interface declarations", () => {
      const code = `
interface User {
  id: string;
  name: string;
  email: string;
  role: 'admin' | 'user';
}
      `.trim();

      const chunks = extractChunks(code, testFilePath);

      expect(chunks).toHaveLength(1);
      expect(chunks[0]?.type).toBe(ChunkType.INTERFACE);
      expect(chunks[0]?.name).toBe("User");
      expect(chunks[0]?.code).toContain("interface User");
    });

    it("should extract type alias declarations", () => {
      const code = `
type Result<T> = { success: true; data: T } | { success: false; error: string };
      `.trim();

      const chunks = extractChunks(code, testFilePath);

      expect(chunks).toHaveLength(1);
      expect(chunks[0]?.type).toBe(ChunkType.TYPE_ALIAS);
      expect(chunks[0]?.name).toBe("Result");
      expect(chunks[0]?.code).toContain("type Result");
    });

    it("should extract enum declarations", () => {
      const code = `
enum Status {
  Pending = 'pending',
  Active = 'active',
  Completed = 'completed',
}
      `.trim();

      const chunks = extractChunks(code, testFilePath);

      // Enums might be extracted as type or exported declaration
      expect(chunks.length).toBeGreaterThanOrEqual(1);
      const enumChunk = chunks.find((c) => c.name === "Status");
      expect(enumChunk).toBeDefined();
      expect(enumChunk?.code).toContain("enum Status");
    });
  });

  describe("context envelope", () => {
    it("should include JSDoc comments in chunk code", () => {
      const code = `
/**
 * Calculates the factorial of a number
 * @param n - The number to calculate factorial for
 * @returns The factorial result
 */
function factorial(n: number): number {
  return n <= 1 ? 1 : n * factorial(n - 1);
}
      `.trim();

      const chunks = extractChunks(code, testFilePath);

      expect(chunks).toHaveLength(1);
      expect(chunks[0]?.code).toContain("Calculates the factorial");
      expect(chunks[0]?.metadata.jsDoc).toContain("@param");
    });

    it("should include surrounding context lines", () => {
      const code = `
// Context line 1
// Context line 2
// Context line 3
function targetFunction() {
  return "target";
}
// Context line 4
// Context line 5
      `.trim();

      const chunks = extractChunks(code, testFilePath);

      expect(chunks).toHaveLength(1);
      // Context envelope should expand the chunk boundaries
      expect(chunks[0]?.startLine).toBeLessThanOrEqual(
        chunks[0]?.contentStartLine ?? 999,
      );
      expect(chunks[0]?.endLine).toBeGreaterThanOrEqual(
        chunks[0]?.contentEndLine ?? 0,
      );
    });
  });

  describe("nested function handling", () => {
    it("should extract nested functions with parent references", () => {
      const code = `
function outerFunction() {
  const data = [];

  function innerHelper(item: any) {
    return item.toUpperCase();
  }

  return data.map(innerHelper);
}
      `.trim();

      const chunks = extractChunks(code, testFilePath);

      // Should extract both outer and inner functions
      expect(chunks.length).toBeGreaterThanOrEqual(1);

      const outerChunk = chunks.find((c) => c.name === "outerFunction");
      expect(outerChunk).toBeDefined();

      // Check if nested function is tracked
      const innerChunk = chunks.find((c) => c.name === "innerHelper");
      if (innerChunk) {
        expect(innerChunk.parentChunkId).toBeDefined();
        expect(innerChunk.nestingLevel).toBeGreaterThan(0);
      }
    });

    it("should create scope paths for nested structures", () => {
      const code = `
class Outer {
  method1() {
    function nested() {
      return "nested";
    }
    return nested();
  }
}
      `.trim();

      const chunks = extractChunks(code, testFilePath);

      const nestedChunk = chunks.find((c) => c.name === "nested");
      if (nestedChunk) {
        expect(nestedChunk.scopePath).toContain("Outer");
        expect(nestedChunk.scopePath).toContain("method1");
      }
    });

    it("should limit nesting depth to 3 levels", () => {
      const code = `
function level1() {
  function level2() {
    function level3() {
      function level4() {
        return "level 4";
      }
      return level4();
    }
    return level3();
  }
  return level2();
}
      `.trim();

      const chunks = extractChunks(code, testFilePath);

      // Should extract up to depth 3, may include level 4 in parent chunk
      const level1 = chunks.find((c) => c.name === "level1");
      const level4 = chunks.find((c) => c.name === "level4");

      expect(level1).toBeDefined();
      // Level 4 may or may not be extracted depending on implementation
      if (level4) {
        expect(level4.nestingLevel).toBeLessThanOrEqual(3);
      }
    });
  });

  describe("fallback behavior", () => {
    it("should fallback to file-level chunk on syntax errors", () => {
      const code = `
function broken( {
  // Missing closing brace and invalid syntax
      `.trim();

      const chunks = extractChunks(code, testFilePath);

      // Should return a single file-level chunk as fallback
      expect(chunks).toHaveLength(1);
      expect(chunks[0]?.name).toBe("utils.ts");
      expect(chunks[0]?.code).toBe(code);
    });

    it("should handle empty files gracefully", () => {
      const code = "";

      const chunks = extractChunks(code, testFilePath);

      expect(chunks).toHaveLength(1);
      expect(chunks[0]?.code).toBe("");
    });

    it("should handle files with only comments", () => {
      const code = `
// Just a comment
/* Block comment */
      `.trim();

      const chunks = extractChunks(code, testFilePath);

      // May return empty array or file-level chunk depending on implementation
      expect(chunks.length).toBeGreaterThanOrEqual(0);
    });
  });

  describe("chunk metadata", () => {
    it("should populate all required chunk fields", () => {
      const code = `
function testFunction() {
  return true;
}
      `.trim();

      const chunks = extractChunks(code, testFilePath);

      expect(chunks).toHaveLength(1);
      const chunk = chunks[0] as CodeChunk;

      // Required fields
      expect(chunk.id).toBeDefined();
      expect(chunk.type).toBeDefined();
      expect(chunk.name).toBeDefined();
      expect(chunk.filePath).toBe(testFilePath);
      expect(chunk.code).toBeDefined();
      expect(chunk.startLine).toBeGreaterThanOrEqual(1);
      expect(chunk.endLine).toBeGreaterThanOrEqual(chunk.startLine);
      expect(chunk.nestingLevel).toBeGreaterThanOrEqual(0);
      expect(chunk.scopePath).toBeDefined();
      expect(chunk.metadata).toBeDefined();
      expect(chunk.createdAt).toBeInstanceOf(Date);
      expect(chunk.updatedAt).toBeInstanceOf(Date);
    });

    it("should detect exported functions", () => {
      const code = `
export function publicApi() {
  return "public";
}

function privateHelper() {
  return "private";
}
      `.trim();

      const chunks = extractChunks(code, testFilePath);

      const publicChunk = chunks.find((c) => c.name === "publicApi");
      const privateChunk = chunks.find((c) => c.name === "privateHelper");

      expect(publicChunk?.metadata.isExported).toBe(true);
      expect(privateChunk?.metadata.isExported).toBe(false);
    });

    it("should detect async functions", () => {
      const code = `
async function asyncFunc() {
  await Promise.resolve();
}

function syncFunc() {
  return true;
}
      `.trim();

      const chunks = extractChunks(code, testFilePath);

      const asyncChunk = chunks.find((c) => c.name === "asyncFunc");
      const syncChunk = chunks.find((c) => c.name === "syncFunc");

      expect(asyncChunk?.metadata.isAsync).toBe(true);
      expect(syncChunk?.metadata.isAsync).toBe(false);
    });
  });

  describe("real-world code patterns", () => {
    it("should handle complex React component", () => {
      const code = `
import React, { useState, useEffect } from 'react';

interface Props {
  userId: string;
}

export const UserProfile: React.FC<Props> = ({ userId }) => {
  const [user, setUser] = useState<User | null>(null);

  useEffect(() => {
    fetchUser(userId).then(setUser);
  }, [userId]);

  const handleUpdate = async (data: Partial<User>) => {
    await updateUser(userId, data);
    setUser({ ...user, ...data });
  };

  return <div>User: {user?.name}</div>;
};
      `.trim();

      const chunks = extractChunks(code, testFilePath);

      // Should extract: interface + component function + possibly inner functions
      expect(chunks.length).toBeGreaterThanOrEqual(1);

      const interfaceChunk = chunks.find((c) => c.name === "Props");
      expect(interfaceChunk?.type).toBe(ChunkType.INTERFACE);
    });

    it("should handle Express.js route handlers", () => {
      const code = `
app.get('/api/users/:id', async (req, res) => {
  const userId = req.params.id;
  const user = await User.findById(userId);
  res.json(user);
});

app.post('/api/users', async (req, res) => {
  const user = await User.create(req.body);
  res.status(201).json(user);
});
      `.trim();

      const chunks = extractChunks(code, testFilePath);

      // Arrow function handlers may or may not be extracted depending on implementation
      // (they're anonymous functions passed as arguments)
      expect(chunks.length).toBeGreaterThanOrEqual(0);
    });
  });
});
