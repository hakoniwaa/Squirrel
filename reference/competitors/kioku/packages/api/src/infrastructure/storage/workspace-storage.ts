/**
 * Workspace Storage Adapter
 *
 * Manages workspace.yaml for multi-project linking
 *
 * @module infrastructure/storage
 */

import { readFileSync, writeFileSync, existsSync } from "fs";
import { parse, stringify } from "yaml";
import { join } from "path";
import { logger } from "../cli/logger";
import type { LinkedProject } from "domain/models/LinkedProject";

export interface Workspace {
  version: string;
  primary_project: {
    path: string;
    name: string;
  };
  linked_projects: LinkedProject[];
  last_updated: string;
}

export class WorkspaceStorage {
  private workspacePath: string;

  constructor(contextDir: string) {
    this.workspacePath = join(contextDir, "workspace.yaml");
  }

  /**
   * Load workspace configuration
   */
  load(): Workspace | null {
    try {
      if (!existsSync(this.workspacePath)) {
        logger.debug("Workspace file does not exist", {
          path: this.workspacePath,
        });
        return null;
      }

      const content = readFileSync(this.workspacePath, "utf-8");
      const workspace = parse(content) as Workspace;

      logger.debug("Workspace loaded", {
        path: this.workspacePath,
        linkedProjects: workspace.linked_projects?.length || 0,
      });

      return workspace;
    } catch (error) {
      logger.error("Failed to load workspace", {
        error,
        path: this.workspacePath,
      });
      return null;
    }
  }

  /**
   * Save workspace configuration
   */
  save(workspace: Workspace): void {
    try {
      workspace.last_updated = new Date().toISOString();
      const yaml = stringify(workspace);
      writeFileSync(this.workspacePath, yaml, "utf-8");

      logger.info("Workspace saved", {
        path: this.workspacePath,
        linkedProjects: workspace.linked_projects?.length || 0,
      });
    } catch (error) {
      logger.error("Failed to save workspace", {
        error,
        path: this.workspacePath,
      });
      throw error;
    }
  }

  /**
   * Initialize workspace with primary project
   */
  initialize(projectPath: string, projectName: string): Workspace {
    const workspace: Workspace = {
      version: "2.0.0",
      primary_project: {
        path: projectPath,
        name: projectName,
      },
      linked_projects: [],
      last_updated: new Date().toISOString(),
    };

    this.save(workspace);
    return workspace;
  }

  /**
   * Add linked project to workspace
   */
  addLinkedProject(project: LinkedProject): void {
    const workspace = this.load();
    if (!workspace) {
      throw new Error("Workspace not initialized. Run 'kioku init' first.");
    }

    // Check if project already linked
    const existing = workspace.linked_projects.find(
      (p) => p.path === project.path,
    );
    if (existing) {
      logger.warn("Project already linked", { path: project.path });
      return;
    }

    workspace.linked_projects.push(project);
    this.save(workspace);

    logger.info("Linked project added", {
      path: project.path,
      name: project.name,
    });
  }

  /**
   * Remove linked project from workspace
   */
  removeLinkedProject(projectPath: string): void {
    const workspace = this.load();
    if (!workspace) {
      throw new Error("Workspace not initialized");
    }

    const index = workspace.linked_projects.findIndex(
      (p) => p.path === projectPath,
    );
    if (index === -1) {
      logger.warn("Project not found in workspace", { path: projectPath });
      return;
    }

    workspace.linked_projects.splice(index, 1);
    this.save(workspace);

    logger.info("Linked project removed", { path: projectPath });
  }

  /**
   * Get all linked projects
   */
  getLinkedProjects(): LinkedProject[] {
    const workspace = this.load();
    return workspace?.linked_projects || [];
  }

  /**
   * Update linked project status
   */
  updateProjectStatus(
    projectPath: string,
    status: LinkedProject["status"],
  ): void {
    const workspace = this.load();
    if (!workspace) {
      throw new Error("Workspace not initialized");
    }

    const project = workspace.linked_projects.find(
      (p) => p.path === projectPath,
    );
    if (!project) {
      logger.warn("Project not found in workspace", { path: projectPath });
      return;
    }

    project.status = status;
    this.save(workspace);

    logger.debug("Project status updated", { path: projectPath, status });
  }

  /**
   * Check if workspace exists
   */
  exists(): boolean {
    return existsSync(this.workspacePath);
  }
}
