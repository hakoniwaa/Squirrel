/**
 * OpenAI Client
 *
 * Client for generating embeddings using OpenAI's API.
 */

import OpenAI from 'openai';
import { logger } from '../cli/logger';

export class OpenAIClient {
  private openai: OpenAI;
  private model = 'text-embedding-3-small';
  private batchSize = 100;
  private maxRetries = 2;

  constructor() {
    const apiKey = process.env.OPENAI_API_KEY;

    if (!apiKey) {
      throw new Error('OPENAI_API_KEY environment variable is required');
    }

    this.openai = new OpenAI({ apiKey });
    logger.debug('OpenAI client initialized', { model: this.model });
  }

  /**
   * Generate embedding for a single text
   */
  async generateEmbedding(text: string): Promise<number[]> {
    if (!text || text.trim().length === 0) {
      throw new Error('Text cannot be empty');
    }

    const result = await this.generateEmbeddings([text]);
    return result[0] ?? [];
  }

  /**
   * Generate embeddings for multiple texts (batched)
   */
  async generateEmbeddings(texts: string[]): Promise<number[][]> {
    if (texts.length === 0) {
      return [];
    }

    const results: number[][] = [];

    // Process in batches of 100
    for (let i = 0; i < texts.length; i += this.batchSize) {
      const batch = texts.slice(i, i + this.batchSize);
      const batchResults = await this.generateEmbeddingsBatch(batch);
      results.push(...batchResults);
    }

    logger.info('Generated embeddings', {
      count: texts.length,
      batches: Math.ceil(texts.length / this.batchSize),
    });

    return results;
  }

  /**
   * Generate embeddings for a single batch with retry logic
   */
  private async generateEmbeddingsBatch(texts: string[]): Promise<number[][]> {
    let lastError: Error | null = null;

    for (let attempt = 0; attempt <= this.maxRetries; attempt++) {
      try {
        const response = await this.openai.embeddings.create({
          model: this.model,
          input: texts,
        });

        return response.data.map(item => item.embedding);
      } catch (error) {
        lastError = error as Error;

        // Check if it's a rate limit error
        if (error instanceof Error && error.message.includes('Rate limit')) {
          const waitTime = Math.pow(2, attempt) * 1000; // Exponential backoff
          logger.warn('Rate limit hit, retrying', {
            attempt: attempt + 1,
            waitMs: waitTime,
          });

          if (attempt < this.maxRetries) {
            await this.sleep(waitTime);
            continue;
          }
        }

        // For other errors or max retries reached, throw immediately
        logger.error('Failed to generate embeddings', {
          error: error instanceof Error ? error.message : 'Unknown error',
          attempt: attempt + 1,
        });
        throw error;
      }
    }

    throw lastError ?? new Error('Failed to generate embeddings');
  }

  private sleep(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
  }
}
