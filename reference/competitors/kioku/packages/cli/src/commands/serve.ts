/**
 * Serve Command
 *
 * Start the MCP server to serve project context to Claude Desktop.
 */

import { startMCPServer } from '@kioku/api';
import { logger } from '../logger';

export async function serveCommand(): Promise<void> {
  const projectPath = process.cwd();

  try {
    logger.info('Starting MCP server', { projectPath });

    await startMCPServer(projectPath);

    // Server runs indefinitely until killed
    // Keep process alive
    await new Promise(() => {
      // This promise never resolves, keeping the server running
    });
  } catch (error) {

    console.error('❌ Failed to start MCP server');

    if (error instanceof Error) {

      console.error('Error:', error.message);
      logger.error('MCP server startup failed', {
        error: error.message,
        stack: error.stack,
      });
    }

    process.exit(1);
  }
}
