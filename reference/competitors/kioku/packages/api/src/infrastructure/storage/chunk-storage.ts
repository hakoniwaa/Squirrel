/**
 * ChunkStorage - SQLite adapter for code chunk persistence
 *
 * Purpose: Implement IChunkStorage interface using bun:sqlite
 * Used by: ChunkingService, SearchService
 *
 * @module infrastructure/storage
 */

import { Database } from "bun:sqlite";
import type { IChunkStorage } from "application/ports/IChunkStorage";
import type { CodeChunk } from "domain/models/CodeChunk";
import { logger } from "infrastructure/cli/logger";

interface ChunkRow {
  id: string;
  file_path: string;
  type: string;
  name: string;
  start_line: number;
  end_line: number;
  content_start_line: number;
  content_end_line: number;
  code: string;
  content_hash: string;
  parent_chunk_id: string | null;
  nesting_level: number;
  scope_path: string;
  metadata: string;
  embedding_id: string | null;
  created_at: string;
  updated_at: string;
}

export class ChunkStorage implements IChunkStorage {
  private db: Database;

  constructor(dbPath: string) {
    this.db = new Database(dbPath);
  }

  async saveChunk(chunk: CodeChunk): Promise<void> {
    try {
      this.db
        .prepare(
          `
        INSERT INTO chunks (
          id, file_path, type, name, start_line, end_line,
          content_start_line, content_end_line, code, content_hash,
          parent_chunk_id, nesting_level, scope_path, metadata, embedding_id,
          created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
      `,
        )
        .run(
          chunk.id,
          chunk.filePath,
          chunk.type,
          chunk.name,
          chunk.startLine,
          chunk.endLine,
          chunk.contentStartLine,
          chunk.contentEndLine,
          chunk.code,
          chunk.contentHash,
          chunk.parentChunkId || null,
          chunk.nestingLevel,
          JSON.stringify(chunk.scopePath),
          JSON.stringify(chunk.metadata),
          chunk.embeddingId || null,
          chunk.createdAt.toISOString(),
          chunk.updatedAt.toISOString(),
        );

      logger.debug("Chunk saved", { id: chunk.id, filePath: chunk.filePath });
    } catch (error) {
      logger.error("Failed to save chunk", {
        error: error instanceof Error ? error.message : String(error),
        chunkId: chunk.id,
      });
      throw error;
    }
  }

  async saveChunks(chunks: CodeChunk[]): Promise<void> {
    const insert = this.db.prepare(`
      INSERT INTO chunks (
        id, file_path, type, name, start_line, end_line,
        content_start_line, content_end_line, code, content_hash,
        parent_chunk_id, nesting_level, scope_path, metadata, embedding_id,
        created_at, updated_at
      ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    `);

    const transaction = this.db.transaction((chunks: CodeChunk[]) => {
      for (const chunk of chunks) {
        insert.run(
          chunk.id,
          chunk.filePath,
          chunk.type,
          chunk.name,
          chunk.startLine,
          chunk.endLine,
          chunk.contentStartLine,
          chunk.contentEndLine,
          chunk.code,
          chunk.contentHash,
          chunk.parentChunkId || null,
          chunk.nestingLevel,
          JSON.stringify(chunk.scopePath),
          JSON.stringify(chunk.metadata),
          chunk.embeddingId || null,
          chunk.createdAt.toISOString(),
          chunk.updatedAt.toISOString(),
        );
      }
    });

    try {
      transaction(chunks);
      logger.debug("Chunks saved (batch)", { count: chunks.length });
    } catch (error) {
      logger.error("Failed to save chunks", {
        error: error instanceof Error ? error.message : String(error),
        count: chunks.length,
      });
      throw error;
    }
  }

  async getChunkById(id: string): Promise<CodeChunk | null> {
    const row = this.db.prepare("SELECT * FROM chunks WHERE id = ?").get(id) as
      | ChunkRow
      | undefined;
    return row ? this.rowToChunk(row) : null;
  }

  async getChunksByFile(filePath: string): Promise<CodeChunk[]> {
    const rows = this.db
      .prepare("SELECT * FROM chunks WHERE file_path = ?")
      .all(filePath) as ChunkRow[];
    return rows.map((row) => this.rowToChunk(row));
  }

  // Alias for interface compatibility
  async getChunksByFilePath(filePath: string): Promise<CodeChunk[]> {
    return this.getChunksByFile(filePath);
  }

  async getAllChunks(): Promise<CodeChunk[]> {
    const rows = this.db.prepare("SELECT * FROM chunks").all() as ChunkRow[];
    return rows.map((row) => this.rowToChunk(row));
  }

