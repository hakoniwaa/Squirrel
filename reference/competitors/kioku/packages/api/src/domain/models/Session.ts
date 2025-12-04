export interface Session {
  id: string;
  projectId: string;
  startedAt: Date;
  endedAt?: Date;
  status: 'active' | 'completed' | 'archived';
  filesAccessed: FileAccess[];
  topics: string[];
  metadata: {
    duration?: number;
    toolCallsCount: number;
    discoveryCount: number;
  };
}

export interface FileAccess {
  path: string;
  accessCount: number;
  firstAccessedAt: Date;
  lastAccessedAt: Date;
}
