/**
 * MetricsRegistry - Prometheus metrics setup
 *
 * Purpose: Initialize and export Prometheus metrics for monitoring.
 * Used by: Metrics server, instrumentation throughout codebase
 *
 * @module infrastructure/monitoring
 */

import { Registry, collectDefaultMetrics, Counter, Gauge, Histogram } from 'prom-client';
import { logger } from '../cli/logger';

// Create registry
export const registry = new Registry();

// Collect default metrics (CPU, memory, etc.)
collectDefaultMetrics({ register: registry });

// Custom metrics

/**
 * Counter: Total file watcher events
 */
export const fileWatcherEventsTotal = new Counter({
  name: 'kioku_file_watcher_events_total',
  help: 'Total number of file watcher events processed',
  labelNames: ['event_type'],
  registers: [registry],
});

/**
 * Counter: Total errors
 */
export const errorsTotal = new Counter({
  name: 'kioku_errors_total',
  help: 'Total number of errors',
  labelNames: ['type', 'component'],
  registers: [registry],
});

/**
 * Gauge: Active sessions
 */
export const activeSessions = new Gauge({
  name: 'kioku_active_sessions',
  help: 'Number of currently active sessions',
  registers: [registry],
});

/**
 * Gauge: Context window usage percentage
 */
export const contextWindowUsage = new Gauge({
  name: 'kioku_context_window_usage_percent',
  help: 'Current context window usage as percentage (0-100)',
  registers: [registry],
});

/**
 * Gauge: Embedding queue depth
 */
export const embeddingQueueDepth = new Gauge({
  name: 'kioku_embedding_queue_depth',
  help: 'Number of items waiting for embedding generation',
  registers: [registry],
});

/**
 * Histogram: API latency in seconds
 */
export const apiLatency = new Histogram({
  name: 'kioku_api_latency_seconds',
  help: 'API operation latency in seconds',
  labelNames: ['operation', 'provider'],
  buckets: [0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10],
  registers: [registry],
});

/**
 * Counter: Chunks created
 */
export const chunksCreated = new Counter({
  name: 'kioku_chunks_created_total',
  help: 'Total number of code chunks created',
  labelNames: ['type'],
  registers: [registry],
});

/**
 * Counter: Git operations
 */
export const gitOperations = new Counter({
  name: 'kioku_git_operations_total',
  help: 'Total number of git operations',
  labelNames: ['operation'],
  registers: [registry],
});

logger.info('Prometheus metrics registry initialized');
