/**
 * API Response Types
 *
 * TypeScript interfaces matching Kioku backend API responses
 */

export interface ProjectOverview {
  name: string;
  type: string;
  techStack: string[];
  moduleCount: number;
  fileCount: number;
  databaseSize: string;
  activeSession: boolean;
  lastSessionTime?: string;
}

export interface Session {
  id: string;
  startTime: string;
  endTime?: string;
  duration: number; // in minutes
  filesCount: number;
  discoveriesCount: number;
}

export interface SessionDetails extends Session {
  files?: string[];
  topics?: string[];
  discoveries?: Discovery[];
}

export interface Discovery {
  id: string;
  type: "pattern" | "decision" | "constraint" | "architecture";
  content: string;
  confidence: number;
  extractedAt: string;
}

export interface ModuleNode {
  id: string;
  name: string;
  path: string;
  fileCount: number;
  lastAccessed?: string;
  activity: "active" | "recent" | "stale";
}

export interface ModuleEdge {
  source: string;
  target: string;
  weight: number; // Number of imports
}

export interface ModuleGraph {
  nodes: ModuleNode[];
  edges: ModuleEdge[];
}

export interface EmbeddingsStats {
  totalCount: number;
  lastGenerated: string;
  queueSize: number;
  errorCount: number;
  diskUsage: string;
  recentErrors?: EmbeddingError[];
}

export interface EmbeddingError {
  timestamp: string;
  message: string;
  filePath?: string;
}

export interface ContextWindowUsage {
  current: number;
  max: number;
  percentage: number;
  status: "healthy" | "warning" | "critical";
}

export interface ServiceStatus {
  name: string;
  status: "running" | "stopped" | "error";
  details?: string;
}

export interface HealthStatus {
  services: ServiceStatus[];
  uptime: number; // in seconds
  timestamp: string;
}

export interface LinkedProjectInfo {
  name: string;
  path: string;
  status: "available" | "unavailable";
  lastAccessed?: string;
  moduleCount?: number;
  fileCount?: number;
}
