// @kioku/api - MCP server and core business logic
// This is the main entry point for the API package

// Export domain models
export * from './domain/models';

// Export application services
export * from './application/services';

// Export use cases (for CLI)
export { InitializeProject } from './application/use-cases/InitializeProject';
export { PruneContext } from './application/use-cases/PruneContext';

// Export infrastructure adapters (for CLI)
export { SQLiteAdapter } from './infrastructure/storage/sqlite-adapter';
export { YAMLHandler } from './infrastructure/storage/yaml-handler';

// Export MCP server
export { startMCPServer } from './infrastructure/server';

// Export monitoring endpoints (for dashboard command)
export * from './infrastructure/monitoring/api-endpoints';
