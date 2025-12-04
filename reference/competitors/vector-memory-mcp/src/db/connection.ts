import * as lancedb from "@lancedb/lancedb";
import { mkdirSync } from "fs";
import { dirname } from "path";

export async function connectToDatabase(dbPath: string): Promise<lancedb.Connection> {
  // Ensure directory exists
  mkdirSync(dirname(dbPath), { recursive: true });

  const db = await lancedb.connect(dbPath);
  return db;
}
