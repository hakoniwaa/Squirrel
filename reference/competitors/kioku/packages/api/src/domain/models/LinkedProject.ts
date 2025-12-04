/**
 * LinkedProject - Represents a linked project in multi-project workspace
 *
 * Purpose: Enable cross-project search and reference tracking.
 * Used by: Multi-Project feature (User Story 6)
 *
 * @module domain/models
 */

export enum LinkType {
  WORKSPACE = 'workspace',         // Part of same workspace (monorepo)
  DEPENDENCY = 'dependency',       // External dependency
}

export enum ProjectStatus {
  AVAILABLE = 'available',
  UNAVAILABLE = 'unavailable',     // Moved, deleted, permission denied
  INITIALIZING = 'initializing',   // Kioku init in progress
}

export interface LinkedProject {
  name: string;                    // User-friendly name
  path: string;                    // Absolute path to project root
  linkType: LinkType;
  status: ProjectStatus;
  lastAccessed: Date;

  // Metadata
  techStack?: string[];            // ['TypeScript', 'React', 'Node.js']
  moduleCount?: number;
  fileCount?: number;
}

export interface CrossReference {
  id: string;                      // UUID v4
  sourceProject: string;           // Source project name
  sourceFile: string;              // Source file path
  targetProject: string;           // Target project name
  targetFile: string;              // Target file path
  referenceType: 'import' | 'api_call' | 'type_usage';
  confidence: number;              // 0-1

  createdAt: Date;
}
