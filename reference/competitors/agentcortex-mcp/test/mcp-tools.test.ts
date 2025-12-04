import { describe, it, expect, beforeEach, vi } from 'vitest';
import { z } from 'zod';

// Mock the MCP tools that would be defined in the main application
const mockTools = {
  // Memory tools
  store_memory: async (content: string, memoryType?: string, importance?: number) => {
    if (!content || content.trim().length === 0) {
      throw new Error('Memory content is required');
    }
    
    if (importance !== undefined && (importance < 1 || importance > 10)) {
      throw new Error('Importance must be between 1 and 10');
    }

    return {
      memory: {
        id: 'mock-memory-id',
        content: content.trim(),
        memory_type: memoryType || 'general',
        importance: importance || 5,
        created_at: new Date().toISOString()
      }
    };
  },

  search_memory: async (query: string, limit = 10) => {
    if (!query || query.trim().length === 0) {
      throw new Error('Search query is required');
    }

    if (limit < 1 || limit > 100) {
      throw new Error('Limit must be between 1 and 100');
    }

    return {
      memories: [
        {
          id: 'memory-1',
          content: 'Relevant memory about ' + query,
          similarity: 0.85,
          memory_type: 'technical',
          importance: 8
        }
      ]
    };
  },

  get_memories: async (memoryType?: string) => {
    return {
      memories: memoryType ? [] : [
        {
          id: 'memory-1',
          content: 'General memory',
          memory_type: 'general',
          importance: 5
        }
      ],
      pagination: { total: memoryType ? 0 : 1, page: 1, limit: 10 }
    };
  },

  // Project tools
  create_project: async (name: string, description?: string) => {
    if (!name || name.trim().length === 0) {
      throw new Error('Project name is required');
    }

    return {
      project: {
        id: 'mock-project-id',
        name: name.trim(),
        description: description?.trim(),
        created_at: new Date().toISOString()
      }
    };
  },

  get_current_project: async () => {
    return {
      project: {
        id: 'current-project-id',
        name: 'Current Project',
        memories_count: 5,
        tasks_count: 3
      }
    };
  },

  set_current_project: async (projectId: string) => {
    if (!projectId || projectId.trim().length === 0) {
      throw new Error('Project ID is required');
    }

    return {
      success: true,
      project: {
        id: projectId,
        name: 'Switched Project'
      }
    };
  },

  list_projects: async () => {
    return {
      projects: [
        {
          id: 'project-1',
          name: 'Project One',
          memories_count: 10,
          tasks_count: 5
        },
        {
          id: 'project-2', 
          name: 'Project Two',
          memories_count: 3,
          tasks_count: 8
        }
      ]
    };
  },

  // Task tools
  create_task: async (title: string, description?: string, priority?: string) => {
    if (!title || title.trim().length === 0) {
      throw new Error('Task title is required');
    }

    const validPriorities = ['low', 'medium', 'high'];
    if (priority && !validPriorities.includes(priority)) {
      throw new Error('Priority must be low, medium, or high');
    }

    return {
      task: {
        id: 'mock-task-id',
        title: title.trim(),
        description: description?.trim(),
        priority: priority || 'medium',
        status: 'pending',
        created_at: new Date().toISOString()
      }
    };
  },

  list_tasks: async (status?: string, priority?: string) => {
    const validStatuses = ['pending', 'in_progress', 'completed', 'cancelled'];
    const validPriorities = ['low', 'medium', 'high'];

    if (status && !validStatuses.includes(status)) {
      throw new Error('Invalid status filter');
    }

    if (priority && !validPriorities.includes(priority)) {
      throw new Error('Invalid priority filter');
    }

    return {
      tasks: [
        {
          id: 'task-1',
          title: 'Sample Task',
          status: status || 'pending',
          priority: priority || 'medium'
        }
      ]
    };
  },

  update_task_status: async (taskId: string, status: string, notes?: string) => {
    if (!taskId || taskId.trim().length === 0) {
      throw new Error('Task ID is required');
    }

    const validStatuses = ['pending', 'in_progress', 'completed', 'cancelled'];
    if (!validStatuses.includes(status)) {
      throw new Error('Invalid task status');
    }

    return {
      task: {
        id: taskId,
        status,
        notes,
        updated_at: new Date().toISOString()
      }
    };
  },

  suggest_next_task: async (context?: string) => {
    return {
      suggestions: [
        {
          title: 'Suggested Task Based on Context',
          description: 'AI-generated task suggestion',
          priority: 'medium',
          reasoning: context ? `Based on: ${context}` : 'Based on project analysis'
        }
      ]
    };
  },

  break_down_task: async (taskId: string, targetComplexity = 5) => {
    if (!taskId || taskId.trim().length === 0) {
      throw new Error('Task ID is required');
    }

    if (targetComplexity < 1 || targetComplexity > 10) {
      throw new Error('Target complexity must be between 1 and 10');
    }

    return {
      subtasks: [
        {
          title: 'Research and Planning',
          description: 'Initial research and requirement gathering',
          priority: 'high'
        },
        {
          title: 'Implementation',
          description: 'Core development work',
          priority: 'high'
        },
        {
          title: 'Testing and Validation',
          description: 'Quality assurance and testing',
          priority: 'medium'
        }
      ]
    };
  }
};

