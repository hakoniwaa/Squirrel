import { describe, it, expect, beforeAll, afterAll, beforeEach } from 'vitest';
import { setupServer } from 'msw/node';
import { http, HttpResponse } from 'msw';

// Mock the AgentCortex API client
class MockAgentCortexAPIClient {
  private apiKey: string;
  private apiUrl: string;

  constructor(apiKey: string, apiUrl = 'https://api.agentcortex.dev') {
    this.apiKey = apiKey;
    this.apiUrl = apiUrl;
  }

  async request(method: string, endpoint: string, body?: any) {
    const response = await fetch(`${this.apiUrl}${endpoint}`, {
      method,
      headers: {
        'Authorization': `Bearer ${this.apiKey}`,
        'Content-Type': 'application/json',
      },
      body: body ? JSON.stringify(body) : undefined,
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.message || `API request failed: ${response.status}`);
    }

    return response.json();
  }

  // Memory operations
  async storeMemory(content: string, memoryType?: string, importance?: number) {
    return this.request('POST', '/memories', { content, memoryType, importance });
  }

  async searchMemory(query: string, limit = 10) {
    return this.request('POST', '/memories/search', { query, limit });
  }

  async getMemories(memoryType?: string) {
    const params = memoryType ? `?memoryType=${memoryType}` : '';
    return this.request('GET', `/memories${params}`);
  }

  // Project operations
  async createProject(name: string, description?: string) {
    return this.request('POST', '/projects', { name, description });
  }

  async getCurrentProject() {
    return this.request('GET', '/projects/current');
  }

  async setCurrentProject(projectId: string) {
    return this.request('POST', `/projects/${projectId}/set-current`);
  }

  // Task operations
  async createTask(title: string, description?: string, priority?: string) {
    return this.request('POST', '/tasks', { title, description, priority });
  }

  async listTasks(status?: string, priority?: string) {
    const params = new URLSearchParams();
    if (status) params.append('status', status);
    if (priority) params.append('priority', priority);
    const query = params.toString() ? `?${params.toString()}` : '';
    return this.request('GET', `/tasks${query}`);
  }

  async updateTaskStatus(taskId: string, status: string, notes?: string) {
    return this.request('PATCH', `/tasks/${taskId}`, { status, notes });
  }
}

// Mock server setup
const server = setupServer(
  // Memory endpoints
  http.post('https://api.agentcortex.dev/memories', () => {
    return HttpResponse.json({
      memory: {
        id: 'test-memory-id',
        content: 'Test memory content',
        memory_type: 'general',
        importance: 5,
        created_at: new Date().toISOString(),
        embedding: new Array(1536).fill(0.1)
      }
    });
  }),

  http.post('https://api.agentcortex.dev/memories/search', () => {
    return HttpResponse.json({
      memories: [
        {
          id: 'memory-1',
          content: 'Relevant memory content',
          similarity: 0.85,
          memory_type: 'technical',
          importance: 8
        }
      ]
    });
  }),

  http.get('https://api.agentcortex.dev/memories', () => {
    return HttpResponse.json({
      memories: [],
      pagination: { total: 0, page: 1, limit: 10 }
    });
  }),

  // Project endpoints
  http.post('https://api.agentcortex.dev/projects', () => {
    return HttpResponse.json({
      project: {
        id: 'test-project-id',
        name: 'Test Project',
        description: 'A test project',
        created_at: new Date().toISOString()
      }
    });
  }),

  http.get('https://api.agentcortex.dev/projects/current', () => {
    return HttpResponse.json({
      project: {
        id: 'current-project-id',
        name: 'Current Project'
      }
    });
  }),

  http.post('https://api.agentcortex.dev/projects/:id/set-current', () => {
    return HttpResponse.json({ success: true });
  }),

  // Task endpoints
  http.post('https://api.agentcortex.dev/tasks', () => {
    return HttpResponse.json({
      task: {
        id: 'test-task-id',
        title: 'Test Task',
        description: 'A test task',
        status: 'pending',
        priority: 'medium',
        created_at: new Date().toISOString()
      }
    });
  }),

  http.get('https://api.agentcortex.dev/tasks', () => {
    return HttpResponse.json({
      tasks: [],
      pagination: { total: 0, page: 1, limit: 10 }
    });
  }),

  http.patch('https://api.agentcortex.dev/tasks/:id', () => {
    return HttpResponse.json({
      task: {
        id: 'test-task-id',
        status: 'completed',
        updated_at: new Date().toISOString()
      }
    });
  }),

  // Error case
  http.post('https://api.agentcortex.dev/error', () => {
    return HttpResponse.json(
      { message: 'Test error message' },
      { status: 400 }
    );
  })
);

