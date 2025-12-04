/**
 * EmbeddingsStats Component
 *
 * Displays embeddings statistics and status:
 * - Total embeddings count
 * - Last generation time
 * - Queue size
 * - Error count
 * - Disk usage
 */

import { useQuery } from "@tanstack/react-query";
import { apiClient } from "../services/api-client";
import type {
  EmbeddingsStats as EmbeddingsStatsType,
  ContextWindowUsage,
} from "../types/api";
import {
  Database,
  HardDrive,
  AlertCircle,
  CheckCircle,
  Clock,
} from "lucide-react";

export function EmbeddingsStats(): JSX.Element {
  const {
    data: stats,
    isLoading: statsLoading,
    error: statsError,
  } = useQuery<EmbeddingsStatsType>({
    queryKey: ["embeddings"],
    queryFn: apiClient.getEmbeddingsStats,
    refetchInterval: 5000, // Poll every 5 seconds
  });

  const {
    data: contextUsage,
    isLoading: contextLoading,
    error: contextError,
  } = useQuery<ContextWindowUsage>({
    queryKey: ["context"],
    queryFn: apiClient.getContextWindowUsage,
    refetchInterval: 5000,
  });

  if (statsLoading || contextLoading) {
    return (
      <div className="bg-white rounded-lg shadow-md p-6 animate-pulse">
        <div className="h-6 bg-gray-200 rounded w-1/3 mb-4"></div>
        <div className="space-y-3">
          <div className="h-20 bg-gray-200 rounded"></div>
          <div className="h-20 bg-gray-200 rounded"></div>
        </div>
      </div>
    );
  }

  if (statsError || contextError) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-6">
        <p className="text-red-800 font-semibold">
          Failed to load embeddings stats
        </p>
        <p className="text-red-600 text-sm mt-2">
          {String(statsError || contextError)}
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Embeddings Statistics */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <h2 className="text-xl font-bold text-gray-900 mb-4">Embeddings</h2>

        {stats && stats.totalCount !== undefined ? (
          <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
            <StatCard
              icon={<Database className="w-5 h-5" />}
              label="Total Count"
              value={stats.totalCount.toLocaleString()}
              color="blue"
            />
            <StatCard
              icon={<Clock className="w-5 h-5" />}
              label="Last Generated"
              value={formatLastGenerated(stats.lastGenerated)}
              color="gray"
            />
            <StatCard
              icon={<AlertCircle className="w-5 h-5" />}
              label="Queue Size"
              value={stats.queueSize ?? 0}
              color={(stats.queueSize ?? 0) > 0 ? "yellow" : "gray"}
            />
            <StatCard
              icon={<AlertCircle className="w-5 h-5" />}
              label="Errors"
              value={stats.errorCount ?? 0}
              color={(stats.errorCount ?? 0) > 0 ? "red" : "green"}
            />
            <StatCard
              icon={<HardDrive className="w-5 h-5" />}
              label="Disk Usage"
              value={stats.diskUsage ?? "N/A"}
              color="gray"
            />
            <StatCard
              icon={<CheckCircle className="w-5 h-5" />}
              label="Status"
              value={getEmbeddingsStatus(stats)}
              color={getEmbeddingsStatusColor(stats)}
            />
          </div>
        ) : (
          <div className="bg-gray-50 rounded-lg p-8 text-center">
            <p className="text-gray-600">No embeddings data available</p>
          </div>
        )}
      </div>

      {/* Context Window Usage */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <h2 className="text-xl font-bold text-gray-900 mb-4">Context Window</h2>

        {contextUsage && contextUsage.current !== undefined ? (
          <>
            {/* Progress Bar */}
            <div className="mb-4">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium text-gray-700">
                  {contextUsage.current.toLocaleString()} /{" "}
                  {contextUsage.max.toLocaleString()} tokens
                </span>
                <span
                  className={`text-sm font-medium ${getContextStatusColor(contextUsage.status)}`}
                >
                  {contextUsage.percentage}% •{" "}
                  {contextUsage.status.toUpperCase()}
                </span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-4 overflow-hidden">
                <div
                  className={`h-full transition-all duration-500 ${getContextBarColor(contextUsage.status)}`}
                  style={{
                    width: `${Math.min(contextUsage.percentage, 100)}%`,
                  }}
                ></div>
              </div>
            </div>

            {/* Status Message */}
            <div
              className={`rounded-lg p-4 ${getContextBgColor(contextUsage.status)}`}
            >
              <p
                className={`text-sm font-medium ${getContextTextColor(contextUsage.status)}`}
              >
                {getContextMessage(contextUsage)}
              </p>
            </div>
          </>
        ) : (
          <div className="bg-gray-50 rounded-lg p-8 text-center">
            <p className="text-gray-600">No context data available</p>
          </div>
        )}
      </div>
    </div>
  );
}

