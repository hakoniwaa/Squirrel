export interface ContextItem {
  id: string;
  type: 'file' | 'module' | 'discovery' | 'session';
  content: string;
  metadata: {
    source: string;
    module?: string;
    sessionId?: string;
  };
  scoring: {
    score: number;
    recencyFactor: number;
    accessFactor: number;
    lastAccessedAt: Date;
    accessCount: number;
  };
  tokens: number;
  status: 'active' | 'archived';
}
