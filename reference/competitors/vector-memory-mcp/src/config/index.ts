import { join } from "path";
import { homedir } from "os";

export interface Config {
  dbPath: string;
  embeddingModel: string;
  embeddingDimension: number;
}

const DEFAULT_DB_PATH = join(
  homedir(),
  ".local",
  "share",
  "vector-memory-mcp",
  "memories.db"
);

const DEFAULT_EMBEDDING_MODEL = "Xenova/all-MiniLM-L6-v2";
const DEFAULT_EMBEDDING_DIMENSION = 384;

export function loadConfig(): Config {
  return {
    dbPath: process.env.VECTOR_MEMORY_DB_PATH ?? DEFAULT_DB_PATH,
    embeddingModel: process.env.VECTOR_MEMORY_MODEL ?? DEFAULT_EMBEDDING_MODEL,
    embeddingDimension: DEFAULT_EMBEDDING_DIMENSION,
  };
}

export const config = loadConfig();
