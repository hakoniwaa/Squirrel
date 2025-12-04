# Kioku Dashboard Setup Guide - With Tailwind CSS

## 🎨 Tech Stack

**Frontend:**
- ⚛️ React 18 + TypeScript
- 🎨 **Tailwind CSS** (utility-first styling)
- ⚡ Vite (fast dev server + build)
- 📊 Recharts (charts/graphs)
- 🌐 D3.js (interactive module graph)
- 🔄 TanStack Query (data fetching + caching)

**Backend:**
- 🚀 Fastify (REST API)
- 📦 Existing Kioku infrastructure

---

## 📦 Installation Steps

### Step 1: Create Dashboard Directory

```bash
cd /Users/sovanaryththorng/sanzoku_labs/kioku
mkdir dashboard
cd dashboard
```

### Step 2: Initialize React + Vite + TypeScript

```bash
# Create Vite React TypeScript project
npm create vite@latest . -- --template react-ts

# Answer prompts:
# ✓ Package name: kioku-dashboard
# ✓ Select a framework: React
# ✓ Select a variant: TypeScript
```

### Step 3: Install Tailwind CSS

```bash
# Install Tailwind and dependencies
npm install -D tailwindcss postcss autoprefixer

# Initialize Tailwind config
npx tailwindcss init -p
```

This creates:
- `tailwind.config.js`
- `postcss.config.js`

### Step 4: Configure Tailwind

**Edit `tailwind.config.js`:**
```javascript
/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Kioku brand colors
        'kioku-primary': '#6366f1',    // Indigo
        'kioku-secondary': '#8b5cf6',  // Purple
        'kioku-success': '#10b981',    // Green
        'kioku-warning': '#f59e0b',    // Amber
        'kioku-danger': '#ef4444',     // Red
        'kioku-dark': '#1f2937',       // Gray-800
        'kioku-light': '#f9fafb',      // Gray-50
      },
      animation: {
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
      }
    },
  },
  plugins: [],
}
```

### Step 5: Add Tailwind to CSS

**Edit `src/index.css`:**
```css
@tailwind base;
@tailwind components;
@tailwind utilities;

/* Custom scrollbar */
@layer utilities {
  .scrollbar-thin::-webkit-scrollbar {
    width: 6px;
    height: 6px;
  }
  
  .scrollbar-thin::-webkit-scrollbar-track {
    @apply bg-gray-100;
  }
  
  .scrollbar-thin::-webkit-scrollbar-thumb {
    @apply bg-gray-300 rounded-full;
  }
  
  .scrollbar-thin::-webkit-scrollbar-thumb:hover {
    @apply bg-gray-400;
  }
}

/* Glass morphism effect */
.glass {
  @apply bg-white/80 backdrop-blur-md border border-gray-200/50;
}

/* Card hover effect */
.card-hover {
  @apply transition-all duration-300 hover:shadow-lg hover:-translate-y-1;
}
```

### Step 6: Install Additional Dependencies

```bash
# Charts and graphs
npm install recharts d3 @types/d3

# Data fetching
npm install @tanstack/react-query axios

# Icons
npm install lucide-react

# Utilities
npm install clsx tailwind-merge

# Date formatting
npm install date-fns
```

### Step 7: Project Structure

```
dashboard/
├── package.json
├── vite.config.ts
├── tailwind.config.js
├── postcss.config.js
├── tsconfig.json
├── index.html
├── public/
│   └── favicon.ico
└── src/
    ├── main.tsx                    # Entry point
    ├── App.tsx                     # Main app component
    ├── index.css                   # Tailwind imports
    │
    ├── components/                 # React components
    │   ├── ProjectOverview.tsx     # Project stats card
    │   ├── SessionTimeline.tsx     # Session history
    │   ├── ModuleGraph.tsx         # D3 dependency graph
    │   ├── EmbeddingsStats.tsx     # Embeddings charts
    │   ├── ContextGauge.tsx        # Context window meter
    │   ├── ServicesStatus.tsx      # Service health
    │   ├── LinkedProjects.tsx      # Multi-project view
    │   └── ui/                     # Reusable UI components
    │       ├── Card.tsx
    │       ├── Badge.tsx
    │       ├── Progress.tsx
    │       └── Spinner.tsx
    │
    ├── services/                   # API layer
    │   ├── api-client.ts           # Axios instance
    │   └── queries.ts              # TanStack Query hooks
    │
    ├── types/                      # TypeScript types
    │   └── api.ts                  # API response types
    │
    └── utils/                      # Helper functions
        ├── cn.ts                   # Tailwind class merger
        └── formatters.ts           # Date/number formatters
```

---