  async deleteChunk(chunkId: string): Promise<void> {
    this.db.prepare("DELETE FROM chunks WHERE id = ?").run(chunkId);
    logger.debug("Chunk deleted", { chunkId });
  }

  async getChunksByType(type: string): Promise<CodeChunk[]> {
    const rows = this.db
      .prepare("SELECT * FROM chunks WHERE type = ?")
      .all(type) as ChunkRow[];
    return rows.map((row) => this.rowToChunk(row));
  }

  async deleteChunksByFilePath(filePath: string): Promise<void> {
    this.db.prepare("DELETE FROM chunks WHERE file_path = ?").run(filePath);
    logger.debug("Chunks deleted", { filePath });
  }

  async updateChunk(chunk: CodeChunk): Promise<void> {
    this.db
      .prepare(
        `
      UPDATE chunks SET
        file_path = ?, type = ?, name = ?, start_line = ?, end_line = ?,
        content_start_line = ?, content_end_line = ?, code = ?, content_hash = ?,
        parent_chunk_id = ?, nesting_level = ?, scope_path = ?, metadata = ?,
        embedding_id = ?, updated_at = ?
      WHERE id = ?
    `,
      )
      .run(
        chunk.filePath,
        chunk.type,
        chunk.name,
        chunk.startLine,
        chunk.endLine,
        chunk.contentStartLine,
        chunk.contentEndLine,
        chunk.code,
        chunk.contentHash,
        chunk.parentChunkId || null,
        chunk.nestingLevel,
        JSON.stringify(chunk.scopePath),
        JSON.stringify(chunk.metadata),
        chunk.embeddingId || null,
        chunk.updatedAt.toISOString(),
        chunk.id,
      );

    logger.debug("Chunk updated", { chunkId: chunk.id });
  }

  async getChunksNeedingEmbeddings(limit: number): Promise<CodeChunk[]> {
    const rows = this.db
      .prepare("SELECT * FROM chunks WHERE embedding_id IS NULL LIMIT ?")
      .all(limit) as ChunkRow[];
    return rows.map((row) => this.rowToChunk(row));
  }

  async getChunkCount(): Promise<number> {
    const result = this.db
      .prepare("SELECT COUNT(*) as count FROM chunks")
      .get() as {
      count: number;
    };
    return result.count;
  }

  async getChunkStats(): Promise<{
    totalChunks: number;
    chunksByType: Record<string, number>;
    avgChunksPerFile: number;
    chunksWithEmbeddings: number;
  }> {
    const total = await this.getChunkCount();

    const typeRows = this.db
      .prepare("SELECT type, COUNT(*) as count FROM chunks GROUP BY type")
      .all() as { type: string; count: number }[];
    const chunksByType: Record<string, number> = {};
    for (const row of typeRows) {
      chunksByType[row.type] = row.count;
    }

    const avgResult = this.db
      .prepare("SELECT COUNT(DISTINCT file_path) as fileCount FROM chunks")
      .get() as { fileCount: number };
    const avgChunksPerFile =
      avgResult.fileCount > 0 ? total / avgResult.fileCount : 0;

    const embeddedResult = this.db
      .prepare(
        "SELECT COUNT(*) as count FROM chunks WHERE embedding_id IS NOT NULL",
      )
      .get() as { count: number };
    const chunksWithEmbeddings = embeddedResult.count;

    return {
      totalChunks: total,
      chunksByType,
      avgChunksPerFile,
      chunksWithEmbeddings,
    };
  }

  private rowToChunk(row: ChunkRow): CodeChunk {
    const metadata = JSON.parse(row.metadata);

    const chunk: CodeChunk = {
      id: row.id,
      filePath: row.file_path,
      type: row.type as CodeChunk["type"],
      name: row.name,
      startLine: row.start_line,
      endLine: row.end_line,
      contentStartLine: row.content_start_line,
      contentEndLine: row.content_end_line,
      code: row.code,
      contentHash: row.content_hash,
      nestingLevel: row.nesting_level,
      scopePath: JSON.parse(row.scope_path),
      metadata: {
        isExported: metadata.isExported,
        isAsync: metadata.isAsync,
        ...(metadata.signature && { signature: metadata.signature }),
        ...(metadata.jsDoc && { jsDoc: metadata.jsDoc }),
        ...(metadata.returnType && { returnType: metadata.returnType }),
        ...(metadata.complexity && { complexity: metadata.complexity }),
        parameters: metadata.parameters || [],
      },
      createdAt: new Date(row.created_at),
      updatedAt: new Date(row.updated_at),
    };

    // Add optional fields only if they exist
    if (row.parent_chunk_id) {
      chunk.parentChunkId = row.parent_chunk_id;
    }
    if (row.embedding_id) {
      chunk.embeddingId = row.embedding_id;
    }

    return chunk;
  }
}
