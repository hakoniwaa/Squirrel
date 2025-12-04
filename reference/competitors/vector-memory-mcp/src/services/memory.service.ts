import { randomUUID } from "crypto";
import type { Memory } from "../types/memory.js";
import { DELETED_TOMBSTONE, isSuperseded } from "../types/memory.js";
import type { MemoryRepository } from "../db/memory.repository.js";
import type { EmbeddingsService } from "./embeddings.service.js";

export class MemoryService {
  constructor(
    private repository: MemoryRepository,
    private embeddings: EmbeddingsService
  ) {}

  async store(
    content: string,
    metadata: Record<string, unknown> = {},
    embeddingText?: string
  ): Promise<Memory> {
    const id = randomUUID();
    const now = new Date();
    const textToEmbed = embeddingText ?? content;
    const embedding = await this.embeddings.embed(textToEmbed);

    const memory: Memory = {
      id,
      content,
      embedding,
      metadata,
      createdAt: now,
      updatedAt: now,
      supersededBy: null,
    };

    await this.repository.insert(memory);
    return memory;
  }

  async get(id: string): Promise<Memory | null> {
    return await this.repository.findById(id);
  }

  async delete(id: string): Promise<boolean> {
    return await this.repository.markDeleted(id);
  }

  async search(query: string, limit: number = 10): Promise<Memory[]> {
    const queryEmbedding = await this.embeddings.embed(query);
    const fetchLimit = limit * 3;

    const rows = await this.repository.findSimilar(queryEmbedding, fetchLimit);

    const results: Memory[] = [];
    const seenIds = new Set<string>();

    for (const row of rows) {
      let memory = await this.repository.findById(row.id);

      if (!memory) {
        continue;
      }

      if (isSuperseded(memory)) {
        memory = await this.followSupersessionChain(row.id);
        if (!memory) {
          continue;
        }
      }

      if (seenIds.has(memory.id)) {
        continue;
      }
      seenIds.add(memory.id);

      results.push(memory);
      if (results.length >= limit) {
        break;
      }
    }

    return results;
  }

  private async followSupersessionChain(memoryId: string): Promise<Memory | null> {
    const visited = new Set<string>();
    let currentId: string | null = memoryId;

    while (currentId && !visited.has(currentId)) {
      visited.add(currentId);
      const memory = await this.repository.findById(currentId);

      if (!memory) {
        return null;
      }

      if (memory.supersededBy === null) {
        return memory;
      }

      if (memory.supersededBy === DELETED_TOMBSTONE) {
        return null;
      }

      currentId = memory.supersededBy;
    }

    return null;
  }
}
