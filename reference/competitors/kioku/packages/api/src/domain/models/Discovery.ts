export interface Discovery {
  id: string;
  sessionId: string;
  type: 'pattern' | 'rule' | 'decision' | 'issue';
  content: string;
  module?: string;
  context: {
    extractedFrom: string;
    confidence: number;
  };
  embedding?: {
    id: string;
    model: string;
    dimensions: number;
  };
  createdAt: Date;
}
