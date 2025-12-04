/**
 * Service Manager
 *
 * Manages all background services with graceful startup and shutdown.
 */

import type { SQLiteAdapter } from 'infrastructure/storage/sqlite-adapter';
import type { SessionManager } from 'application/use-cases/SessionManager';
import { ContextScorer } from './ContextScorer';
import { ContextPruner } from './ContextPruner';
import { SessionTimeoutChecker } from './SessionTimeoutChecker';
import { logger } from '../cli/logger';

export interface BackgroundService {
  start(): void;
  stop(): void;
}

export class ServiceManager {
  private services: Map<string, BackgroundService>;
  private sqliteAdapter: SQLiteAdapter;
  private sessionManager: SessionManager | undefined;
  private running = false;

  constructor(sqliteAdapter: SQLiteAdapter, sessionManager?: SessionManager) {
    this.sqliteAdapter = sqliteAdapter;
    this.sessionManager = sessionManager;
    this.services = new Map();
  }

  /**
   * Initialize all background services
   */
  private initializeServices(): void {
    // Context Scorer - runs every 5 minutes
    const scorer = new ContextScorer(this.sqliteAdapter, 300000);
    this.services.set('scorer', scorer);

    // Context Pruner - runs every 10 minutes
    const pruner = new ContextPruner(this.sqliteAdapter, 600000);
    this.services.set('pruner', pruner);

    // Session Timeout Checker - runs every 5 minutes (if SessionManager provided)
    if (this.sessionManager) {
      const timeoutChecker = new SessionTimeoutChecker(this.sessionManager, 300000);
      this.services.set('sessionTimeout', timeoutChecker);
    }

    logger.debug('Background services initialized', {
      services: Array.from(this.services.keys()),
    });
  }

  /**
   * Start all background services
   */
  start(): void {
    if (this.running) {
      logger.warn('Service manager already running');
      return;
    }

    logger.info('Starting background services');

    this.initializeServices();

    // Start all services
    for (const [name, service] of this.services) {
      try {
        service.start();
        logger.debug(`Started service: ${name}`);
      } catch (error) {
        logger.error(`Failed to start service: ${name}`, { error });
      }
    }

    this.running = true;
    this.setupSignalHandlers();

    logger.info('All background services started', {
      count: this.services.size,
    });
  }

  /**
   * Stop all background services gracefully
   */
  stop(): void {
    if (!this.running) {
      return;
    }

    logger.info('Stopping background services');

    // Stop all services in reverse order
    const serviceEntries = Array.from(this.services.entries()).reverse();

    for (const [name, service] of serviceEntries) {
      try {
        service.stop();
        logger.debug(`Stopped service: ${name}`);
      } catch (error) {
        logger.error(`Failed to stop service: ${name}`, { error });
      }
    }

    this.services.clear();
    this.running = false;

    logger.info('All background services stopped');
  }

  /**
   * Setup signal handlers for graceful shutdown
   */
  private setupSignalHandlers(): void {
    const signals: NodeJS.Signals[] = ['SIGINT', 'SIGTERM'];

    for (const signal of signals) {
      process.on(signal, () => {
        logger.info(`Received ${signal}, shutting down gracefully`);
        this.stop();
        process.exit(0);
      });
    }
  }

  /**
   * Check if service manager is running
   */
  isRunning(): boolean {
    return this.running;
  }

  /**
   * Get list of active services
   */
  getServices(): string[] {
    return Array.from(this.services.keys());
  }
}
