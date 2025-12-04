/**
 * Multi-Project Service
 *
 * Orchestrates cross-project search, link management, and circular detection
 *
 * Layer: Application (orchestration)
 * Purpose: Enable multi-project workspaces with shared context
 *
 * @module application/services
 */

import type { LinkedProject } from "domain/models/LinkedProject";
import { ProjectStatus } from "domain/models/LinkedProject";
import type { WorkspaceStorage } from "infrastructure/storage/workspace-storage";
import { logger } from "../../infrastructure/cli/logger";
import { existsSync, accessSync, constants } from "fs";

export interface LinkResult {
  success: boolean;
  project?: LinkedProject;
  error?: string;
}

export interface UnlinkResult {
  success: boolean;
  error?: string;
}

export interface SearchOptions {
  query: string;
  projectScope: "current" | "all_linked";
}

export interface MultiProjectSearchResult {
  id: string;
  content: string;
  filePath: string;
  projectName: string;
  score: number;
  finalScore?: number;
}

export interface StatusSummary {
  total: number;
  available: number;
  unavailable: number;
  initializing: number;
}

export interface ProjectWithLinks {
  name: string;
  links: string[];
}

export interface GetLinkedProjectsOptions {
  status?: ProjectStatus;
}

/**
 * MultiProjectService
 *
 * Manages multi-project linking, search aggregation, and availability checking
 */
export class MultiProjectService {
  private workspaceStorage: WorkspaceStorage | null = null;
  private linkedProjects = new Map<string, LinkedProject>();

  constructor(workspaceStorage?: WorkspaceStorage) {
    if (workspaceStorage) {
      this.workspaceStorage = workspaceStorage;
      this.loadLinkedProjects();
    }
  }

  /**
   * Load linked projects from workspace storage
   */
  private loadLinkedProjects(): void {
    if (!this.workspaceStorage) {
      return;
    }

    const projects = this.workspaceStorage.getLinkedProjects();
    projects.forEach((project) => {
      this.linkedProjects.set(project.path, project);
    });

    logger.debug("Linked projects loaded", {
      count: projects.length,
    });
  }

  /**
   * Link a new project to the workspace
   */
  linkProject(project: LinkedProject): LinkResult {
    // Check if already linked
    if (this.linkedProjects.has(project.path)) {
      logger.warn("Project already linked", { path: project.path });
      return {
        success: false,
        error: `Project at ${project.path} is already linked`,
      };
    }

    // Validate path exists (skip validation for unavailable status)
    if (
      project.status !== ProjectStatus.UNAVAILABLE &&
      !existsSync(project.path)
    ) {
      logger.warn("Project path does not exist", { path: project.path });
      return {
        success: false,
        error: `Project path ${project.path} does not exist`,
      };
    }

    // Add to linked projects
    this.linkedProjects.set(project.path, project);

    // Persist to workspace storage
    if (this.workspaceStorage) {
      this.workspaceStorage.addLinkedProject(project);
    }

    logger.info("Project linked successfully", {
      name: project.name,
      path: project.path,
    });

    return {
      success: true,
      project,
    };
  }

  /**
   * Unlink a project from the workspace
   */
  unlinkProject(projectPath: string): UnlinkResult {
    if (!this.linkedProjects.has(projectPath)) {
      logger.warn("Project not found in workspace", { path: projectPath });
      return {
        success: false,
        error: `Project at ${projectPath} not found in workspace`,
      };
    }

    // Remove from linked projects
    this.linkedProjects.delete(projectPath);

    // Persist to workspace storage
    if (this.workspaceStorage) {
      this.workspaceStorage.removeLinkedProject(projectPath);
    }

    logger.info("Project unlinked successfully", { path: projectPath });

    return {
      success: true,
    };
  }

  /**
   * Get all linked projects
   */
  getLinkedProjects(options?: GetLinkedProjectsOptions): LinkedProject[] {
    const projects = Array.from(this.linkedProjects.values());

    if (options?.status) {
      return projects.filter((p) => p.status === options.status);
    }

    return projects;
  }

  /**
   * Detect circular links using graph traversal
   *
   * Uses DFS (Depth-First Search) to detect cycles in the project link graph
   */
  detectCircularLinks(projects: ProjectWithLinks[]): boolean {
    const graph = new Map<string, string[]>();
    const visited = new Set<string>();
    const recursionStack = new Set<string>();

    // Build adjacency list
    projects.forEach((project) => {
      graph.set(project.name, project.links || []);
    });

    // DFS function to detect cycle
    const hasCycle = (node: string): boolean => {
      if (recursionStack.has(node)) {
        // Found a back edge (cycle)
        return true;
      }

      if (visited.has(node)) {
        // Already processed this node
        return false;
      }

      visited.add(node);
      recursionStack.add(node);

      const neighbors = graph.get(node) || [];
      for (const neighbor of neighbors) {
        if (hasCycle(neighbor)) {
          return true;
        }
      }

      recursionStack.delete(node);
      return false;
    };

    // Check each node
    for (const project of projects) {
      if (hasCycle(project.name)) {
        logger.warn("Circular link detected", { project: project.name });
        return true;
      }
    }

    return false;
  }

