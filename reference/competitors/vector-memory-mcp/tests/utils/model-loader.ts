/**
 * Model loader utility for tests.
 *
 * Provides a way to pre-load the embedding model before tests run,
 * and skip tests gracefully if the model is unavailable.
 */

import { EmbeddingsService } from "../../src/services/embeddings.service.js";

const MODEL_NAME = "Xenova/all-MiniLM-L6-v2";
const MODEL_DIMENSION = 384;
const WARMUP_TIMEOUT_MS = 120_000; // 2 minutes for initial download

export interface ModelState {
  available: boolean;
  error?: Error;
  service?: EmbeddingsService;
}

let modelState: ModelState = { available: false };
let warmupPromise: Promise<ModelState> | null = null;

/**
 * Warms up the embedding model by loading it and running a test embedding.
 * Safe to call multiple times - will only load once.
 */
export async function warmupModel(): Promise<ModelState> {
  if (warmupPromise) {
    return warmupPromise;
  }

  warmupPromise = (async () => {
    try {
      const service = new EmbeddingsService(MODEL_NAME, MODEL_DIMENSION);

      // Run a test embedding to force model download/load
      const timeoutPromise = new Promise<never>((_, reject) => {
        setTimeout(() => reject(new Error(`Model warmup timed out after ${WARMUP_TIMEOUT_MS}ms`)), WARMUP_TIMEOUT_MS);
      });

      await Promise.race([
        service.embed("warmup test"),
        timeoutPromise,
      ]);

      modelState = { available: true, service };
      return modelState;
    } catch (error) {
      modelState = {
        available: false,
        error: error instanceof Error ? error : new Error(String(error))
      };
      return modelState;
    }
  })();

  return warmupPromise;
}

/**
 * Gets the current model state. Call warmupModel() first to initialize.
 */
export function getModelState(): ModelState {
  return modelState;
}

/**
 * Returns true if the model is available for testing.
 * Must call warmupModel() before this will return true.
 */
export function isModelAvailable(): boolean {
  return modelState.available;
}

/**
 * Creates a fresh EmbeddingsService instance for testing.
 * Throws if model is not available.
 */
export function createEmbeddingsService(): EmbeddingsService {
  if (!modelState.available) {
    throw new Error(
      "Model not available. Call warmupModel() first or check isModelAvailable(). " +
      (modelState.error ? `Error: ${modelState.error.message}` : "")
    );
  }
  return new EmbeddingsService(MODEL_NAME, MODEL_DIMENSION);
}

/**
 * Helper to create a describe block that skips if model is unavailable.
 * Usage: describeWithModel("EmbeddingsService", () => { ... })
 */
export function describeWithModel(name: string, fn: () => void): void {
  if (modelState.available) {
    describe(name, fn);
  } else {
    describe.skip(name, fn);
  }
}

/**
 * Helper to create a test that skips if model is unavailable.
 * Usage: testWithModel("generates embedding", async () => { ... })
 */
export function testWithModel(name: string, fn: () => void | Promise<void>): void {
  if (modelState.available) {
    test(name, fn);
  } else {
    test.skip(name, fn);
  }
}

// Re-export test and describe for convenience
import { test, describe } from "bun:test";
export { test, describe };
