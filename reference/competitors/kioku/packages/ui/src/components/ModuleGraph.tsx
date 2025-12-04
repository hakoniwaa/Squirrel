/**
 * ModuleGraph Component
 *
 * Interactive visualization of module dependencies:
 * - Nodes: modules with file count
 * - Edges: dependencies between modules
 * - Color-coded by activity (active, recent, stale)
 * - Interactive hover and click
 */

import { useQuery } from "@tanstack/react-query";
import { apiClient } from "../services/api-client";
import type { ModuleGraph as ModuleGraphType } from "../types/api";
import { Network } from "lucide-react";

export function ModuleGraph(): JSX.Element {
  const {
    data: graph,
    isLoading,
    error,
  } = useQuery<ModuleGraphType>({
    queryKey: ["modules"],
    queryFn: apiClient.getModuleGraph,
    refetchInterval: 5000, // Poll every 5 seconds
  });

  if (isLoading) {
    return (
      <div className="bg-white rounded-lg shadow-md p-6">
        <h2 className="text-xl font-bold text-gray-900 mb-4">
          Module Dependencies
        </h2>
        <div className="h-96 bg-gray-100 rounded-lg animate-pulse flex items-center justify-center">
          <Network className="w-12 h-12 text-gray-400" />
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-6">
        <p className="text-red-800 font-semibold">
          Failed to load module graph
        </p>
        <p className="text-red-600 text-sm mt-2">{String(error)}</p>
      </div>
    );
  }

  if (!graph || !graph.nodes || graph.nodes.length === 0) {
    return (
      <div className="bg-white rounded-lg shadow-md p-6">
        <h2 className="text-xl font-bold text-gray-900 mb-4">
          Module Dependencies
        </h2>
        <div className="bg-gray-50 rounded-lg p-8 text-center">
          <Network className="w-12 h-12 text-gray-400 mx-auto mb-4" />
          <p className="text-gray-600">No modules found</p>
          <p className="text-sm text-gray-500 mt-2">
            Module graph will appear after scanning your project
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-xl font-bold text-gray-900">Module Dependencies</h2>
        <div className="flex items-center space-x-4 text-sm">
          <ActivityLegend />
        </div>
      </div>

      {/* Module Tree View (Simple visualization) */}
      <div className="space-y-2 max-h-96 overflow-y-auto">
        {graph.nodes.map((node) => (
          <ModuleNode key={node.id} node={node} edges={graph.edges} />
        ))}
      </div>

      {/* Stats */}
      <div className="mt-4 pt-4 border-t border-gray-200">
        <div className="grid grid-cols-3 gap-4 text-center">
          <div>
            <p className="text-2xl font-bold text-gray-900">
              {graph.nodes.length}
            </p>
            <p className="text-sm text-gray-600">Modules</p>
          </div>
          <div>
            <p className="text-2xl font-bold text-gray-900">
              {graph.edges?.length || 0}
            </p>
            <p className="text-sm text-gray-600">Dependencies</p>
          </div>
          <div>
            <p className="text-2xl font-bold text-gray-900">
              {graph.nodes.reduce((sum, n) => sum + n.fileCount, 0)}
            </p>
            <p className="text-sm text-gray-600">Total Files</p>
          </div>
        </div>
      </div>
    </div>
  );
}

interface ModuleNodeProps {
  node: ModuleGraphType["nodes"][0];
  edges: ModuleGraphType["edges"];
}

function ModuleNode({ node, edges }: ModuleNodeProps): JSX.Element {
  const dependencies = edges.filter((e) => e.source === node.id);
  const dependents = edges.filter((e) => e.target === node.id);

  const activityColor = {
    active: "bg-kioku-success",
    recent: "bg-kioku-warning",
    stale: "bg-gray-400",
  }[node.activity];

  const activityText = {
    active: "Active",
    recent: "Recent",
    stale: "Stale",
  }[node.activity];

  return (
    <div className="border border-gray-200 rounded-lg p-4 hover:bg-gray-50 transition-colors">
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <div className={`w-3 h-3 rounded-full ${activityColor}`}></div>
          <div>
            <p className="font-medium text-gray-900">{node.name}</p>
            <p className="text-sm text-gray-600 font-mono">{node.path}</p>
          </div>
        </div>

        <div className="flex items-center space-x-4 text-sm">
          <span className="text-gray-600">{node.fileCount} files</span>
          <span
            className={`px-2 py-1 rounded text-xs font-medium ${activityColor} text-white`}
          >
            {activityText}
          </span>
        </div>
      </div>

      {/* Dependencies Info */}
      {(dependencies.length > 0 || dependents.length > 0) && (
        <div className="mt-3 pt-3 border-t border-gray-200 flex items-center space-x-4 text-sm text-gray-600">
          {dependencies.length > 0 && (
            <span>→ Depends on {dependencies.length} module(s)</span>
          )}
          {dependents.length > 0 && (
            <span>← Used by {dependents.length} module(s)</span>
          )}
        </div>
      )}
    </div>
  );
}

function ActivityLegend(): JSX.Element {
  return (
    <div className="flex items-center space-x-3 text-xs">
      <div className="flex items-center space-x-1">
        <div className="w-2 h-2 rounded-full bg-kioku-success"></div>
        <span className="text-gray-600">Active</span>
      </div>
      <div className="flex items-center space-x-1">
        <div className="w-2 h-2 rounded-full bg-kioku-warning"></div>
        <span className="text-gray-600">Recent</span>
      </div>
      <div className="flex items-center space-x-1">
        <div className="w-2 h-2 rounded-full bg-gray-400"></div>
        <span className="text-gray-600">Stale</span>
      </div>
    </div>
  );
}
