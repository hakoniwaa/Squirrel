export const DELETED_TOMBSTONE = "DELETED";

export interface Memory {
  id: string;
  content: string;
  embedding: number[];
  metadata: Record<string, unknown>;
  createdAt: Date;
  updatedAt: Date;
  supersededBy: string | null;
}

export interface VectorRow {
  id: string;
  distance: number;
}

export function isDeleted(memory: Memory): boolean {
  return memory.supersededBy === DELETED_TOMBSTONE;
}

export function isSuperseded(memory: Memory): boolean {
  return memory.supersededBy !== null;
}

export function memoryToDict(memory: Memory): Record<string, unknown> {
  return {
    id: memory.id,
    content: memory.content,
    metadata: memory.metadata,
    createdAt: memory.createdAt.toISOString(),
    updatedAt: memory.updatedAt.toISOString(),
    supersededBy: memory.supersededBy,
  };
}
