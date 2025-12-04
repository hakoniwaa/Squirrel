import { describe, it, expect, beforeEach, afterEach } from "vitest";
import { InitializeProject } from "../../../src/application/use-cases/InitializeProject";
import { mkdirSync, rmSync, writeFileSync, existsSync } from "fs";
import { join } from "path";

describe("InitializeProject", () => {
  let useCase: InitializeProject;
  let testProjectPath: string;

  beforeEach(() => {
    useCase = new InitializeProject();

    // Create test project directory
    testProjectPath = join(process.cwd(), "test-project-" + Date.now());
    mkdirSync(testProjectPath, { recursive: true });

    // Create package.json
    writeFileSync(
      join(testProjectPath, "package.json"),
      JSON.stringify({
        name: "test-project",
        dependencies: {
          react: "^18.0.0",
          typescript: "^5.0.0",
        },
      }),
    );

    // Create src directory structure
    mkdirSync(join(testProjectPath, "src", "domain"), { recursive: true });
    mkdirSync(join(testProjectPath, "src", "application"), { recursive: true });
    mkdirSync(join(testProjectPath, "src", "infrastructure"), {
      recursive: true,
    });

    // Create bun.lockb to indicate bun package manager
    writeFileSync(join(testProjectPath, "bun.lockb"), "");
  });

  afterEach(() => {
    // Cleanup test project
    if (existsSync(testProjectPath)) {
      rmSync(testProjectPath, { recursive: true, force: true });
    }
  });

  describe("execute", () => {
    it("should scan directory structure", async () => {
      const result = await useCase.execute(testProjectPath);

      expect(result).toBeDefined();
      expect(result.project.path).toBe(testProjectPath);
    });

    it("should detect tech stack from package.json", async () => {
      const result = await useCase.execute(testProjectPath);

      expect(result.tech.stack).toContain("React");
      expect(result.tech.stack).toContain("TypeScript");
    });

    it("should identify modules from folder structure", async () => {
      const result = await useCase.execute(testProjectPath);

      expect(result.modules).toBeDefined();
      expect(Object.keys(result.modules)).toContain("domain");
      expect(Object.keys(result.modules)).toContain("application");
      expect(Object.keys(result.modules)).toContain("infrastructure");
    });

    it("should create .context directory", async () => {
      await useCase.execute(testProjectPath);

      const contextDir = join(testProjectPath, ".context");
      expect(existsSync(contextDir)).toBe(true);
    });

    it("should generate project.yaml", async () => {
      await useCase.execute(testProjectPath);

      const yamlPath = join(testProjectPath, ".context", "project.yaml");
      expect(existsSync(yamlPath)).toBe(true);
    });

    it("should initialize SQLite database", async () => {
      await useCase.execute(testProjectPath);

      const dbPath = join(testProjectPath, ".context", "sessions.db");
      expect(existsSync(dbPath)).toBe(true);
    });

    it("should set project metadata timestamps", async () => {
      const result = await useCase.execute(testProjectPath);

      expect(result.metadata.createdAt).toBeInstanceOf(Date);
      expect(result.metadata.updatedAt).toBeInstanceOf(Date);
      expect(result.metadata.lastScanAt).toBeInstanceOf(Date);
    });

    it("should infer layered architecture pattern", async () => {
      const result = await useCase.execute(testProjectPath);

      expect(result.architecture.pattern).toBe("layered");
      expect(result.architecture.description).toContain("Onion");
    });
  });

  describe("scanProject", () => {
    it("should detect package manager from lock files", async () => {
      const result = await useCase.execute(testProjectPath);

      expect(result.tech.packageManager).toBe("bun");
    });

    it("should detect runtime from package.json or config", async () => {
      const result = await useCase.execute(testProjectPath);

      expect(result.tech.runtime).toBeDefined();
    });

    it("should set project name from package.json", async () => {
      const result = await useCase.execute(testProjectPath);

      expect(result.project.name).toBe("test-project");
    });

    it("should infer project type from dependencies", async () => {
      const result = await useCase.execute(testProjectPath);

      expect(result.project.type).toBe("web-app");
    });
  });

  describe("identifyModules", () => {
    it("should identify modules from src/ directories", async () => {
      const result = await useCase.execute(testProjectPath);

      const moduleCount = Object.keys(result.modules).length;
      expect(moduleCount).toBe(3); // domain, application, infrastructure
    });

    it("should set module descriptions", async () => {
      const result = await useCase.execute(testProjectPath);

      Object.values(result.modules).forEach((module) => {
        expect(module.description).toBeDefined();
        expect(module.description.length).toBeGreaterThan(0);
      });
    });

    it("should initialize key files array for each module", async () => {
      const result = await useCase.execute(testProjectPath);

      Object.values(result.modules).forEach((module) => {
        expect(Array.isArray(module.keyFiles)).toBe(true);
      });
    });
  });
});
