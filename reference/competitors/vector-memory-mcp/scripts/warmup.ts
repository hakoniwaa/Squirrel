#!/usr/bin/env bun

/**
 * Warmup script to pre-download ML models and verify dependencies
 * This runs during installation to ensure everything is ready to use
 */

import { config } from "../src/config/index.js";
import { EmbeddingsService } from "../src/services/embeddings.service.js";

async function warmup(): Promise<void> {
  console.log("🔥 Warming up vector-memory-mcp...");
  console.log();

  try {
    // Check native dependencies
    console.log("✓ Checking native dependencies...");
    try {
      await import("onnxruntime-node");
      console.log("  ✓ onnxruntime-node loaded");
    } catch (e) {
      console.error("  ✗ onnxruntime-node failed:", (e as Error).message);
      process.exit(1);
    }

    try {
      await import("sharp");
      console.log("  ✓ sharp loaded");
    } catch (e) {
      console.error("  ✗ sharp failed:", (e as Error).message);
      process.exit(1);
    }

    console.log();

    // Initialize embeddings service to download model
    console.log("📥 Downloading ML model (this may take a minute)...");
    console.log(`   Model: ${config.embeddingModel}`);
    console.log(`   Cache: ~/.cache/huggingface/`);
    console.log();

    const embeddings = new EmbeddingsService(
      config.embeddingModel,
      config.embeddingDimension
    );

    // Trigger model download by generating a test embedding
    const startTime = Date.now();
    await embeddings.embed("warmup test");
    const duration = ((Date.now() - startTime) / 1000).toFixed(2);

    console.log();
    console.log(`✅ Warmup complete! (${duration}s)`);
    console.log();
    console.log("Ready to use! Configure Claude Code and restart to get started.");
    console.log("See: https://github.com/AerionDyseti/vector-memory-mcp#configure-claude-code");
    console.log();
  } catch (error) {
    console.error();
    console.error("❌ Warmup failed:", error);
    console.error();
    console.error("This is not a critical error - the server will download models on first run.");
    console.error("You can try running 'vector-memory-mcp warmup' manually later.");
    process.exit(0); // Exit successfully to not block installation
  }
}

// Only run if this is the main module
if (import.meta.url === `file://${process.argv[1]}`) {
  warmup();
}

export { warmup };
