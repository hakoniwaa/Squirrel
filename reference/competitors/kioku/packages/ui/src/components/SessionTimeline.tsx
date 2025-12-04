/**
 * SessionTimeline Component
 *
 * Displays a timeline of past sessions with click-to-expand details:
 * - Session start/end times
 * - Duration
 * - Files accessed
 * - Discoveries extracted
 * - Expandable to show full session details
 */

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { apiClient } from "../services/api-client";
import type { Session, SessionDetails } from "../types/api";
import { ChevronDown, ChevronRight, FileText, Lightbulb } from "lucide-react";

export function SessionTimeline(): JSX.Element {
  const {
    data: sessions,
    isLoading,
    error,
  } = useQuery<Session[]>({
    queryKey: ["sessions"],
    queryFn: () => apiClient.getSessions(10), // Get last 10 sessions
    refetchInterval: 5000, // Poll every 5 seconds
  });

  if (isLoading) {
    return (
      <div className="bg-white rounded-lg shadow-md p-6">
        <h2 className="text-xl font-bold text-gray-900 mb-4">
          Session Timeline
        </h2>
        <div className="space-y-4">
          {[1, 2, 3].map((i) => (
            <div key={i} className="animate-pulse">
              <div className="h-20 bg-gray-200 rounded"></div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-6">
        <p className="text-red-800 font-semibold">Failed to load sessions</p>
        <p className="text-red-600 text-sm mt-2">{String(error)}</p>
      </div>
    );
  }

  if (!sessions || sessions.length === 0) {
    return (
      <div className="bg-white rounded-lg shadow-md p-6">
        <h2 className="text-xl font-bold text-gray-900 mb-4">
          Session Timeline
        </h2>
        <div className="bg-gray-50 rounded-lg p-8 text-center">
          <p className="text-gray-600">No sessions yet</p>
          <p className="text-sm text-gray-500 mt-2">
            Sessions will appear here after you start using Kioku
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <h2 className="text-xl font-bold text-gray-900 mb-4">Session Timeline</h2>
      <div className="space-y-3">
        {Array.isArray(sessions) &&
          sessions.map((session) => (
            <SessionCard key={session.id} session={session} />
          ))}
      </div>
    </div>
  );
}

interface SessionCardProps {
  session: Session;
}

function SessionCard({ session }: SessionCardProps): JSX.Element {
  const [isExpanded, setIsExpanded] = useState(false);

  const { data: details, isLoading } = useQuery<SessionDetails>({
    queryKey: ["session", session.id],
    queryFn: () => apiClient.getSessionDetails(session.id),
    enabled: isExpanded, // Only fetch when expanded
  });

  const isActive = !session.endTime;

  return (
    <div className="border border-gray-200 rounded-lg overflow-hidden">
      {/* Session Summary (Always Visible) */}
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full px-4 py-3 flex items-center justify-between hover:bg-gray-50 transition-colors"
      >
        <div className="flex items-center space-x-3">
          {isExpanded ? (
            <ChevronDown className="w-5 h-5 text-gray-400" />
          ) : (
            <ChevronRight className="w-5 h-5 text-gray-400" />
          )}

          <div className="text-left">
            <div className="flex items-center space-x-2">
              <p className="font-medium text-gray-900">
                {formatSessionTime(session.startTime)}
              </p>
              {isActive && (
                <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-kioku-success text-white">
                  Active
                </span>
              )}
            </div>
            <p className="text-sm text-gray-600">
              Duration: {formatDuration(session.duration)}
            </p>
          </div>
        </div>

        <div className="flex items-center space-x-4 text-sm text-gray-600">
          <div className="flex items-center space-x-1">
            <FileText className="w-4 h-4" />
            <span>{session.filesCount} files</span>
          </div>
          <div className="flex items-center space-x-1">
            <Lightbulb className="w-4 h-4" />
            <span>{session.discoveriesCount} discoveries</span>
          </div>
        </div>
      </button>

      {/* Session Details (Expandable) */}
      {isExpanded && (
        <div className="px-4 pb-4 pt-2 bg-gray-50 border-t border-gray-200">
          {isLoading ? (
            <div className="animate-pulse space-y-2">
              <div className="h-4 bg-gray-200 rounded w-3/4"></div>
              <div className="h-4 bg-gray-200 rounded w-1/2"></div>
            </div>
          ) : details ? (
            <div className="space-y-4">
              {/* Session Info */}
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <p className="font-semibold text-gray-700">Session ID</p>
                  <p className="text-gray-600 font-mono text-xs">
                    {details.id}
                  </p>
                </div>
                <div>
                  <p className="font-semibold text-gray-700">Duration</p>
                  <p className="text-gray-600">
                    {formatDuration(details.duration)}
                  </p>
                </div>
              </div>

              {/* Topics */}
              {details.topics && details.topics.length > 0 && (
                <div>
                  <p className="font-semibold text-gray-700 text-sm mb-2">
                    Topics
                  </p>
                  <div className="flex flex-wrap gap-2">
                    {details.topics.map((topic) => (
                      <span
                        key={topic}
                        className="inline-flex items-center px-2 py-1 rounded text-xs font-medium bg-kioku-secondary text-white"
                      >
                        {topic}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {/* Files Accessed */}
              {details.files && details.files.length > 0 && (
                <div>
                  <p className="font-semibold text-gray-700 text-sm mb-2">
                    Files Accessed ({details.files.length})
                  </p>
                  <div className="bg-white rounded border border-gray-200 max-h-40 overflow-y-auto">
                    <ul className="divide-y divide-gray-200">
                      {details.files.slice(0, 10).map((file, idx) => (
                        <li
                          key={idx}
                          className="px-3 py-2 text-sm text-gray-700 font-mono"
                        >
                          {file}
                        </li>
                      ))}
                      {details.files.length > 10 && (
                        <li className="px-3 py-2 text-sm text-gray-500 italic">
                          ... and {details.files.length - 10} more files
                        </li>
                      )}
                    </ul>
                  </div>
                </div>
              )}

              {/* Discoveries */}
              {details.discoveries && details.discoveries.length > 0 && (
                <div>
                  <p className="font-semibold text-gray-700 text-sm mb-2">
                    Discoveries ({details.discoveries.length})
                  </p>
                  <div className="bg-white rounded border border-gray-200 max-h-40 overflow-y-auto">
                    <ul className="divide-y divide-gray-200">
                      {details.discoveries.slice(0, 5).map((discovery) => (
                        <li key={discovery.id} className="px-3 py-2">
                          <div className="flex items-start justify-between">
                            <div className="flex-1">
                              <p className="text-sm font-medium text-gray-900">
                                {discovery.type}
                              </p>
                              <p className="text-sm text-gray-600 mt-1">
                                {discovery.content}
                              </p>
                            </div>
                            <span className="ml-2 text-xs text-gray-500">
                              {Math.round(discovery.confidence * 100)}%
                            </span>
                          </div>
                        </li>
                      ))}
                      {details.discoveries.length > 5 && (
                        <li className="px-3 py-2 text-sm text-gray-500 italic">
                          ... and {details.discoveries.length - 5} more
                          discoveries
                        </li>
                      )}
                    </ul>
                  </div>
                </div>
              )}
            </div>
          ) : (
            <p className="text-sm text-gray-600">
              Failed to load session details
            </p>
          )}
        </div>
      )}
    </div>
  );
}

function formatSessionTime(timestamp: string): string {
  const date = new Date(timestamp);
  return date.toLocaleString("en-US", {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function formatDuration(minutes: number): string {
  if (minutes < 1) {
    return "< 1 min";
  } else if (minutes < 60) {
    return `${minutes} min`;
  } else {
    const hours = Math.floor(minutes / 60);
    const mins = minutes % 60;
    return mins > 0 ? `${hours}h ${mins}m` : `${hours}h`;
  }
}