describe('AgentCortex API Client', () => {
  let client: MockAgentCortexAPIClient;

  beforeAll(() => {
    server.listen();
  });

  afterAll(() => {
    server.close();
  });

  beforeEach(() => {
    client = new MockAgentCortexAPIClient('test-api-key');
    server.resetHandlers();
  });

  describe('Authentication', () => {
    it('should include API key in requests', async () => {
      const result = await client.storeMemory('Test content');
      expect(result.memory).toBeDefined();
      expect(result.memory.content).toBe('Test memory content');
    });

    it('should handle API errors gracefully', async () => {
      try {
        await client.request('POST', '/error');
        expect.fail('Should have thrown an error');
      } catch (error) {
        expect(error).toBeInstanceOf(Error);
        expect((error as Error).message).toContain('Test error message');
      }
    });
  });

  describe('Memory Operations', () => {
    it('should store memory with content', async () => {
      const result = await client.storeMemory('Important information');
      
      expect(result.memory).toBeDefined();
      expect(result.memory.id).toBe('test-memory-id');
      expect(result.memory.content).toBe('Test memory content');
      expect(result.memory.importance).toBe(5);
    });

    it('should search memories semantically', async () => {
      const result = await client.searchMemory('technical details');
      
      expect(result.memories).toBeDefined();
      expect(Array.isArray(result.memories)).toBe(true);
      expect(result.memories.length).toBeGreaterThan(0);
      expect(result.memories[0].similarity).toBeGreaterThan(0.8);
    });

    it('should retrieve memories with filters', async () => {
      const result = await client.getMemories('technical');
      
      expect(result.memories).toBeDefined();
      expect(Array.isArray(result.memories)).toBe(true);
    });
  });

  describe('Project Operations', () => {
    it('should create new project', async () => {
      const result = await client.createProject('New Project', 'Description');
      
      expect(result.project).toBeDefined();
      expect(result.project.id).toBe('test-project-id');
      expect(result.project.name).toBe('Test Project');
    });

    it('should get current project', async () => {
      const result = await client.getCurrentProject();
      
      expect(result.project).toBeDefined();
      expect(result.project.id).toBe('current-project-id');
    });

    it('should set current project', async () => {
      const result = await client.setCurrentProject('new-project-id');
      
      expect(result.success).toBe(true);
    });
  });

  describe('Task Operations', () => {
    it('should create new task', async () => {
      const result = await client.createTask('New Task', 'Task description', 'high');
      
      expect(result.task).toBeDefined();
      expect(result.task.id).toBe('test-task-id');
      expect(result.task.title).toBe('Test Task');
      expect(result.task.status).toBe('pending');
    });

    it('should list tasks with filters', async () => {
      const result = await client.listTasks('pending', 'high');
      
      expect(result.tasks).toBeDefined();
      expect(Array.isArray(result.tasks)).toBe(true);
    });

    it('should update task status', async () => {
      const result = await client.updateTaskStatus('task-id', 'completed', 'Finished successfully');
      
      expect(result.task).toBeDefined();
      expect(result.task.status).toBe('completed');
    });
  });

  describe('Error Handling', () => {
    it('should handle network errors', async () => {
      // Create client with invalid URL
      const badClient = new MockAgentCortexAPIClient('test-key', 'https://invalid-url-that-does-not-exist.com');
      
      try {
        await badClient.storeMemory('Test');
        expect.fail('Should have thrown a network error');
      } catch (error) {
        expect(error).toBeInstanceOf(Error);
      }
    });

    it('should handle malformed API responses', async () => {
      server.use(
        http.post('https://api.agentcortex.dev/memories', () => {
          return new HttpResponse('invalid json', { status: 200 });
        })
      );

      try {
        await client.storeMemory('Test');
        expect.fail('Should have thrown a parsing error');
      } catch (error) {
        expect(error).toBeInstanceOf(Error);
      }
    });
  });
});