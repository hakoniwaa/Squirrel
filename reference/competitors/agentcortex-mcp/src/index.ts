#!/usr/bin/env node
import { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import { z } from 'zod';
import fetch from 'node-fetch';

// API Client for AgentCortex SaaS
class AgentCortexAPIClient {
  private apiKey: string;
  private apiUrl: string;

  constructor(apiKey: string, apiUrl = 'https://api.agentcortex.dev') {
    this.apiKey = apiKey;
    this.apiUrl = apiUrl;
  }

  private async request(method: string, endpoint: string, body?: any) {
    try {
      const response = await fetch(`${this.apiUrl}${endpoint}`, {
        method,
        headers: {
          'Authorization': `Bearer ${this.apiKey}`,
          'Content-Type': 'application/json',
        },
        body: body ? JSON.stringify(body) : undefined,
      });

      if (!response.ok) {
        let errorMessage = `API request failed: ${response.status} ${response.statusText}`;
        try {
          const error = await response.json() as any;
          errorMessage = error.message || errorMessage;
        } catch {
          // If we can't parse the error response, use the status message
        }
        throw new Error(errorMessage);
      }

      // Track usage
      await this.trackUsage(endpoint, method);

      return response.json();
    } catch (error) {
      if (error instanceof Error) {
        throw error;
      }
      throw new Error(`Network error: ${error}`);
    }
  }

  async validateKey() {
    try {
      const data = await this.request('GET', '/projects') as any;
      return { valid: true, subscription: 'free', projects: data };
    } catch (error: any) {
      throw new Error(`API validation failed: ${error.message}`);
    }
  }

  async trackUsage(endpoint: string, method: string) {
    // Fire and forget usage tracking
    fetch(`${this.apiUrl}/usage/track`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${this.apiKey}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ endpoint, method }),
    }).catch(() => {}); // Ignore errors in usage tracking
  }

  // Project methods
  async createProject(name: string, description?: string) {
    return this.request('POST', '/projects', { name, description });
  }

  async listProjects() {
    return this.request('GET', '/projects');
  }

  async setCurrentProject(projectId: string) {
    return this.request('PUT', '/projects/current', { projectId });
  }

  async getCurrentProject() {
    return this.request('GET', '/projects/current');
  }

  // Memory methods
  async storeMemory(projectId: string | null, content: string, memoryType?: string, importance?: number) {
    if (!projectId) {
      throw new Error('Project ID is required for memory operations');
    }
    return this.request('POST', `/projects/${projectId}/memories`, {
      content,
      memoryType,
      importance,
    });
  }

  async searchMemory(projectId: string | null, query: string, limit: number = 10) {
    if (!projectId) {
      throw new Error('Project ID is required for memory operations');
    }
    return this.request('POST', `/projects/${projectId}/memories/search`, {
      query,
      limit,
    });
  }

  async getMemories(projectId: string | null, limit: number = 20) {
    if (!projectId) {
      throw new Error('Project ID is required for memory operations');
    }
    const params = new URLSearchParams({
      limit: limit.toString(),
    });
    return this.request('GET', `/projects/${projectId}/memories?${params}`);
  }

  async updateMemoryImportance(memoryId: string, importance: number) {
    return this.request('PUT', `/memories/${memoryId}`, { importance });
  }

  // Task methods
  async createTask(projectId: string | null, title: string, description?: string, priority?: 'low' | 'medium' | 'high', dependencies?: string[]) {
    if (!projectId) {
      throw new Error('Project ID is required for task operations');
    }
    return this.request('POST', `/projects/${projectId}/tasks`, {
      title,
      description,
      priority: priority || 'medium',
      dependencies,
    });
  }

  async listTasks(projectId: string | null, status?: string) {
    if (!projectId) {
      throw new Error('Project ID is required for task operations');
    }
    const params = new URLSearchParams({
      ...(status && { status }),
    });
    return this.request('GET', `/projects/${projectId}/tasks?${params}`);
  }

  async updateTaskStatus(taskId: string, status: string) {
    return this.request('PUT', `/tasks/${taskId}`, { status });
  }

  async suggestNextTask(projectId: string | null) {
    return this.request('POST', '/tasks/suggest', { projectId });
  }

  async breakDownTask(taskId: string) {
    return this.request('POST', `/tasks/${taskId}/breakdown`);
  }
}

