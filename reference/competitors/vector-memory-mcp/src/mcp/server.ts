import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} from "@modelcontextprotocol/sdk/types.js";

import { tools } from "./tools.js";
import { handleToolCall } from "./handlers.js";
import type { MemoryService } from "../services/memory.service.js";

export function createServer(memoryService: MemoryService): Server {
  const server = new Server(
    { name: "vector-memory-mcp", version: "0.2.0" },
    { capabilities: { tools: {} } }
  );

  server.setRequestHandler(ListToolsRequestSchema, async () => {
    return { tools };
  });

  server.setRequestHandler(CallToolRequestSchema, async (request) => {
    const { name, arguments: args } = request.params;
    return handleToolCall(name, args, memoryService);
  });

  return server;
}

export async function startServer(memoryService: MemoryService): Promise<void> {
  const server = createServer(memoryService);
  const transport = new StdioServerTransport();
  await server.connect(transport);
}
