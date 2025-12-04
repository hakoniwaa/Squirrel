import type { CallToolResult } from "@modelcontextprotocol/sdk/types.js";
import type { MemoryService } from "../services/memory.service.js";

export async function handleStoreMemory(
  args: Record<string, unknown> | undefined,
  service: MemoryService
): Promise<CallToolResult> {
  const content = args?.content as string;
  const embeddingText = args?.embedding_text as string | undefined;
  const metadata = (args?.metadata as Record<string, unknown>) ?? {};
  const memory = await service.store(content, metadata, embeddingText);

  return {
    content: [{ type: "text", text: `Memory stored with ID: ${memory.id}` }],
  };
}

export async function handleDeleteMemory(
  args: Record<string, unknown> | undefined,
  service: MemoryService
): Promise<CallToolResult> {
  const id = args?.id as string;
  const success = await service.delete(id);

  return {
    content: [
      {
        type: "text",
        text: success
          ? `Memory ${id} deleted successfully`
          : `Memory ${id} not found`,
      },
    ],
  };
}

export async function handleSearchMemories(
  args: Record<string, unknown> | undefined,
  service: MemoryService
): Promise<CallToolResult> {
  const query = args?.query as string;
  const limit = (args?.limit as number) ?? 10;
  const memories = await service.search(query, limit);

  if (memories.length === 0) {
    return {
      content: [{ type: "text", text: "No memories found matching your query." }],
    };
  }

  const results = memories.map((mem) => {
    let result = `ID: ${mem.id}\nContent: ${mem.content}`;
    if (Object.keys(mem.metadata).length > 0) {
      result += `\nMetadata: ${JSON.stringify(mem.metadata)}`;
    }
    return result;
  });

  return {
    content: [{ type: "text", text: results.join("\n\n---\n\n") }],
  };
}

export async function handleGetMemory(
  args: Record<string, unknown> | undefined,
  service: MemoryService
): Promise<CallToolResult> {
  const id = args?.id as string;
  const memory = await service.get(id);

  if (!memory) {
    return {
      content: [{ type: "text", text: `Memory ${id} not found` }],
    };
  }

  let result = `ID: ${memory.id}\nContent: ${memory.content}`;
  if (Object.keys(memory.metadata).length > 0) {
    result += `\nMetadata: ${JSON.stringify(memory.metadata)}`;
  }
  result += `\nCreated: ${memory.createdAt.toISOString()}`;
  result += `\nUpdated: ${memory.updatedAt.toISOString()}`;
  if (memory.supersededBy) {
    result += `\nSuperseded by: ${memory.supersededBy}`;
  }

  return {
    content: [{ type: "text", text: result }],
  };
}

export async function handleToolCall(
  name: string,
  args: Record<string, unknown> | undefined,
  service: MemoryService
): Promise<CallToolResult> {
  switch (name) {
    case "store_memory":
      return handleStoreMemory(args, service);
    case "delete_memory":
      return handleDeleteMemory(args, service);
    case "search_memories":
      return handleSearchMemories(args, service);
    case "get_memory":
      return handleGetMemory(args, service);
    default:
      return {
        content: [{ type: "text", text: `Unknown tool: ${name}` }],
        isError: true,
      };
  }
}