## 🎨 Tailwind CSS Usage Examples

### 1. **Card Component** (Reusable UI)

```tsx
// src/components/ui/Card.tsx
import { cn } from '@/utils/cn';

interface CardProps {
  children: React.ReactNode;
  className?: string;
  hover?: boolean;
}

export function Card({ children, className, hover = false }: CardProps) {
  return (
    <div
      className={cn(
        'rounded-lg border border-gray-200 bg-white p-6 shadow-sm',
        hover && 'card-hover',
        className
      )}
    >
      {children}
    </div>
  );
}
```

### 2. **Project Overview** (Using Tailwind)

```tsx
// src/components/ProjectOverview.tsx
import { Card } from './ui/Card';
import { Folder, Code, Database, Activity } from 'lucide-react';

interface ProjectData {
  name: string;
  type: string;
  techStack: string[];
  moduleCount: number;
  fileCount: number;
  databaseSize: string;
  activeSession: boolean;
}

export function ProjectOverview({ data }: { data: ProjectData }) {
  return (
    <Card className="glass">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
          <Folder className="w-6 h-6 text-kioku-primary" />
          {data.name}
        </h2>
        {data.activeSession && (
          <span className="flex items-center gap-2 px-3 py-1 bg-green-100 text-green-700 rounded-full text-sm font-medium">
            <Activity className="w-4 h-4 animate-pulse" />
            Active
          </span>
        )}
      </div>

      <div className="flex flex-wrap gap-2 mb-4">
        {data.techStack.map((tech) => (
          <span
            key={tech}
            className="px-2 py-1 bg-kioku-primary/10 text-kioku-primary rounded-md text-xs font-medium"
          >
            {tech}
          </span>
        ))}
      </div>

      <div className="grid grid-cols-3 gap-4">
        <div className="flex flex-col">
          <span className="text-gray-500 text-sm">Modules</span>
          <span className="text-2xl font-bold text-gray-900 flex items-center gap-2">
            <Code className="w-5 h-5 text-kioku-secondary" />
            {data.moduleCount}
          </span>
        </div>

        <div className="flex flex-col">
          <span className="text-gray-500 text-sm">Files</span>
          <span className="text-2xl font-bold text-gray-900">
            {data.fileCount.toLocaleString()}
          </span>
        </div>

        <div className="flex flex-col">
          <span className="text-gray-500 text-sm">Database</span>
          <span className="text-2xl font-bold text-gray-900 flex items-center gap-2">
            <Database className="w-5 h-5 text-blue-500" />
            {data.databaseSize}
          </span>
        </div>
      </div>
    </Card>
  );
}
```

### 3. **Context Gauge** (Circular Progress)

```tsx
// src/components/ContextGauge.tsx
import { Card } from './ui/Card';
import { cn } from '@/utils/cn';

interface ContextGaugeProps {
  current: number;
  max: number;
}

export function ContextGauge({ current, max }: ContextGaugeProps) {
  const percentage = (current / max) * 100;
  
  const getColor = () => {
    if (percentage < 70) return 'text-green-500';
    if (percentage < 90) return 'text-amber-500';
    return 'text-red-500';
  };

  const getBgColor = () => {
    if (percentage < 70) return 'bg-green-500';
    if (percentage < 90) return 'bg-amber-500';
    return 'bg-red-500';
  };

  return (
    <Card>
      <h3 className="text-lg font-semibold text-gray-900 mb-4">
        Context Window Usage
      </h3>

      <div className="flex flex-col items-center">
        {/* Circular progress */}
        <div className="relative w-40 h-40">
          <svg className="w-40 h-40 transform -rotate-90">
            {/* Background circle */}
            <circle
              cx="80"
              cy="80"
              r="70"
              stroke="currentColor"
              strokeWidth="12"
              fill="none"
              className="text-gray-200"
            />
            {/* Progress circle */}
            <circle
              cx="80"
              cy="80"
              r="70"
              stroke="currentColor"
              strokeWidth="12"
              fill="none"
              strokeDasharray={`${2 * Math.PI * 70}`}
              strokeDashoffset={`${2 * Math.PI * 70 * (1 - percentage / 100)}`}
              className={cn('transition-all duration-500', getBgColor())}
              strokeLinecap="round"
            />
          </svg>
          
          {/* Center text */}
          <div className="absolute inset-0 flex flex-col items-center justify-center">
            <span className={cn('text-4xl font-bold', getColor())}>
              {percentage.toFixed(0)}%
            </span>
            <span className="text-sm text-gray-500 mt-1">
              {current.toLocaleString()} / {max.toLocaleString()}
            </span>
          </div>
        </div>

        {/* Status message */}
        <div className="mt-4 text-center">
          {percentage < 70 && (
            <p className="text-sm text-green-600 font-medium">
              ✓ Healthy - Plenty of space
            </p>
          )}
          {percentage >= 70 && percentage < 90 && (
            <p className="text-sm text-amber-600 font-medium">
              ⚠ Warning - Approaching limit
            </p>
          )}
          {percentage >= 90 && (
            <p className="text-sm text-red-600 font-medium">
              🚨 Critical - Pruning will activate
            </p>
          )}
        </div>
      </div>
    </Card>
  );
}
```

