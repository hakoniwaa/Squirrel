import { Activity } from "lucide-react";
import { ProjectOverview } from "@components/ProjectOverview";
import { SessionTimeline } from "@components/SessionTimeline";
import { ModuleGraph } from "@components/ModuleGraph";
import { EmbeddingsStats } from "@components/EmbeddingsStats";

function App(): JSX.Element {
  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100">
      {/* Header */}
      <header className="glass sticky top-0 z-50 border-b border-gray-200/50">
        <div className="container mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-kioku-primary to-kioku-secondary flex items-center justify-center">
                <Activity className="w-6 h-6 text-white" />
              </div>
              <div>
                <h1 className="text-2xl font-bold text-gray-900">
                  Kioku Dashboard
                </h1>
                <p className="text-sm text-gray-500">
                  Real-time context monitoring
                </p>
              </div>
            </div>

            <div className="flex items-center gap-2">
              <span className="flex items-center gap-2 px-3 py-1.5 bg-green-100 text-green-700 rounded-full text-sm font-medium">
                <span className="w-2 h-2 rounded-full bg-green-500 animate-pulse" />
                Connected
              </span>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="container mx-auto px-6 py-8">
        <div className="space-y-8">
          {/* Project Overview */}
          <ProjectOverview />

          {/* Two Column Layout */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
            {/* Left Column: Sessions */}
            <SessionTimeline />

            {/* Right Column: Module Graph */}
            <ModuleGraph />
          </div>

          {/* Embeddings and Context Stats */}
          <EmbeddingsStats />
        </div>
      </main>

      {/* Footer */}
      <footer className="container mx-auto px-6 py-4 text-center text-sm text-gray-500">
        Kioku v2.0.0 - Context Management for AI Coding Assistants
      </footer>
    </div>
  );
}

export default App;