  /**
   * Search across linked projects
   */
  async searchAcrossProjects(options: SearchOptions): Promise<MultiProjectSearchResult[]> {
    const { query, projectScope } = options;

    logger.debug("Cross-project search started", {
      query,
      projectScope,
    });

    if (projectScope === "current") {
      // Search only current project
      return this.searchCurrentProject(query);
    }

    // Search across all linked projects
    const availableProjects = this.linkedProjects.values();
    const resultsByProject: MultiProjectSearchResult[][] = [];

    for (const project of availableProjects) {
      // Skip unavailable projects
      if (project.status === ProjectStatus.UNAVAILABLE) {
        logger.warn("Skipping unavailable project", { name: project.name });
        continue;
      }

      try {
        const results = await this.searchProject(project, query);
        if (results.length > 0) {
          resultsByProject.push(results);
        }
      } catch (error) {
        logger.error("Failed to search project", {
          project: project.name,
          error,
        });
        // Continue with other projects
      }
    }

    // Aggregate and rank results
    const aggregated = this.aggregateResults(resultsByProject);

    logger.debug("Cross-project search completed", {
      query,
      totalResults: aggregated.length,
    });

    return aggregated;
  }

  /**
   * Search current project only
   */
  private async searchCurrentProject(query: string): Promise<MultiProjectSearchResult[]> {
    // Mock implementation for testing
    // In real implementation, would search the primary project
    logger.debug("Searching current project", { query });
    return [];
  }

  /**
   * Search a specific project
   */
  private async searchProject(
    project: LinkedProject,
    query: string,
  ): Promise<MultiProjectSearchResult[]> {
    // Mock implementation for testing
    // In real implementation, would use ChunkSearchService
    logger.debug("Searching project", { project: project.name, query });

    // Return mock results for testing
    return [
      {
        id: `${project.name}-result-1`,
        content: `Result from ${project.name} matching ${query}`,
        filePath: `/path/to/${project.name}/file.ts`,
        projectName: project.name,
        score: 0.85,
        finalScore: 0.85,
      },
    ];
  }

  /**
   * Aggregate results from multiple projects
   */
  aggregateResults(resultsByProject: MultiProjectSearchResult[][]): MultiProjectSearchResult[] {
    const allResults: MultiProjectSearchResult[] = [];

    // Flatten results
    for (const projectResults of resultsByProject) {
      allResults.push(...projectResults);
    }

    // Sort by score (descending)
    allResults.sort((a, b) => {
      const scoreA = a.finalScore ?? a.score;
      const scoreB = b.finalScore ?? b.score;
      return scoreB - scoreA;
    });

    // Deduplicate by content AND project (only remove exact duplicates from same project)
    const seen = new Set<string>();
    const deduplicated: MultiProjectSearchResult[] = [];

    for (const result of allResults) {
      // Use content + filePath as key to avoid removing results from different projects
      const key = `${result.content}:${result.filePath}`;
      if (!seen.has(key)) {
        seen.add(key);
        deduplicated.push(result);
      }
    }

    return deduplicated;
  }

  /**
   * Check if a project is available (exists and accessible)
   */
  async checkProjectAvailability(project: LinkedProject): Promise<void> {
    try {
      // Check if path exists
      if (!existsSync(project.path)) {
        project.status = ProjectStatus.UNAVAILABLE;
        logger.debug("Project path does not exist", { path: project.path });
        return;
      }

      // Check if path is accessible
      accessSync(project.path, constants.R_OK);

      // Project is available
      project.status = ProjectStatus.AVAILABLE;
      logger.debug("Project is available", { path: project.path });
    } catch (error) {
      // Permission denied or other error
      project.status = ProjectStatus.UNAVAILABLE;
      logger.debug("Project is not accessible", {
        path: project.path,
        error,
      });
    }
  }

  /**
   * Refresh status for all linked projects
   */
  async refreshProjectStatus(): Promise<StatusSummary> {
    const projects = Array.from(this.linkedProjects.values());

    logger.debug("Refreshing project status", { count: projects.length });

    // Check availability for each project
    await Promise.all(
      projects.map((project) => this.checkProjectAvailability(project)),
    );

    // Update workspace storage
    if (this.workspaceStorage) {
      projects.forEach((project) => {
        this.workspaceStorage!.updateProjectStatus(
          project.path,
          project.status,
        );
      });
    }

    // Calculate summary
    const summary: StatusSummary = {
      total: projects.length,
      available: 0,
      unavailable: 0,
      initializing: 0,
    };

    projects.forEach((project) => {
      if (project.status === ProjectStatus.AVAILABLE) {
        summary.available++;
      } else if (project.status === ProjectStatus.UNAVAILABLE) {
        summary.unavailable++;
      } else if (project.status === ProjectStatus.INITIALIZING) {
        summary.initializing++;
      }
    });

    logger.info("Project status refreshed", summary);

    return summary;
  }
}