### 4. **Session Timeline** (List with hover effects)

```tsx
// src/components/SessionTimeline.tsx
import { Card } from './ui/Card';
import { Clock, FileText, Lightbulb } from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';
import { useState } from 'react';

interface Session {
  id: string;
  startTime: Date;
  duration: number;
  filesCount: number;
  discoveriesCount: number;
  files?: string[];
  topics?: string[];
}

export function SessionTimeline({ sessions }: { sessions: Session[] }) {
  const [expandedId, setExpandedId] = useState<string | null>(null);

  return (
    <Card className="scrollbar-thin max-h-96 overflow-y-auto">
      <h3 className="text-lg font-semibold text-gray-900 mb-4">
        Session Timeline
      </h3>

      <div className="space-y-3">
        {sessions.map((session) => {
          const isExpanded = expandedId === session.id;

          return (
            <div
              key={session.id}
              className={cn(
                'border rounded-lg p-4 cursor-pointer transition-all',
                isExpanded
                  ? 'border-kioku-primary bg-kioku-primary/5'
                  : 'border-gray-200 hover:border-kioku-primary/50 hover:bg-gray-50'
              )}
              onClick={() => setExpandedId(isExpanded ? null : session.id)}
            >
              {/* Header */}
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Clock className="w-4 h-4 text-gray-400" />
                  <span className="text-sm font-medium text-gray-900">
                    {formatDistanceToNow(session.startTime, { addSuffix: true })}
                  </span>
                  <span className="text-sm text-gray-500">
                    ({session.duration} min)
                  </span>
                </div>

                <div className="flex items-center gap-4">
                  <span className="flex items-center gap-1 text-sm text-gray-600">
                    <FileText className="w-4 h-4" />
                    {session.filesCount}
                  </span>
                  {session.discoveriesCount > 0 && (
                    <span className="flex items-center gap-1 text-sm text-kioku-primary">
                      <Lightbulb className="w-4 h-4" />
                      {session.discoveriesCount}
                    </span>
                  )}
                </div>
              </div>

              {/* Expanded details */}
              {isExpanded && session.files && (
                <div className="mt-4 pt-4 border-t border-gray-200">
                  <h4 className="text-sm font-medium text-gray-700 mb-2">
                    Files Accessed:
                  </h4>
                  <div className="space-y-1">
                    {session.files.slice(0, 5).map((file) => (
                      <div
                        key={file}
                        className="text-sm text-gray-600 pl-2 border-l-2 border-gray-300"
                      >
                        {file}
                      </div>
                    ))}
                  </div>

                  {session.topics && session.topics.length > 0 && (
                    <>
                      <h4 className="text-sm font-medium text-gray-700 mt-3 mb-2">
                        Topics:
                      </h4>
                      <div className="flex flex-wrap gap-2">
                        {session.topics.map((topic) => (
                          <span
                            key={topic}
                            className="px-2 py-1 bg-gray-100 text-gray-700 rounded text-xs"
                          >
                            {topic}
                          </span>
                        ))}
                      </div>
                    </>
                  )}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </Card>
  );
}
```

### 5. **Services Status** (Status indicators)

```tsx
// src/components/ServicesStatus.tsx
import { Card } from './ui/Card';
import { Activity, Eye, Zap, Clock, Settings } from 'lucide-react';
import { cn } from '@/utils/cn';

interface Service {
  name: string;
  status: 'running' | 'stopped' | 'error';
  details?: string;
  icon: typeof Activity;
}

export function ServicesStatus({ services }: { services: Service[] }) {
  return (
    <Card>
      <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
        <Settings className="w-5 h-5" />
        Background Services
      </h3>

      <div className="space-y-3">
        {services.map((service) => (
          <div
            key={service.name}
            className="flex items-center justify-between p-3 rounded-lg bg-gray-50"
          >
            <div className="flex items-center gap-3">
              <service.icon className="w-5 h-5 text-gray-400" />
              <span className="font-medium text-gray-900">{service.name}</span>
            </div>

            <div className="flex items-center gap-2">
              {service.details && (
                <span className="text-sm text-gray-500">{service.details}</span>
              )}
              
              <span
                className={cn(
                  'flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium',
                  service.status === 'running' &&
                    'bg-green-100 text-green-700',
                  service.status === 'stopped' &&
                    'bg-gray-100 text-gray-700',
                  service.status === 'error' && 'bg-red-100 text-red-700'
                )}
              >
                <span
                  className={cn(
                    'w-2 h-2 rounded-full',
                    service.status === 'running' && 'bg-green-500 animate-pulse',
                    service.status === 'stopped' && 'bg-gray-400',
                    service.status === 'error' && 'bg-red-500'
                  )}
                />
                {service.status}
              </span>
            </div>
          </div>
        ))}
      </div>
    </Card>
  );
}
```

