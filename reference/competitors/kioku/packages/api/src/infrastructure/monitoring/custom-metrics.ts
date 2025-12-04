/**
 * Custom Metrics - Prometheus metrics for Kioku monitoring
 *
 * Purpose: Define application-specific metrics for observability.
 * Layer: Infrastructure (monitoring)
 * Used by: All services, background jobs, MCP tools
 *
 * Metrics Categories:
 * - Counters: Monotonically increasing (errors, events, tool calls)
 * - Gauges: Point-in-time values (queue depth, active sessions, usage)
 * - Histograms: Distribution of values (latency, processing time)
 *
 * @module infrastructure/monitoring
 */

import { Counter, Gauge, Histogram, Registry } from "prom-client";
import { logger } from "../cli/logger";

// Create custom registry
export const customRegistry = new Registry();

/**
 * Counter: Total errors by type
 */
export const errorsTotal = new Counter({
  name: "kioku_errors_total",
  help: "Total number of errors by type",
  labelNames: ["error_type", "component"],
  registers: [customRegistry],
});

/**
 * Counter: File watcher events by type
 */
export const fileWatcherEventsTotal = new Counter({
  name: "kioku_file_watcher_events_total",
  help: "Total file watcher events by type",
  labelNames: ["event_type"], // add, change, unlink, rename
  registers: [customRegistry],
});

/**
 * Counter: MCP tool calls
 */
export const toolCallsTotal = new Counter({
  name: "kioku_tool_calls_total",
  help: "Total MCP tool calls by tool name",
  labelNames: ["tool_name"],
  registers: [customRegistry],
});

/**
 * Counter: AI API calls
 */
export const aiApiCallsTotal = new Counter({
  name: "kioku_ai_api_calls_total",
  help: "Total AI API calls by provider",
  labelNames: ["provider", "status"], // provider: anthropic/openai, status: success/error
  registers: [customRegistry],
});

/**
 * Counter: AI tokens used
 */
export const aiTokensUsedTotal = new Counter({
  name: "kioku_ai_tokens_used_total",
  help: "Total AI tokens used by provider and type",
  labelNames: ["provider", "token_type"], // token_type: input/output
  registers: [customRegistry],
});

/**
 * Gauge: Embedding queue depth
 */
export const embeddingQueueDepth = new Gauge({
  name: "kioku_embedding_queue_depth",
  help: "Number of pending embeddings in queue",
  registers: [customRegistry],
});

/**
 * Gauge: Active sessions
 */
export const activeSessions = new Gauge({
  name: "kioku_active_sessions",
  help: "Number of currently active sessions",
  registers: [customRegistry],
});

/**
 * Gauge: Context window usage percentage
 */
export const contextWindowUsagePercent = new Gauge({
  name: "kioku_context_window_usage_percent",
  help: "Context window usage as percentage (0-100)",
  registers: [customRegistry],
});

/**
 * Gauge: Database size in bytes
 */
export const databaseSizeBytes = new Gauge({
  name: "kioku_database_size_bytes",
  help: "Total database size in bytes",
  labelNames: ["database"], // sqlite, chroma
  registers: [customRegistry],
});

/**
 * Gauge: Total chunks stored
 */
export const chunksStored = new Gauge({
  name: "kioku_chunks_stored_total",
  help: "Total number of code chunks stored",
  registers: [customRegistry],
});

/**
 * Histogram: API latency in seconds
 */
export const apiLatencySeconds = new Histogram({
  name: "kioku_api_latency_seconds",
  help: "API request latency in seconds",
  labelNames: ["operation", "status"], // operation: search/embed/refine, status: success/error
  buckets: [0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10],
  registers: [customRegistry],
});

/**
 * Histogram: Chunking processing time in seconds
 */
export const chunkingProcessingSeconds = new Histogram({
  name: "kioku_chunking_processing_seconds",
  help: "Time to process file chunking in seconds",
  labelNames: ["file_type"], // ts, tsx, js, jsx
  buckets: [0.01, 0.05, 0.1, 0.25, 0.5, 1, 2, 5],
  registers: [customRegistry],
});

/**
 * Histogram: Git operation latency in seconds
 */
export const gitOperationSeconds = new Histogram({
  name: "kioku_git_operation_seconds",
  help: "Git operation latency in seconds",
  labelNames: ["operation"], // log, blame, diff
  buckets: [0.1, 0.25, 0.5, 1, 2, 5, 10],
  registers: [customRegistry],
});

/**
 * Histogram: Search result count distribution
 */
export const searchResultCount = new Histogram({
  name: "kioku_search_result_count",
  help: "Distribution of search result counts",
  labelNames: ["query_type"], // semantic, keyword, git
  buckets: [0, 1, 3, 5, 10, 20, 50],
  registers: [customRegistry],
});

/**
 * Initialize all metrics with default values
 */
export function initializeMetrics(): void {
  logger.info("Initializing custom metrics");

  // Set default gauge values
  embeddingQueueDepth.set(0);
  activeSessions.set(0);
  contextWindowUsagePercent.set(0);
  chunksStored.set(0);

  logger.debug("Custom metrics initialized", {
    metricsCount: customRegistry.getMetricsAsArray().length,
  });
}

/**
 * Reset all metrics (useful for testing)
 */
export function resetMetrics(): void {
  customRegistry.resetMetrics();
  logger.debug("All metrics reset");
}

/**
 * Get metrics in Prometheus text format
 */
export async function getMetricsText(): Promise<string> {
  return customRegistry.metrics();
}
