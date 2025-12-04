/**
 * Session Timeout Checker Background Service
 *
 * Periodically checks for inactive sessions and ends them after 30 minutes of inactivity.
 */

import { SessionManager } from 'application/use-cases/SessionManager';
import { logger } from '../cli/logger';

export class SessionTimeoutChecker {
  private sessionManager: SessionManager;
  private intervalId: Timer | null = null;
  private readonly intervalMs: number;

  constructor(sessionManager: SessionManager, intervalMs = 300000) {
    // Default: 5 minutes (300000ms)
    this.sessionManager = sessionManager;
    this.intervalMs = intervalMs;
  }

  /**
   * Start the background timeout checker
   */
  start(): void {
    if (this.intervalId) {
      logger.warn('Session timeout checker already running');
      return;
    }

    logger.info('Starting session timeout checker', {
      intervalMs: this.intervalMs,
      intervalMinutes: this.intervalMs / 60000,
      inactivityTimeoutMinutes: SessionManager.getInactivityTimeout() / 60000,
    });

    // Run immediately on start
    this.checkTimeout().catch((error) => {
      logger.error('Failed to check session timeout on startup', { error });
    });

    // Then run periodically
    this.intervalId = setInterval(() => {
      this.checkTimeout().catch((error) => {
        logger.error('Failed to check session timeout', { error });
      });
    }, this.intervalMs);
  }

  /**
   * Stop the background timeout checker
   */
  stop(): void {
    if (this.intervalId) {
      clearInterval(this.intervalId);
      this.intervalId = null;
      logger.info('Session timeout checker stopped');
    }
  }

  /**
   * Check if current session has exceeded inactivity timeout
   */
  private async checkTimeout(): Promise<void> {
    logger.debug('Checking session inactivity timeout');

    try {
      const wasEnded = await this.sessionManager.checkInactivity();

      if (wasEnded) {
        logger.info('Session ended due to inactivity timeout');
      } else {
        logger.debug('Session still active or no active session');
      }
    } catch (error) {
      logger.error('Error checking session timeout', { error });
      throw error;
    }
  }
}