---

## 🛠️ Utility Function

**Create `src/utils/cn.ts`:**
```typescript
import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

/**
 * Merge Tailwind classes intelligently
 * Handles conflicts (e.g., "text-red-500 text-blue-500" → "text-blue-500")
 */
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}
```

---

## 🎨 Color Palette

**Kioku Brand Colors (Tailwind Extended):**

```typescript
// In tailwind.config.js
colors: {
  'kioku-primary': '#6366f1',    // Indigo-500 (main brand)
  'kioku-secondary': '#8b5cf6',  // Violet-500 (accents)
  'kioku-success': '#10b981',    // Emerald-500 (success states)
  'kioku-warning': '#f59e0b',    // Amber-500 (warnings)
  'kioku-danger': '#ef4444',     // Red-500 (errors)
  'kioku-dark': '#1f2937',       // Gray-800 (dark text)
  'kioku-light': '#f9fafb',      // Gray-50 (light background)
}
```

**Usage:**
```tsx
<div className="bg-kioku-primary text-white">Primary Button</div>
<div className="text-kioku-success">Success Message</div>
<div className="border-kioku-warning">Warning Box</div>
```

---

## 🚀 Running the Dashboard

**Development:**
```bash
cd dashboard
npm run dev
# Opens at http://localhost:5173 (Vite default)
```

**Build for Production:**
```bash
npm run build
# Creates dashboard/dist/ folder
```

**Preview Production Build:**
```bash
npm run preview
```

---

## 📐 Responsive Design

Tailwind makes responsive design easy:

```tsx
<div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
  {/* 1 column on mobile, 2 on tablet, 3 on desktop */}
  <Card>...</Card>
  <Card>...</Card>
  <Card>...</Card>
</div>

<h1 className="text-xl md:text-2xl lg:text-3xl">
  {/* Responsive text sizes */}
  Kioku Dashboard
</h1>

<div className="hidden md:block">
  {/* Show only on tablet+ */}
  Advanced Stats
</div>
```

---

## ✅ Benefits of Tailwind CSS

1. **No CSS files needed** - All styling inline with components
2. **Fast development** - No context switching to CSS files
3. **Consistent design** - Predefined spacing/colors
4. **Responsive built-in** - `md:` `lg:` prefixes
5. **Purge unused CSS** - Production builds are tiny (< 10KB)
6. **Hover/focus states easy** - `hover:` `focus:` prefixes
7. **Dark mode ready** - `dark:` prefix (if needed later)

---

## 📦 Complete `package.json` for Dashboard

```json
{
  "name": "kioku-dashboard",
  "version": "1.0.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "tsc && vite build",
    "preview": "vite preview"
  },
  "dependencies": {
    "react": "^18.3.1",
    "react-dom": "^18.3.1",
    "recharts": "^2.15.0",
    "d3": "^7.10.0",
    "@tanstack/react-query": "^5.59.0",
    "axios": "^1.7.9",
    "lucide-react": "^0.468.0",
    "date-fns": "^4.1.0",
    "clsx": "^2.1.1",
    "tailwind-merge": "^2.6.0"
  },
  "devDependencies": {
    "@types/react": "^18.3.3",
    "@types/react-dom": "^18.3.0",
    "@types/d3": "^7.4.3",
    "@vitejs/plugin-react": "^4.3.1",
    "typescript": "^5.5.3",
    "vite": "^5.4.1",
    "tailwindcss": "^3.4.1",
    "postcss": "^8.4.35",
    "autoprefixer": "^10.4.17"
  }
}
```

---

## 🎯 Next Steps

1. ✅ Tailwind CSS added to tech stack
2. ⏳ Create dashboard directory structure
3. ⏳ Install all dependencies
4. ⏳ Set up Tailwind config
5. ⏳ Build UI components with Tailwind
6. ⏳ Connect to Kioku REST API

**Ready to start building?** 🚀
