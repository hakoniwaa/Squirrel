import * as lancedb from "@lancedb/lancedb";
import { TABLE_NAME, memorySchema } from "./schema.js";
import {
  type Memory,
  type VectorRow,
  DELETED_TOMBSTONE,
} from "../types/memory.js";

export class MemoryRepository {
  constructor(private db: lancedb.Connection) {}

  private async getTable() {
    const names = await this.db.tableNames();
    if (names.includes(TABLE_NAME)) {
      return await this.db.openTable(TABLE_NAME);
    }
    // Create with empty data to initialize schema
    return await this.db.createTable(TABLE_NAME, [], { schema: memorySchema });
  }

  async insert(memory: Memory): Promise<void> {
    const table = await this.getTable();
    await table.add([
      {
        id: memory.id,
        vector: memory.embedding,
        content: memory.content,
        metadata: JSON.stringify(memory.metadata),
        created_at: memory.createdAt.getTime(),
        updated_at: memory.updatedAt.getTime(),
        superseded_by: memory.supersededBy,
      },
    ]);
  }

  async findById(id: string): Promise<Memory | null> {
    const table = await this.getTable();
    const results = await table.query().where(`id = '${id}'`).limit(1).toArray();

    if (results.length === 0) {
      return null;
    }

    const row = results[0];
    
    // Handle Arrow Vector type conversion
    // LanceDB returns an Arrow Vector object which is iterable but not an array
    const vectorData = row.vector as any;
    const embedding = Array.isArray(vectorData) 
      ? vectorData 
      : Array.from(vectorData) as number[];

    return {
      id: row.id as string,
      content: row.content as string,
      embedding,
      metadata: JSON.parse(row.metadata as string),
      createdAt: new Date(row.created_at as number),
      updatedAt: new Date(row.updated_at as number),
      supersededBy: row.superseded_by as string | null,
    };
  }

  async markDeleted(id: string): Promise<boolean> {
    const table = await this.getTable();
    
    // Verify existence first to match previous behavior (return false if not found)
    const existing = await table.query().where(`id = '${id}'`).limit(1).toArray();
    if (existing.length === 0) {
      return false;
    }

    const now = Date.now();
    await table.update({
      where: `id = '${id}'`,
      values: {
        superseded_by: DELETED_TOMBSTONE,
        updated_at: now,
      },
    });

    return true;
  }

  async findSimilar(embedding: number[], limit: number): Promise<VectorRow[]> {
    const table = await this.getTable();
    const results = await table.vectorSearch(embedding).limit(limit).toArray();

    return results.map((r) => ({
      id: r.id as string,
      distance: r._distance as number,
    }));
  }
}