interface StatCardProps {
  icon: React.ReactNode;
  label: string;
  value: string | number;
  color: "blue" | "gray" | "yellow" | "red" | "green";
}

function StatCard({ icon, label, value, color }: StatCardProps): JSX.Element {
  const colorClasses = {
    blue: "text-blue-600 bg-blue-50",
    gray: "text-gray-600 bg-gray-50",
    yellow: "text-yellow-600 bg-yellow-50",
    red: "text-red-600 bg-red-50",
    green: "text-green-600 bg-green-50",
  };

  return (
    <div className="bg-gray-50 rounded-lg p-4">
      <div
        className={`inline-flex items-center justify-center w-10 h-10 rounded-lg mb-3 ${colorClasses[color]}`}
      >
        {icon}
      </div>
      <p className="text-sm font-medium text-gray-600 mb-1">{label}</p>
      <p className="text-2xl font-bold text-gray-900">{value}</p>
    </div>
  );
}

function formatLastGenerated(timestamp: string): string {
  const date = new Date(timestamp);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMins = Math.floor(diffMs / (1000 * 60));
  const diffHours = Math.floor(diffMs / (1000 * 60 * 60));

  if (diffMins < 1) {
    return "Just now";
  } else if (diffMins < 60) {
    return `${diffMins}m ago`;
  } else if (diffHours < 24) {
    return `${diffHours}h ago`;
  } else {
    return date.toLocaleDateString();
  }
}

function getEmbeddingsStatus(stats: EmbeddingsStatsType): string {
  if ((stats.errorCount ?? 0) > 0) {
    return "Errors";
  } else if ((stats.queueSize ?? 0) > 0) {
    return "Processing";
  } else {
    return "Healthy";
  }
}

function getEmbeddingsStatusColor(
  stats: EmbeddingsStatsType,
): "red" | "yellow" | "green" {
  if ((stats.errorCount ?? 0) > 0) {
    return "red";
  } else if ((stats.queueSize ?? 0) > 0) {
    return "yellow";
  } else {
    return "green";
  }
}

function getContextStatusColor(status: string): string {
  switch (status) {
    case "healthy":
      return "text-kioku-success";
    case "warning":
      return "text-kioku-warning";
    case "critical":
      return "text-kioku-danger";
    default:
      return "text-gray-600";
  }
}

function getContextBarColor(status: string): string {
  switch (status) {
    case "healthy":
      return "bg-kioku-success";
    case "warning":
      return "bg-kioku-warning";
    case "critical":
      return "bg-kioku-danger";
    default:
      return "bg-gray-400";
  }
}

function getContextBgColor(status: string): string {
  switch (status) {
    case "healthy":
      return "bg-green-50";
    case "warning":
      return "bg-yellow-50";
    case "critical":
      return "bg-red-50";
    default:
      return "bg-gray-50";
  }
}

function getContextTextColor(status: string): string {
  switch (status) {
    case "healthy":
      return "text-green-800";
    case "warning":
      return "text-yellow-800";
    case "critical":
      return "text-red-800";
    default:
      return "text-gray-800";
  }
}

function getContextMessage(usage: ContextWindowUsage): string {
  switch (usage.status) {
    case "healthy":
      return "Context window is healthy. Plenty of space available.";
    case "warning":
      return "Context window is filling up. Consider pruning old contexts.";
    case "critical":
      return "Context window is nearly full! Automatic pruning recommended.";
    default:
      return "Context window status unknown.";
  }
}
