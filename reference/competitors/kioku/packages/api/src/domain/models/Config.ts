export interface Config {
  storage: {
    contextDir: string;
    dbPath: string;
    chromaPath: string;
  };
  embeddings: {
    provider: "openai";
    model: string;
    apiKey: string;
    batchSize: number;
  };
  services: {
    scorerInterval: number;
    prunerThreshold: number;
    sessionTimeout: number;
    embeddingsInterval: number;
  };
  contextWindow: {
    maxTokens: number;
    pruneTarget: number;
  };
  logging: {
    level: "debug" | "info" | "warn" | "error";
    file?: string;
  };
  // v2.0 additions
  chunking?: {
    enabled: boolean;
    minLines: number;
    maxLines: number;
    contextLines: number;
    maxNestingDepth: number;
    fallbackToFile: boolean;
  };
  file_watcher?: {
    enabled: boolean;
    debounceMs: number;
    pollIntervalMs: number;
    ignored: string[];
  };
  git?: {
    enabled: boolean;
    maxCommitsPerLog: number;
    diffMaxFiles: number;
  };
  ai_discovery?: {
    enabled: boolean;
    provider: "anthropic";
    model: string;
    confidenceThreshold: number;
    maxMessagesPerSession: number;
    costLimitPerDay: number;
  };
  ranking?: {
    recencyWeight: number;
    recencyWeekWeight: number;
    moduleWeight: number;
    frequencyDivisor: number;
    frequencyCap: number;
  };
  multi_project?: {
    enabled: boolean;
    maxLinkedProjects: number;
    searchDepth: number;
  };
  monitoring?: {
    metricsEnabled: boolean;
    metricsPort: number;
    healthCheckEnabled: boolean;
    cacheMetricsTTL: number;
  };
  dashboard?: {
    enabled: boolean;
    port: number;
    autoOpenBrowser: boolean;
    pollInterval: number;
  };
}