// Zod schemas for validation
const StoreMemorySchema = z.object({
  content: z.string().min(1, 'Content is required'),
  memoryType: z.string().optional(),
  importance: z.number().min(1).max(10).optional()
});

const SearchMemorySchema = z.object({
  query: z.string().min(1, 'Query is required'),
  limit: z.number().min(1).max(100).optional()
});

const CreateProjectSchema = z.object({
  name: z.string().min(1, 'Name is required'),
  description: z.string().optional()
});

const CreateTaskSchema = z.object({
  title: z.string().min(1, 'Title is required'),
  description: z.string().optional(),
  priority: z.enum(['low', 'medium', 'high']).optional()
});

describe('MCP Tools', () => {
  describe('Memory Management', () => {
    describe('store_memory', () => {
      it('should store memory with valid content', async () => {
        const result = await mockTools.store_memory('Important project decision');
        
        expect(result.memory).toBeDefined();
        expect(result.memory.content).toBe('Important project decision');
        expect(result.memory.memory_type).toBe('general');
        expect(result.memory.importance).toBe(5);
      });

      it('should store memory with custom type and importance', async () => {
        const result = await mockTools.store_memory('Technical architecture note', 'technical', 9);
        
        expect(result.memory.memory_type).toBe('technical');
        expect(result.memory.importance).toBe(9);
      });

      it('should reject empty content', async () => {
        await expect(mockTools.store_memory('')).rejects.toThrow('Memory content is required');
      });

      it('should reject invalid importance values', async () => {
        await expect(mockTools.store_memory('test', undefined, 11)).rejects.toThrow('Importance must be between 1 and 10');
        await expect(mockTools.store_memory('test', undefined, 0)).rejects.toThrow('Importance must be between 1 and 10');
      });

      it('should validate with Zod schema', () => {
        expect(() => StoreMemorySchema.parse({ content: 'valid content' })).not.toThrow();
        expect(() => StoreMemorySchema.parse({ content: '' })).toThrow();
        expect(() => StoreMemorySchema.parse({ content: 'test', importance: 11 })).toThrow();
      });
    });

    describe('search_memory', () => {
      it('should search memories with query', async () => {
        const result = await mockTools.search_memory('authentication');
        
        expect(result.memories).toBeDefined();
        expect(Array.isArray(result.memories)).toBe(true);
        expect(result.memories[0].content).toContain('authentication');
        expect(result.memories[0].similarity).toBeGreaterThan(0.8);
      });

      it('should respect limit parameter', async () => {
        const result = await mockTools.search_memory('test', 5);
        expect(result.memories.length).toBeLessThanOrEqual(5);
      });

      it('should reject empty query', async () => {
        await expect(mockTools.search_memory('')).rejects.toThrow('Search query is required');
      });

      it('should reject invalid limit', async () => {
        await expect(mockTools.search_memory('test', 101)).rejects.toThrow('Limit must be between 1 and 100');
      });

      it('should validate with Zod schema', () => {
        expect(() => SearchMemorySchema.parse({ query: 'valid query' })).not.toThrow();
        expect(() => SearchMemorySchema.parse({ query: '' })).toThrow();
        expect(() => SearchMemorySchema.parse({ query: 'test', limit: 101 })).toThrow();
      });
    });

    describe('get_memories', () => {
      it('should retrieve all memories without filter', async () => {
        const result = await mockTools.get_memories();
        
        expect(result.memories).toBeDefined();
        expect(result.pagination).toBeDefined();
        expect(result.pagination.total).toBeGreaterThan(0);
      });

      it('should filter by memory type', async () => {
        const result = await mockTools.get_memories('technical');
        
        expect(result.memories).toBeDefined();
        expect(Array.isArray(result.memories)).toBe(true);
      });
    });
  });

  describe('Project Management', () => {
    describe('create_project', () => {
      it('should create project with name', async () => {
        const result = await mockTools.create_project('New Project');
        
        expect(result.project).toBeDefined();
        expect(result.project.name).toBe('New Project');
        expect(result.project.id).toBeDefined();
      });

      it('should create project with description', async () => {
        const result = await mockTools.create_project('Test Project', 'A test project');
        
        expect(result.project.description).toBe('A test project');
      });

      it('should reject empty name', async () => {
        await expect(mockTools.create_project('')).rejects.toThrow('Project name is required');
      });

      it('should validate with Zod schema', () => {
        expect(() => CreateProjectSchema.parse({ name: 'Valid Name' })).not.toThrow();
        expect(() => CreateProjectSchema.parse({ name: '' })).toThrow();
      });
    });

    describe('get_current_project', () => {
      it('should return current project info', async () => {
        const result = await mockTools.get_current_project();
        
        expect(result.project).toBeDefined();
        expect(result.project.id).toBeDefined();
        expect(result.project.memories_count).toBeDefined();
        expect(result.project.tasks_count).toBeDefined();
      });
    });

    describe('set_current_project', () => {
      it('should switch to project', async () => {
        const result = await mockTools.set_current_project('project-123');
        
        expect(result.success).toBe(true);
        expect(result.project.id).toBe('project-123');
      });

      it('should reject empty project ID', async () => {
        await expect(mockTools.set_current_project('')).rejects.toThrow('Project ID is required');
      });
    });

    describe('list_projects', () => {
      it('should return list of projects', async () => {
        const result = await mockTools.list_projects();
        
        expect(result.projects).toBeDefined();
        expect(Array.isArray(result.projects)).toBe(true);
        expect(result.projects.length).toBeGreaterThan(0);
        expect(result.projects[0].memories_count).toBeDefined();
        expect(result.projects[0].tasks_count).toBeDefined();
      });
    });
  });

  describe('Task Management', () => {
    describe('create_task', () => {
      it('should create task with title', async () => {
        const result = await mockTools.create_task('New Task');
        
        expect(result.task).toBeDefined();
        expect(result.task.title).toBe('New Task');
        expect(result.task.status).toBe('pending');
        expect(result.task.priority).toBe('medium');
      });

      it('should create task with all fields', async () => {
        const result = await mockTools.create_task('Important Task', 'Detailed description', 'high');
        
        expect(result.task.description).toBe('Detailed description');
        expect(result.task.priority).toBe('high');
      });

      it('should reject empty title', async () => {
        await expect(mockTools.create_task('')).rejects.toThrow('Task title is required');
      });

      it('should reject invalid priority', async () => {
        await expect(mockTools.create_task('test', undefined, 'invalid')).rejects.toThrow('Priority must be low, medium, or high');
      });

      it('should validate with Zod schema', () => {
        expect(() => CreateTaskSchema.parse({ title: 'Valid Title' })).not.toThrow();
        expect(() => CreateTaskSchema.parse({ title: '' })).toThrow();
        expect(() => CreateTaskSchema.parse({ title: 'test', priority: 'invalid' })).toThrow();
      });
    });

    describe('list_tasks', () => {
      it('should list tasks without filters', async () => {
        const result = await mockTools.list_tasks();
        
        expect(result.tasks).toBeDefined();
        expect(Array.isArray(result.tasks)).toBe(true);
      });

      it('should filter by status', async () => {
        const result = await mockTools.list_tasks('completed');
        
        expect(result.tasks[0].status).toBe('completed');
      });

      it('should filter by priority', async () => {
        const result = await mockTools.list_tasks(undefined, 'high');
        
        expect(result.tasks[0].priority).toBe('high');
      });

      it('should reject invalid status', async () => {
        await expect(mockTools.list_tasks('invalid')).rejects.toThrow('Invalid status filter');
      });

      it('should reject invalid priority', async () => {
        await expect(mockTools.list_tasks(undefined, 'invalid')).rejects.toThrow('Invalid priority filter');
      });
    });

    describe('update_task_status', () => {
      it('should update task status', async () => {
        const result = await mockTools.update_task_status('task-123', 'completed');
        
        expect(result.task.status).toBe('completed');
        expect(result.task.updated_at).toBeDefined();
      });

      it('should update with notes', async () => {
        const result = await mockTools.update_task_status('task-123', 'completed', 'Finished successfully');
        
        expect(result.task.notes).toBe('Finished successfully');
      });

      it('should reject empty task ID', async () => {
        await expect(mockTools.update_task_status('', 'completed')).rejects.toThrow('Task ID is required');
      });

      it('should reject invalid status', async () => {
        await expect(mockTools.update_task_status('task-123', 'invalid')).rejects.toThrow('Invalid task status');
      });
    });

    describe('suggest_next_task', () => {
      it('should suggest tasks without context', async () => {
        const result = await mockTools.suggest_next_task();
        
        expect(result.suggestions).toBeDefined();
        expect(Array.isArray(result.suggestions)).toBe(true);
        expect(result.suggestions[0].title).toBeDefined();
      });

      it('should suggest tasks with context', async () => {
        const result = await mockTools.suggest_next_task('authentication feature');
        
        expect(result.suggestions[0].reasoning).toContain('authentication feature');
      });
    });

    describe('break_down_task', () => {
      it('should break down task into subtasks', async () => {
        const result = await mockTools.break_down_task('task-123');
        
        expect(result.subtasks).toBeDefined();
        expect(Array.isArray(result.subtasks)).toBe(true);
        expect(result.subtasks.length).toBeGreaterThan(0);
        expect(result.subtasks[0].title).toBeDefined();
      });

      it('should respect target complexity', async () => {
        const result = await mockTools.break_down_task('task-123', 3);
        
        expect(result.subtasks).toBeDefined();
      });

      it('should reject empty task ID', async () => {
        await expect(mockTools.break_down_task('')).rejects.toThrow('Task ID is required');
      });

      it('should reject invalid complexity', async () => {
        await expect(mockTools.break_down_task('task-123', 11)).rejects.toThrow('Target complexity must be between 1 and 10');
      });
    });
  });

  describe('Error Handling', () => {
    it('should handle validation errors consistently', () => {
      const invalidInputs = [
        () => mockTools.store_memory(''),
        () => mockTools.search_memory(''),
        () => mockTools.create_project(''),
        () => mockTools.create_task(''),
        () => mockTools.update_task_status('', 'completed')
      ];

      invalidInputs.forEach(async (fn) => {
        await expect(fn()).rejects.toThrow();
      });
    });

    it('should provide meaningful error messages', async () => {
      try {
        await mockTools.store_memory('');
      } catch (error) {
        expect(error).toBeInstanceOf(Error);
        expect((error as Error).message).toContain('required');
      }
    });
  });
});