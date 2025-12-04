export interface ProjectContext {
  version: string;
  project: {
    name: string;
    type: 'web-app' | 'api' | 'cli' | 'library' | 'fullstack';
    path: string;
  };
  tech: {
    stack: string[];
    runtime: string;
    packageManager: 'npm' | 'yarn' | 'pnpm' | 'bun';
  };
  architecture: {
    pattern: 'feature-based' | 'layered' | 'modular' | 'monorepo' | 'unknown';
    description: string;
  };
  modules: Record<string, ModuleContext>;
  metadata: {
    createdAt: Date;
    updatedAt: Date;
    lastScanAt: Date;
  };
}

export interface ModuleContext {
  name: string;
  description: string;
  keyFiles: KeyFile[];
  patterns: string[];
  businessRules: string[];
  commonIssues: Issue[];
  dependencies: string[];
}

export interface KeyFile {
  path: string;
  role: 'entry' | 'config' | 'core' | 'test';
  description?: string;
}

export interface Issue {
  description: string;
  solution: string;
  sessionId: string;
  discoveredAt: Date;
}
