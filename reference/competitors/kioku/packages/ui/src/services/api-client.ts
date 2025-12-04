import axios from "axios";
import type {
  ProjectOverview,
  Session,
  SessionDetails,
  ModuleGraph,
  EmbeddingsStats,
  ContextWindowUsage,
  HealthStatus,
  LinkedProjectInfo,
} from "../types/api";

/**
 * API client for Kioku backend
 *
 * Base URL points to Kioku server (defaults to localhost:9090)
 * Vite proxy will forward /api/* requests to the backend
 */
const axiosInstance = axios.create({
  baseURL: "/api",
  timeout: 10000,
  headers: {
    "Content-Type": "application/json",
  },
});

// Request interceptor for logging (development only)
axiosInstance.interceptors.request.use(
  (config) => {
    if (import.meta.env.DEV) {
      console.log(`[API] ${config.method?.toUpperCase()} ${config.url}`);
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  },
);

// Response interceptor for error handling
axiosInstance.interceptors.response.use(
  (response) => response,
  (error) => {
    if (import.meta.env.DEV) {
      console.error("[API Error]", error.message);
    }
    return Promise.reject(error);
  },
);

/**
 * API Client with typed methods
 */
export const apiClient = {
  /**
   * Get project overview
   */
  async getProjectOverview(): Promise<ProjectOverview> {
    const response = await axiosInstance.get<ProjectOverview>("/project");
    return response.data;
  },

  /**
   * Get sessions list
   */
  async getSessions(limit?: number): Promise<Session[]> {
    const response = await axiosInstance.get<Session[]>("/sessions", {
      params: { limit },
    });
    return response.data;
  },

  /**
   * Get session details
   */
  async getSessionDetails(sessionId: string): Promise<SessionDetails> {
    const response = await axiosInstance.get<SessionDetails>(
      `/sessions/${sessionId}`,
    );
    return response.data;
  },

  /**
   * Get module dependency graph
   */
  async getModuleGraph(): Promise<ModuleGraph> {
    const response = await axiosInstance.get<ModuleGraph>("/modules");
    return response.data;
  },

  /**
   * Get embeddings statistics
   */
  async getEmbeddingsStats(): Promise<EmbeddingsStats> {
    const response = await axiosInstance.get<EmbeddingsStats>("/embeddings");
    return response.data;
  },

  /**
   * Get context window usage
   */
  async getContextWindowUsage(): Promise<ContextWindowUsage> {
    const response = await axiosInstance.get<ContextWindowUsage>("/context");
    return response.data;
  },

  /**
   * Get service health status
   */
  async getHealthStatus(): Promise<HealthStatus> {
    const response = await axiosInstance.get<HealthStatus>("/health");
    return response.data;
  },

  /**
   * Get linked projects
   */
  async getLinkedProjects(): Promise<LinkedProjectInfo[]> {
    const response =
      await axiosInstance.get<LinkedProjectInfo[]>("/linked-projects");
    return response.data;
  },
};
