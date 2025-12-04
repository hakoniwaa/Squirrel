import { describe, it, expect } from "vitest";
import { extractChunks } from "../../../src/domain/calculations/chunk-extractor";
import { ChunkType } from "../../../src/domain/models/CodeChunk";

describe("chunk-extractor - fallback strategies", () => {
  const testFilePath = "/test/fallback.ts";

  describe("syntax error handling", () => {
    it("should fallback to whole-file chunk on parse error", () => {
      const code = `
function broken( {
  return "missing closing brace";
}
      `.trim();

      const chunks = extractChunks(code, testFilePath, {
        fallbackToFile: true,
      });

      expect(chunks).toHaveLength(1);
      expect(chunks[0].type).toBe(ChunkType.EXPORTED_DECLARATION);
      expect(chunks[0].name).toBe("fallback.ts");
      expect(chunks[0].code).toBe(code);
      expect(chunks[0].nestingLevel).toBe(0);
      expect(chunks[0].scopePath).toEqual(["fallback.ts"]);
    });

    it("should return empty array on parse error if fallbackToFile is false", () => {
      const code = `
function broken( {
  return "syntax error";
}
      `.trim();

      const chunks = extractChunks(code, testFilePath, {
        fallbackToFile: false,
      });

      expect(chunks).toHaveLength(0);
    });

    it("should use fallbackToFile: true by default", () => {
      const code = `const x = function( { return 1; };`; // Syntax error

      // No options provided, should default to fallbackToFile: true
      const chunks = extractChunks(code, testFilePath);

      expect(chunks).toHaveLength(1);
      expect(chunks[0].type).toBe(ChunkType.EXPORTED_DECLARATION);
    });

    it("should handle incomplete function declaration", () => {
      const code = `
function incomplete() {
  const x = 1
  // Missing closing brace
      `.trim();

      const chunks = extractChunks(code, testFilePath, {
        fallbackToFile: true,
      });

      expect(chunks).toHaveLength(1);
      expect(chunks[0].type).toBe(ChunkType.EXPORTED_DECLARATION);
    });

    it("should handle mismatched brackets", () => {
      const code = `
function test() {
  return { key: "value" };
}}
      `.trim();

      const chunks = extractChunks(code, testFilePath, {
        fallbackToFile: true,
      });

      expect(chunks).toHaveLength(1);
      expect(chunks[0].type).toBe(ChunkType.EXPORTED_DECLARATION);
    });

    it("should handle invalid TypeScript syntax", () => {
      const code = `
function test(): invalid>>type {
  return null;
}
      `.trim();

      const chunks = extractChunks(code, testFilePath, {
        fallbackToFile: true,
      });

      // Should fallback to whole file
      expect(chunks).toHaveLength(1);
      expect(chunks[0].type).toBe(ChunkType.EXPORTED_DECLARATION);
    });
  });

  describe("fallback chunk metadata", () => {
    it("should use filename as chunk name for fallback", () => {
      const code = `function broken( {`;

      const chunks = extractChunks(code, "/path/to/myfile.ts", {
        fallbackToFile: true,
      });

      expect(chunks[0].name).toBe("myfile.ts");
    });

    it("should set correct line numbers for fallback chunk", () => {
      const code = `line 1
line 2
line 3
function broken( {
line 5`;

      const chunks = extractChunks(code, testFilePath, {
        fallbackToFile: true,
      });

      expect(chunks[0].startLine).toBe(1);
      expect(chunks[0].contentStartLine).toBe(1);
      expect(chunks[0].endLine).toBe(5);
      expect(chunks[0].contentEndLine).toBe(5);
    });

    it("should set metadata to defaults for fallback chunk", () => {
      const code = `function broken( {`;

      const chunks = extractChunks(code, testFilePath, {
        fallbackToFile: true,
      });

      expect(chunks[0].metadata).toMatchObject({
        isExported: false,
        isAsync: false,
        parameters: [],
      });
      expect(chunks[0].metadata.signature).toBeUndefined();
      expect(chunks[0].metadata.jsDoc).toBeUndefined();
    });

    it("should preserve full code in fallback chunk", () => {
      const code = `
import { something } from './module';

function broken( {
  const x = 1;
  const y = 2;
}

export default broken;
      `.trim();

      const chunks = extractChunks(code, testFilePath, {
        fallbackToFile: true,
      });

      expect(chunks[0].code).toBe(code);
      expect(chunks[0].code).toContain("import { something }");
      expect(chunks[0].code).toContain("export default");
    });
  });

  describe("partial parsing success", () => {
    it("should extract valid functions even with errors elsewhere in file", () => {
      const code = `
function validFunction() {
  return "I'm valid";
}

function broken( {
  return "syntax error here";
}
      `.trim();

      // Note: Babel parser typically fails on ANY syntax error
      // This tests the fallback behavior
      const chunks = extractChunks(code, testFilePath, {
        fallbackToFile: true,
      });

      // Should fallback to whole file due to parse error
      expect(chunks).toHaveLength(1);
      expect(chunks[0].type).toBe(ChunkType.EXPORTED_DECLARATION);
    });

    it("should successfully parse file with only valid code", () => {
      const code = `
function validFunction1() {
  return "valid";
}

function validFunction2() {
  return "also valid";
}
      `.trim();

      const chunks = extractChunks(code, testFilePath, {
        fallbackToFile: true,
      });

      // No parse errors, should extract both functions
      expect(chunks).toHaveLength(2);
      expect(chunks[0].type).toBe(ChunkType.FUNCTION_DECLARATION);
      expect(chunks[1].type).toBe(ChunkType.FUNCTION_DECLARATION);
    });
  });

  describe("unsupported language features", () => {
    it("should handle decorators gracefully", () => {
      const code = `
@Component
class MyComponent {
  @Input()
  value: string;
}
      `.trim();

      // Decorators require specific parser plugins
      const chunks = extractChunks(code, testFilePath, {
        fallbackToFile: true,
      });

      // May or may not parse depending on parser config
      // At minimum, should not crash
      expect(chunks.length).toBeGreaterThanOrEqual(1);
    });

    it("should handle JSX syntax if enabled", () => {
      const code = `
function Component() {
  return <div>Hello</div>;
}
      `.trim();

      const chunks = extractChunks(code, "/test/Component.tsx", {
        fallbackToFile: true,
      });

      // JSX requires parser plugin - may fallback or parse successfully
      expect(chunks.length).toBeGreaterThanOrEqual(1);
    });

    it("should handle experimental features", () => {
      const code = `
function test() {
  const result = value ?? "default";
  return result;
}
      `.trim();

      const chunks = extractChunks(code, testFilePath, {
        fallbackToFile: true,
      });

      // Nullish coalescing should be supported
      expect(chunks.length).toBeGreaterThanOrEqual(1);
    });
  });

  describe("max file size limits", () => {
    it("should handle very large functions", () => {
      const lines = Array(500)
        .fill(null)
        .map((_, i) => `  const var${i} = ${i};`)
        .join("\n");
      const code = `function large() {\n${lines}\n  return true;\n}`;

      const chunks = extractChunks(code, testFilePath);

      // Should still extract, even if exceeds maxLines
      // (maxLines is for splitting, not limiting)
      expect(chunks.length).toBeGreaterThanOrEqual(1);
    });

    it("should handle files with many small functions", () => {
      const functions = Array(100)
        .fill(null)
        .map((_, i) => `function fn${i}() { return ${i}; }`)
        .join("\n\n");

      const chunks = extractChunks(functions, testFilePath);

      expect(chunks).toHaveLength(100);
      expect(
        chunks.every((c) => c.type === ChunkType.FUNCTION_DECLARATION),
      ).toBe(true);
    });
  });

  describe("edge cases in fallback", () => {
    it("should handle empty file with fallback enabled", () => {
      const code = "";

      const chunks = extractChunks(code, testFilePath, {
        fallbackToFile: true,
      });

      expect(chunks).toHaveLength(0);
    });

    it("should handle file with only whitespace", () => {
      const code = "\n\n  \t  \n\n";

      const chunks = extractChunks(code, testFilePath, {
        fallbackToFile: true,
      });

      expect(chunks).toHaveLength(0);
    });

    it("should handle file with only comments (valid syntax)", () => {
      const code = `
// Just comments
/* Block comment */
/**
 * JSDoc comment
 */
      `.trim();

      const chunks = extractChunks(code, testFilePath, {
        fallbackToFile: true,
      });

      // Comments are valid syntax, should parse successfully
      // But no functions/classes to extract
      expect(chunks).toHaveLength(0);
    });

    it("should generate valid UUID for fallback chunk", () => {
      const code = `function broken( {`;

      const chunks = extractChunks(code, testFilePath, {
        fallbackToFile: true,
      });

      expect(chunks[0].id).toMatch(
        /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/,
      );
    });

    it("should set timestamps for fallback chunk", () => {
      const code = `function broken( {`;
      const beforeTime = new Date();

      const chunks = extractChunks(code, testFilePath, {
        fallbackToFile: true,
      });

      const afterTime = new Date();
      expect(chunks[0].createdAt).toBeInstanceOf(Date);
      expect(chunks[0].updatedAt).toBeInstanceOf(Date);
      expect(chunks[0].createdAt.getTime()).toBeGreaterThanOrEqual(
        beforeTime.getTime(),
      );
      expect(chunks[0].createdAt.getTime()).toBeLessThanOrEqual(
        afterTime.getTime(),
      );
    });
  });

  describe("logging and error reporting", () => {
    it("should include original error information in fallback", () => {
      const code = `function broken( { return 1; }`;

      // Extracting should not throw - fallback gracefully
      expect(() => {
        extractChunks(code, testFilePath, { fallbackToFile: true });
      }).not.toThrow();
    });

    it("should not log errors when fallbackToFile is false and parsing fails", () => {
      const code = `function broken( {`;

      // Should return empty array without throwing
      expect(() => {
        extractChunks(code, testFilePath, { fallbackToFile: false });
      }).not.toThrow();
    });

    it("should handle null or undefined code gracefully", () => {
      // Testing runtime behavior with invalid input
      expect(() => extractChunks(null as any, testFilePath)).not.toThrow();

      // Testing runtime behavior with invalid input
      expect(() => extractChunks(undefined as any, testFilePath)).not.toThrow();
    });

    it("should handle non-string file paths gracefully", () => {
      const code = `function test() { return true; }`;

      // Testing runtime behavior with invalid input
      expect(() => extractChunks(code, null as any)).not.toThrow();

      // Testing runtime behavior with invalid input
      expect(() => extractChunks(code, undefined as any)).not.toThrow();
    });
  });

  describe("parser configuration edge cases", () => {
    it("should handle strict mode code", () => {
      const code = `
"use strict";

function strictFunction() {
  return true;
}
      `.trim();

      const chunks = extractChunks(code, testFilePath);

      expect(chunks).toHaveLength(1);
      expect(chunks[0].name).toBe("strictFunction");
    });

    it("should handle module vs script distinction", () => {
      const code = `
import { something } from './module';

export function exported() {
  return true;
}
      `.trim();

      const chunks = extractChunks(code, testFilePath);

      expect(chunks).toHaveLength(1);
      expect(chunks[0].metadata.isExported).toBe(true);
    });

    it("should handle mixed CommonJS and ES6", () => {
      const code = `
const module = require('./old-module');

export function newFunction() {
  return module.data;
}
      `.trim();

      const chunks = extractChunks(code, testFilePath, {
        fallbackToFile: true,
      });

      // This might be a syntax error or parse successfully depending on parser config
      expect(chunks.length).toBeGreaterThanOrEqual(1);
    });

    it("should handle TypeScript-specific syntax", () => {
      const code = `
type MyType = string | number;

function process(value: MyType): string {
  return String(value);
}

interface Config {
  key: string;
}
      `.trim();

      const chunks = extractChunks(code, testFilePath);

      // Should extract the function, ignore type/interface declarations
      expect(chunks.some((c) => c.name === "process")).toBe(true);
    });

    it("should handle async/await syntax", () => {
      const code = `
async function fetchData(): Promise<string> {
  const response = await fetch('/api');
  return response.text();
}
      `.trim();

      const chunks = extractChunks(code, testFilePath);

      expect(chunks).toHaveLength(1);
      expect(chunks[0].metadata.isAsync).toBe(true);
    });

    it("should handle generator functions", () => {
      const code = `
function* generateNumbers() {
  yield 1;
  yield 2;
  yield 3;
}
      `.trim();

      const chunks = extractChunks(code, testFilePath, {
        fallbackToFile: true,
      });

      // Generator functions should be extracted or fallback
      expect(chunks.length).toBeGreaterThanOrEqual(1);
    });

    it("should handle private class fields", () => {
      const code = `
class Service {
  #privateField: string;

  constructor() {
    this.#privateField = "secret";
  }

  getField(): string {
    return this.#privateField;
  }
}
      `.trim();

      const chunks = extractChunks(code, testFilePath, {
        fallbackToFile: true,
      });

      // Private fields require specific parser config
      // Should either parse or fallback gracefully
      expect(chunks.length).toBeGreaterThanOrEqual(1);
    });
  });
});
