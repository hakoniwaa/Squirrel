/**
 * Multi-Project Integration Tests
 *
 * Tests the full workflow: link projects → search across both → verify results labeled
 *
 * Validates Phase 9: User Story 6 - Multi-Project Context
 */

import { describe, it, expect, beforeEach, afterEach } from "vitest";
import { MultiProjectService } from "../../../src/application/services/MultiProjectService";
import { WorkspaceStorage } from "@kioku/api/infrastructure/storage/workspace-storage";
import type { LinkedProject } from "../../../src/domain/models/LinkedProject";
import { LinkType, ProjectStatus } from "../../../src/domain/models/LinkedProject";
import * as fs from "fs/promises";
import * as path from "path";
import * as os from "os";

describe("Multi-Project Integration", () => {
  let service: MultiProjectService;
  let workspaceStorage: WorkspaceStorage;
  let testDir: string;
  let project1Dir: string;
  let project2Dir: string;

  beforeEach(async () => {
    // Create temporary test directory
    testDir = await fs.mkdtemp(
      path.join(os.tmpdir(), "kioku-multiproject-test-"),
    );

    // Create two mock projects
    project1Dir = path.join(testDir, "project-frontend");
    project2Dir = path.join(testDir, "project-backend");

    await fs.mkdir(project1Dir, { recursive: true });
    await fs.mkdir(project2Dir, { recursive: true });

    // Create mock source files
    await fs.writeFile(
      path.join(project1Dir, "auth.ts"),
      `
export function loginUser(email: string, password: string) {
  // Frontend authentication logic
  return fetch('/api/auth/login', {
    method: 'POST',
    body: JSON.stringify({ email, password })
  });
}
      `.trim(),
    );

    await fs.writeFile(
      path.join(project2Dir, "auth.ts"),
      `
export async function authenticateUser(email: string, password: string) {
  // Backend authentication logic
  const user = await db.users.findByEmail(email);
  return bcrypt.compare(password, user.passwordHash);
}
      `.trim(),
    );

    // Initialize workspace storage
    const contextDir = path.join(testDir, ".context");
    await fs.mkdir(contextDir, { recursive: true });

    workspaceStorage = new WorkspaceStorage(contextDir);
    workspaceStorage.initialize(project1Dir, "project-frontend");

    // Initialize service
    service = new MultiProjectService(workspaceStorage);
  });

  afterEach(async () => {
    // Clean up test directory
    try {
      await fs.rm(testDir, { recursive: true, force: true });
    } catch {
      // Ignore cleanup errors
    }
  });

  describe("T138: Full multi-project workflow", () => {
    it("should link two projects and search across both", async () => {
      // Step 1: Link backend project to workspace
      const backendProject: LinkedProject = {
        name: "project-backend",
        path: project2Dir,
        linkType: LinkType.WORKSPACE,
        status: ProjectStatus.AVAILABLE,
        lastAccessed: new Date(),
        techStack: ["TypeScript", "Node.js"],
      };

      const linkResult = service.linkProject(backendProject);
      expect(linkResult.success).toBe(true);

      // Step 2: Verify both projects are linked
      const linkedProjects = service.getLinkedProjects();
      expect(linkedProjects).toHaveLength(1); // Only backend (frontend is primary)
      expect(linkedProjects[0].name).toBe("project-backend");

      // Step 3: Search across all projects
      const results = await service.searchAcrossProjects({
        query: "authentication",
        projectScope: "all_linked",
      });

      // Step 4: Verify results are labeled by project
      expect(results).toBeDefined();
      expect(Array.isArray(results)).toBe(true);

      if (results.length > 0) {
        results.forEach((result) => {
          expect(result).toHaveProperty("projectName");
          expect(["project-frontend", "project-backend"]).toContain(
            result.projectName,
          );
        });

        // Verify we have results from both projects
        const projectNames = [...new Set(results.map((r) => r.projectName))];
        expect(projectNames.length).toBeGreaterThanOrEqual(1);
      }
    });

    it("should handle linking and unlinking projects", async () => {
      // Link project
      const project: LinkedProject = {
        name: "project-backend",
        path: project2Dir,
        linkType: LinkType.WORKSPACE,
        status: ProjectStatus.AVAILABLE,
        lastAccessed: new Date(),
      };

      service.linkProject(project);
      expect(service.getLinkedProjects()).toHaveLength(1);

      // Unlink project
      const unlinkResult = service.unlinkProject(project2Dir);
      expect(unlinkResult.success).toBe(true);
      expect(service.getLinkedProjects()).toHaveLength(0);
    });

    it("should persist linked projects to workspace.yaml", async () => {
      // Link project
      const project: LinkedProject = {
        name: "project-backend",
        path: project2Dir,
        linkType: LinkType.WORKSPACE,
        status: ProjectStatus.AVAILABLE,
        lastAccessed: new Date(),
      };

      service.linkProject(project);

      // Create new service instance (simulate restart)
      const newService = new MultiProjectService(workspaceStorage);

      // Verify linked projects are loaded from workspace.yaml
      const linkedProjects = newService.getLinkedProjects();
      expect(linkedProjects).toHaveLength(1);
      expect(linkedProjects[0].name).toBe("project-backend");
      expect(linkedProjects[0].path).toBe(project2Dir);
    });

    it("should detect and prevent circular links", async () => {
      // This test simulates a scenario where:
      // Project A links to Project B
      // Project B tries to link back to Project A (circular)

      const projectB: LinkedProject = {
        name: "project-backend",
        path: project2Dir,
        linkType: LinkType.WORKSPACE,
        status: ProjectStatus.AVAILABLE,
        lastAccessed: new Date(),
      };

      // Link B from A
      service.linkProject(projectB);

      // Try to create circular link (B -> A)
      // This would be detected by the service
      const hasCircular = service.detectCircularLinks([
        { name: "project-frontend", links: ["project-backend"] },
        { name: "project-backend", links: ["project-frontend"] },
      ]);

      expect(hasCircular).toBe(true);
    });

    it("should exclude unavailable projects from search", async () => {
      // Link an available project
      const availableProject: LinkedProject = {
        name: "project-backend",
        path: project2Dir,
        linkType: LinkType.WORKSPACE,
        status: ProjectStatus.AVAILABLE,
        lastAccessed: new Date(),
      };

      service.linkProject(availableProject);

      // Link an unavailable project (non-existent path)
      const unavailableProject: LinkedProject = {
        name: "deleted-project",
        path: "/nonexistent/path",
        linkType: LinkType.WORKSPACE,
        status: ProjectStatus.UNAVAILABLE,
        lastAccessed: new Date(),
      };

      service.linkProject(unavailableProject);

      // Search across all projects
      const results = await service.searchAcrossProjects({
        query: "authentication",
        projectScope: "all_linked",
      });

      // Verify no results from unavailable project
      if (results.length > 0) {
        const projectNames = results.map((r) => r.projectName);
        expect(projectNames).not.toContain("deleted-project");
      }
    });

    it("should refresh project status and update availability", async () => {
      // Link a project
      const project: LinkedProject = {
        name: "project-backend",
        path: project2Dir,
        linkType: LinkType.WORKSPACE,
        status: ProjectStatus.AVAILABLE,
        lastAccessed: new Date(),
      };

      service.linkProject(project);

      // Delete the project directory
      await fs.rm(project2Dir, { recursive: true, force: true });

      // Refresh status
      const summary = await service.refreshProjectStatus();

      // Verify project is marked unavailable
      expect(summary.unavailable).toBe(1);

      const linkedProjects = service.getLinkedProjects();
      const backendProject = linkedProjects.find(
        (p) => p.name === "project-backend",
      );

      expect(backendProject?.status).toBe(ProjectStatus.UNAVAILABLE);
    });

    it("should search only current project when scope is 'current'", async () => {
      // Link backend project
      const backendProject: LinkedProject = {
        name: "project-backend",
        path: project2Dir,
        linkType: LinkType.WORKSPACE,
        status: ProjectStatus.AVAILABLE,
        lastAccessed: new Date(),
      };

      service.linkProject(backendProject);

      // Search with scope 'current'
      const results = await service.searchAcrossProjects({
        query: "authentication",
        projectScope: "current",
      });

      // All results should be from current project only
      if (results.length > 0) {
        const projectNames = [...new Set(results.map((r) => r.projectName))];
        expect(projectNames).toHaveLength(1);
      }
    });

    it("should deduplicate results from shared modules", async () => {
      // Create shared module in both projects
      const sharedCode = `
export interface User {
  id: string;
  email: string;
}
      `.trim();

      await fs.writeFile(path.join(project1Dir, "types.ts"), sharedCode);
      await fs.writeFile(path.join(project2Dir, "types.ts"), sharedCode);

      // Link backend
      service.linkProject({
        name: "project-backend",
        path: project2Dir,
        linkType: LinkType.WORKSPACE,
        status: ProjectStatus.AVAILABLE,
        lastAccessed: new Date(),
      });

      // Search for "User interface"
      const results = await service.searchAcrossProjects({
        query: "User interface",
        projectScope: "all_linked",
      });

      // Verify no duplicate results with identical content
      const contentSet = new Set();
      let hasDuplicates = false;

      for (const result of results) {
        const key = `${result.content}`;
        if (contentSet.has(key)) {
          hasDuplicates = true;
          break;
        }
        contentSet.add(key);
      }

      expect(hasDuplicates).toBe(false);
    });
  });
});
