/**
 * ProjectOverview Component
 *
 * Displays project statistics and information:
 * - Project name and type
 * - Tech stack tags
 * - Module count, file count
 * - Database size
 * - Active session indicator
 * - Last session time
 */

import { useQuery } from "@tanstack/react-query";
import { apiClient } from "../services/api-client";
import type { ProjectOverview as ProjectOverviewType } from "../types/api";

export function ProjectOverview(): JSX.Element {
  const {
    data: project,
    isLoading,
    error,
  } = useQuery<ProjectOverviewType>({
    queryKey: ["project"],
    queryFn: apiClient.getProjectOverview,
    refetchInterval: 5000, // Poll every 5 seconds
  });

  if (isLoading) {
    return (
      <div className="bg-white rounded-lg shadow-md p-6 animate-pulse">
        <div className="h-8 bg-gray-200 rounded w-1/3 mb-4"></div>
        <div className="h-4 bg-gray-200 rounded w-1/2 mb-2"></div>
        <div className="h-4 bg-gray-200 rounded w-2/3"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-6">
        <p className="text-red-800 font-semibold">
          Failed to load project overview
        </p>
        <p className="text-red-600 text-sm mt-2">{String(error)}</p>
      </div>
    );
  }

  if (!project) {
    return (
      <div className="bg-gray-50 border border-gray-200 rounded-lg p-6">
        <p className="text-gray-600">No project data available</p>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">{project.name}</h2>
          <p className="text-sm text-gray-600">{project.type}</p>
        </div>
        {project.activeSession && (
          <span className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-kioku-success text-white">
            <span className="w-2 h-2 bg-white rounded-full mr-2 animate-pulse"></span>
            Active Session
          </span>
        )}
      </div>

      {/* Tech Stack */}
      {project.techStack && project.techStack.length > 0 && (
        <div className="mb-6">
          <h3 className="text-sm font-semibold text-gray-700 mb-2">
            Tech Stack
          </h3>
          <div className="flex flex-wrap gap-2">
            {project.techStack.map((tech) => (
              <span
                key={tech}
                className="inline-flex items-center px-3 py-1 rounded-md text-sm font-medium bg-kioku-primary text-white"
              >
                {tech}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Stats Grid */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <StatCard label="Modules" value={project.moduleCount} icon="📦" />
        <StatCard label="Files" value={project.fileCount} icon="📄" />
        <StatCard
          label="Database Size"
          value={project.databaseSize}
          icon="💾"
        />
        <StatCard
          label="Last Session"
          value={formatLastSession(project.lastSessionTime)}
          icon="🕒"
        />
      </div>
    </div>
  );
}

interface StatCardProps {
  label: string;
  value: string | number;
  icon: string;
}

function StatCard({ label, value, icon }: StatCardProps): JSX.Element {
  return (
    <div className="bg-gray-50 rounded-lg p-4">
      <div className="flex items-center justify-between mb-2">
        <span className="text-sm font-medium text-gray-600">{label}</span>
        <span className="text-2xl">{icon}</span>
      </div>
      <p className="text-2xl font-bold text-gray-900">{value}</p>
    </div>
  );
}

function formatLastSession(timestamp?: string): string {
  if (!timestamp) {
    return "Never";
  }

  const date = new Date(timestamp);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMins = Math.floor(diffMs / (1000 * 60));
  const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
  const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));

  if (diffMins < 1) {
    return "Just now";
  } else if (diffMins < 60) {
    return `${diffMins}m ago`;
  } else if (diffHours < 24) {
    return `${diffHours}h ago`;
  } else if (diffDays === 1) {
    return "Yesterday";
  } else if (diffDays < 7) {
    return `${diffDays}d ago`;
  } else {
    return date.toLocaleDateString();
  }
}