// Main function
async function main() {
  // Get API key from environment
  const apiKey = process.env.AGENTCORTEX_API_KEY;
  if (!apiKey) {
    console.error('Error: AGENTCORTEX_API_KEY environment variable is required');
    console.error('Get your API key from https://agentcortex.dev/dashboard/api-keys');
    process.exit(1);
  }

  const apiUrl = process.env.AGENTCORTEX_API_URL || 'https://api.agentcortex.dev';
  
  // Initialize API client
  const apiClient = new AgentCortexAPIClient(apiKey, apiUrl);
  
  // Validate API key
  try {
    const { valid, subscription } = await apiClient.validateKey() as any;
    if (!valid) {
      console.error('Error: Invalid API key');
      process.exit(1);
    }
    console.error(`Connected to TaskMem (${subscription} plan)`);
  } catch (error: any) {
    console.error('Error: Failed to validate API key:', error.message);
    process.exit(1);
  }

  // Create MCP server with comprehensive capabilities
  const server = new McpServer(
    {
      name: 'agentcortex',
      version: '1.0.1',
    },
    {
      capabilities: {
        tools: {},
        logging: {},
      },
    }
  );

  // Store current project ID in memory
  let currentProjectId: string | null = null;
  
  // Helper function to ensure we have a current project
  async function ensureCurrentProject(): Promise<string> {
    if (currentProjectId) {
      return currentProjectId;
    }
    
    // Try to get current project from API
    try {
      const response = await apiClient.getCurrentProject() as any;
      const project = response.project;
      if (project && project.id) {
        currentProjectId = project.id;
        return project.id;
      }
    } catch (error) {
      // Current project not set, continue to list projects
    }
    
    // If no current project, get the first available project
    try {
      const response = await apiClient.listProjects() as any;
      const projects = response.projects || response;
      if (projects && projects.length > 0) {
        const projectId = projects[0].id;
        currentProjectId = projectId;
        // Set it as current project in the API
        await apiClient.setCurrentProject(projectId);
        return projectId;
      }
    } catch (error) {
      // Can't get projects
    }
    
    throw new Error('No project available. Please create a project first using create_project.');
  }

  // Tool: store_memory
  server.tool(
    'store_memory',
    'Store important information in persistent memory for later retrieval. Use this to remember key facts, decisions, code patterns, or any information that might be useful in future conversations.',
    {
      content: z.string().min(1).describe('The content/information to store in memory. Can be facts, insights, code snippets, decisions, or any important information you want to remember for later use.'),
      memoryType: z.string().optional().describe('Optional category/type of memory to help with organization. Examples: "code", "decision", "insight", "reference", "todo", "bug", "feature"'),
      importance: z.number().min(1).max(10).optional().describe('Importance level from 1-10 where 10 is most critical. Higher importance memories are prioritized in search results. Default: 5'),
    },
    async ({ content, memoryType, importance }) => {
      try {
        const projectId = await ensureCurrentProject();
        const memory = await apiClient.storeMemory(
          projectId,
          content,
          memoryType,
          importance || 5
        ) as any;
        
        return {
          content: [
            {
              type: 'text',
              text: `✅ Memory stored successfully\nID: ${memory.id}\nType: ${memoryType || 'general'}\nImportance: ${importance || 5}/10`,
            },
          ],
        };
      } catch (error: any) {
        return {
          content: [
            {
              type: 'text',
              text: `Error: ${error.message}`,
            },
          ],
        };
      }
    }
  );

  // Tool: search_memory
  server.tool(
    'search_memory',
    'Search through stored memories using semantic search. Finds memories related to your query even if they don\'t contain exact keywords.',
    {
      query: z.string().min(1).describe('Natural language search query to find relevant memories. Use keywords, phrases, or questions like "code examples", "API decisions", or "how did we solve X?"'),
      limit: z.number().min(1).max(50).optional().describe('Maximum number of results to return (1-50). Default: 10. Higher limits may include less relevant results.'),
    },
    async ({ query, limit }) => {
      try {
        const projectId = await ensureCurrentProject();
        const response = await apiClient.searchMemory(
          projectId,
          query,
          limit || 10
        ) as any;
        const results = response.memories || response;
        
        return {
          content: [
            {
              type: 'text',
              text: JSON.stringify(results, null, 2),
            },
          ],
        };
      } catch (error: any) {
        return {
          content: [
            {
              type: 'text',
              text: `Error: ${error.message}`,
            },
          ],
        };
      }
    }
  );

  // Tool: get_memories
  server.tool(
    'get_memories',
    'Retrieve memories with optional filtering by type and date range. Returns memories in reverse chronological order (newest first).',
    {
      memoryType: z.string().optional().describe('Filter by memory type'),
      timeRange: z.object({
        start: z.string().optional().describe('Start date-time'),
        end: z.string().optional().describe('End date-time'),
      }).optional().describe('Time range filter'),
    },
    async () => {
      try {
        const projectId = await ensureCurrentProject();
        const response = await apiClient.getMemories(
          projectId,
          20
        ) as any;
        const memories = response.memories || response;
        
        const memoryData = memories.map((m: any) => ({
          id: m.id,
          content: m.content,
          type: m.memory_type,
          importance: m.importance,
          created_at: m.created_at,
        }));
        
        return {
          content: [
            {
              type: 'text',
              text: JSON.stringify(memoryData, null, 2),
            },
          ],
        };
      } catch (error: any) {
        return {
          content: [
            {
              type: 'text',
              text: `Error: ${error.message}`,
            },
          ],
        };
      }
    }
  );

  // Tool: update_memory_importance
  server.tool(
    'update_memory_importance',
    'Update the importance level of an existing memory. Use this to prioritize critical information or de-prioritize outdated content.',
    {
      memoryId: z.string().describe('ID of the memory to update'),
      importance: z.number().min(1).max(10).describe('New importance level (1-10)'),
    },
    async ({ memoryId, importance }) => {
      try {
        const memory = await apiClient.updateMemoryImportance(memoryId, importance) as any;
        
        return {
          content: [
            {
              type: 'text',
              text: `Memory importance updated successfully: ${memory.id} (importance: ${memory.importance})`,
            },
          ],
        };
      } catch (error: any) {
        return {
          content: [
            {
              type: 'text',
              text: `Error: ${error.message}`,
            },
          ],
        };
      }
    }
  );

  // Tool: create_project
  server.tool(
    'create_project',
    'Create a new project to organize memories and tasks. Projects help separate different work contexts and make it easier to find relevant information.',
    {
      name: z.string().min(1).describe('Project name'),
      description: z.string().optional().describe('Project description'),
    },
    async ({ name, description }) => {
      try {
        const response = await apiClient.createProject(name, description) as any;
        const project = response.project || response;
        
        const projectData = {
          id: project.id,
          name: project.name,
          description: project.description,
          created_at: project.created_at,
        };
        
        return {
          content: [
            {
              type: 'text',
              text: JSON.stringify(projectData, null, 2),
            },
          ],
        };
      } catch (error: any) {
        return {
          content: [
            {
              type: 'text',
              text: `Error: ${error.message}`,
            },
          ],
        };
      }
    }
  );

  // Tool: set_current_project
  server.tool(
    'set_current_project',
    'Switch the active project context. All memory and task operations will use this project until changed.',
    {
      projectId: z.string().describe('Project ID to switch to'),
    },
    async ({ projectId }) => {
      try {
        currentProjectId = projectId;
        await apiClient.setCurrentProject(projectId);
        
        return {
          content: [
            {
              type: 'text',
              text: `Current project set to: ${projectId}`,
            },
          ],
        };
      } catch (error: any) {
        return {
          content: [
            {
              type: 'text',
              text: `Error: ${error.message}`,
            },
          ],
        };
      }
    }
  );

  // Tool: get_current_project
  server.tool(
    'get_current_project',
    'Get information about the currently active project, including stats on memories and tasks.',
    {
      type: 'object',
      properties: {},
      additionalProperties: false,
    },
    async () => {
      try {
        const response = await apiClient.getCurrentProject() as any;
        const project = response.project;
        
        if (!project) {
          return {
            content: [
              {
                type: 'text',
                text: 'No project currently selected',
              },
            ],
          };
        }

        const projectData = {
          id: project.id,
          name: project.name,
          description: project.description,
        };
        
        return {
          content: [
            {
              type: 'text',
              text: JSON.stringify(projectData, null, 2),
            },
          ],
        };
      } catch (error: any) {
        return {
          content: [
            {
              type: 'text',
              text: `Error: ${error.message}`,
            },
          ],
        };
      }
    }
  );

  // Tool: list_projects
  server.tool(
    'list_projects',
    'List all available projects with their basic information and statistics.',
    {
      type: 'object',
      properties: {},
      additionalProperties: false,
    },
    async () => {
      try {
        const response = await apiClient.listProjects() as any;
        const projects = response.projects || response;
        
        const projectData = projects.map((p: any) => ({
          id: p.id,
          name: p.name,
          description: p.description,
          memory_count: p.memory_count,
          task_count: p.task_count,
          created_at: p.created_at,
        }));
        
        return {
          content: [
            {
              type: 'text',
              text: JSON.stringify(projectData, null, 2),
            },
          ],
        };
      } catch (error: any) {
        return {
          content: [
            {
              type: 'text',
              text: `Error: ${error.message}`,
            },
          ],
        };
      }
    }
  );

  // Tool: create_task
  server.tool(
    'create_task',
    'Create a new task within the current project. Tasks help organize work and track progress on specific objectives.',
    {
      title: z.string().min(1).describe('Task title'),
      description: z.string().optional().describe('Task description (optional)'),
      priority: z.enum(['low', 'medium', 'high']).optional().describe('Task priority (optional)'),
      dependencies: z.array(z.string()).optional().describe('Task IDs this depends on (optional)'),
    },
    async ({ title, description, priority, dependencies }) => {
      try {
        const projectId = await ensureCurrentProject();
        const response = await apiClient.createTask(
          projectId,
          title,
          description,
          priority || 'medium',
          dependencies
        ) as any;
        const task = response.task || response;
        
        const taskData = {
          id: task.id,
          title: task.title,
          priority: task.priority,
          status: task.status,
          created_at: task.created_at,
        };
        
        return {
          content: [
            {
              type: 'text',
              text: JSON.stringify(taskData, null, 2),
            },
          ],
        };
      } catch (error: any) {
        return {
          content: [
            {
              type: 'text',
              text: `Error: ${error.message}`,
            },
          ],
        };
      }
    }
  );

  // Tool: list_tasks
  server.tool(
    'list_tasks',
    'List tasks in the current project with optional filtering by status, priority, or assignee.',
    {
      status: z.enum(['pending', 'in_progress', 'completed', 'cancelled']).optional()
        .describe('Filter by task status'),
      assignee: z.string().optional().describe('Filter by assignee'),
      priority: z.enum(['low', 'medium', 'high']).optional().describe('Filter by priority'),
    },
    async ({ status } = {}) => {
      try {
        const projectId = await ensureCurrentProject();
        const response = await apiClient.listTasks(projectId, status) as any;
        const tasks = response.tasks || response;
        
        const taskData = tasks.map((t: any) => ({
          id: t.id,
          title: t.title,
          priority: t.priority,
          status: t.status,
          parent_id: t.parent_id,
          created_at: t.created_at,
        }));
        
        return {
          content: [
            {
              type: 'text',
              text: JSON.stringify(taskData, null, 2),
            },
          ],
        };
      } catch (error: any) {
        return {
          content: [
            {
              type: 'text',
              text: `Error: ${error.message}`,
            },
          ],
        };
      }
    }
  );

  // Tool: update_task_status
  server.tool(
    'update_task_status',
    'Update the status of an existing task. Use this to track progress and mark tasks as completed.',
    {
      taskId: z.string().describe('Task ID'),
      status: z.enum(['pending', 'in_progress', 'completed', 'cancelled'])
        .describe('New task status'),
      notes: z.string().optional().describe('Optional notes about the update'),
    },
    async ({ taskId, status }) => {
      try {
        const task = await apiClient.updateTaskStatus(taskId, status) as any;
        
        return {
          content: [
            {
              type: 'text',
              text: `Task status updated successfully: ${task.id} (status: ${task.status})`,
            },
          ],
        };
      } catch (error: any) {
        return {
          content: [
            {
              type: 'text',
              text: `Error: ${error.message}`,
            },
          ],
        };
      }
    }
  );

  // Tool: suggest_next_task
  server.tool(
    'suggest_next_task',
    'Get AI-powered suggestions for the next task to work on based on current project context and priorities.',
    {
      context: z.string().optional().describe('Optional context for the suggestion'),
    },
    async () => {
      try {
        const projectId = await ensureCurrentProject();
        const suggestion = await apiClient.suggestNextTask(projectId) as any;
        
        return {
          content: [
            {
              type: 'text',
              text: JSON.stringify(suggestion, null, 2),
            },
          ],
        };
      } catch (error: any) {
        return {
          content: [
            {
              type: 'text',
              text: `Error: ${error.message}`,
            },
          ],
        };
      }
    }
  );

  // Tool: break_down_task
  server.tool(
    'break_down_task',
    'Break down a complex task into smaller, manageable subtasks. Helps with project planning and execution.',
    {
      taskId: z.string().describe('Task ID to break down'),
      targetComplexity: z.number().min(1).max(10).optional().describe('Target complexity level 1-10 (optional)'),
    },
    async ({ taskId }) => {
      try {
        const subtasks = await apiClient.breakDownTask(taskId) as any;
        
        return {
          content: [
            {
              type: 'text',
              text: JSON.stringify(subtasks, null, 2),
            },
          ],
        };
      } catch (error: any) {
        return {
          content: [
            {
              type: 'text',
              text: `Error: ${error.message}`,
            },
          ],
        };
      }
    }
  );

  // Tool: get_project_context
  server.tool(
    'get_project_context',
    'Get comprehensive project overview including recent memories, active tasks, and project statistics.',
    {
      projectId: z.string().optional().describe('Project ID (uses current if not provided)'),
    },
    async ({ projectId }) => {
      try {
        const targetProjectId = projectId || await ensureCurrentProject();

        // Get project details
        const response = await apiClient.listProjects() as any;
        const projects = response.projects || response;
        const project = projects.find((p: any) => p.id === targetProjectId);

        if (!project) {
          return {
            content: [
              {
                type: 'text',
                text: 'Error: Project not found',
              },
            ],
          };
        }

        // Get recent memories and active tasks in parallel
        const [memories, tasks] = await Promise.all([
          apiClient.getMemories(targetProjectId, 10),
          apiClient.listTasks(targetProjectId, 'in_progress'),
        ]) as any;

        const contextData = {
          project: {
            id: project.id,
            name: project.name,
            description: project.description,
          },
          recent_memories: memories.slice(0, 5).map((m: any) => ({
            content: m.content,
            type: m.memory_type,
            importance: m.importance,
          })),
          active_tasks: tasks.map((t: any) => ({
            title: t.title,
            priority: t.priority,
          })),
          stats: {
            total_memories: project.memory_count,
            total_tasks: project.task_count,
          },
        };
        
        return {
          content: [
            {
              type: 'text',
              text: JSON.stringify(contextData, null, 2),
            },
          ],
        };
      } catch (error: any) {
        return {
          content: [
            {
              type: 'text',
              text: `Error: ${error.message}`,
            },
          ],
        };
      }
    }
  );

  // Set up transport
  const transport = new StdioServerTransport();
  await server.connect(transport);

  // Handle graceful shutdown
  process.on('SIGINT', async () => {
    await server.close();
    process.exit(0);
  });
}

// Run the server
main().catch((error) => {
  console.error('Server error:', error);
  process.exit(1);
});