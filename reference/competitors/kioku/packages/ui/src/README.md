# Kioku Dashboard

Visual context monitoring and inspection for the Kioku MCP server.

## 🚀 Quick Start

### Prerequisites

- Node.js 18+ or Bun
- Kioku server running on `localhost:9090`

### Installation

```bash
cd dashboard
bun install
```

### Development

```bash
# Start dev server (opens at http://localhost:3456)
bun run dev

# Run type checking
bun run type-check

# Run linter
bun run lint

# Run quality gate (type-check + lint)
bun run quality-gate
```

### Production Build

```bash
# Build for production
bun run build

# Preview production build
bun run preview
```

## 📁 Project Structure

```
dashboard/
├── src/
│   ├── components/          # React components
│   │   ├── ui/              # Reusable UI components
│   │   ├── ProjectOverview.tsx
│   │   ├── SessionTimeline.tsx
│   │   ├── ModuleGraph.tsx
│   │   ├── EmbeddingsStats.tsx
│   │   ├── ContextGauge.tsx
│   │   └── ServicesStatus.tsx
│   │
│   ├── services/            # API layer
│   │   ├── api-client.ts    # Axios instance
│   │   └── queries.ts       # TanStack Query hooks
│   │
│   ├── types/               # TypeScript types
│   │   └── api.ts           # API response types
│   │
│   ├── utils/               # Helper functions
│   │   └── cn.ts            # Tailwind class merger
│   │
│   ├── App.tsx              # Main app component
│   ├── main.tsx             # Entry point
│   └── index.css            # Tailwind + custom styles
│
├── public/                  # Static assets
├── index.html               # HTML entry point
├── vite.config.ts           # Vite configuration
├── tsconfig.json            # TypeScript config (strict mode)
├── eslint.config.mjs        # ESLint config (matching main project)
├── tailwind.config.js       # Tailwind CSS config
├── postcss.config.js        # PostCSS config
└── package.json             # Dependencies
```

## 🎨 Tech Stack

### Core
- **React 18** - UI framework
- **TypeScript** - Type safety (strict mode matching main project)
- **Vite** - Fast dev server and build tool

### Styling
- **Tailwind CSS** - Utility-first CSS framework
- **Lucide React** - Beautiful icon library

### Data Fetching
- **TanStack Query** - Server state management with caching
- **Axios** - HTTP client

### Visualization
- **Recharts** - Chart library
- **D3.js** - Interactive graph visualizations

### Code Quality
- **ESLint** - Linting (strict rules matching main project)
- **TypeScript** - Type checking (strict mode)

## 🔧 Configuration

### TypeScript

Strict type checking enabled (matching main project standards):
- `strict: true`
- `noImplicitAny: true`
- `strictNullChecks: true`
- `noUnusedLocals: true`
- `noUnusedParameters: true`
- `noUncheckedIndexedAccess: true`

### ESLint

Strict linting enabled (matching main project standards):
- TypeScript recommended + strict + stylistic rules
- React Hooks rules (exhaustive-deps)
- Explicit function return types required
- No `any` types allowed
- Consistent type imports

### Tailwind CSS

Custom Kioku brand colors configured:
- `kioku-primary`: #6366f1 (Indigo)
- `kioku-secondary`: #8b5cf6 (Violet)
- `kioku-success`: #10b981 (Emerald)
- `kioku-warning`: #f59e0b (Amber)
- `kioku-danger`: #ef4444 (Red)

Glass morphism utilities included.

### Vite

Development server on port `3456` with:
- Auto-open browser
- API proxy to `localhost:9090`
- Fast HMR (Hot Module Replacement)

## 📡 API Integration

The dashboard communicates with the Kioku server via REST API:

```typescript
// API endpoints (proxied through Vite dev server)
GET /api/project         // Project overview
GET /api/sessions        // Session list
GET /api/sessions/:id    // Session details
GET /api/modules         // Module dependency graph
GET /api/embeddings      // Embeddings statistics
GET /api/context         // Context window usage
GET /api/health          // Service health status
GET /api/linked-projects // Multi-project info
```

All API calls use TanStack Query for:
- Automatic caching
- Background refetching
- Loading/error states
- Optimistic updates

## 🎯 Quality Gates

Before committing code, run:

```bash
bun run quality-gate
```

This runs:
1. TypeScript type checking (`tsc --noEmit`)
2. ESLint linting (`eslint .`)

Both must pass with zero errors.

## 🌐 Environment

### Development
- Dashboard: `http://localhost:3456`
- API (proxied): `http://localhost:9090/api/*`

### Production
- Build output: `dashboard/dist/`
- Served by Kioku server (future implementation)

## 🎨 Component Guidelines

### File Naming
- Components: PascalCase (e.g., `ProjectOverview.tsx`)
- Utilities: camelCase (e.g., `cn.ts`)
- Types: PascalCase (e.g., `api.ts` with PascalCase interfaces)

### Component Structure
```tsx
import type { ComponentProps } from './types';
import { cn } from '@utils/cn';

interface Props {
  // Props definition
}

export function ComponentName({ prop }: Props): JSX.Element {
  return (
    <div className={cn('base-classes', 'conditional-classes')}>
      {/* Component content */}
    </div>
  );
}
```

### Styling with Tailwind
```tsx
// Use utility classes
<div className="flex items-center gap-2 px-4 py-2 bg-white rounded-lg shadow-sm">

// Use custom Kioku colors
<div className="bg-kioku-primary text-white">

// Use responsive classes
<div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3">

// Use hover states
<button className="hover:bg-gray-100 transition-colors">
```

### State Management
```tsx
// Use TanStack Query for server state
const { data, isLoading, error } = useQuery({
  queryKey: ['project'],
  queryFn: fetchProject,
});

// Use React state for UI state
const [isOpen, setIsOpen] = useState(false);
```

## 📝 Development Workflow

1. **Create feature branch**
   ```bash
   git checkout -b feature/dashboard-component
   ```

2. **Develop with type safety**
   ```bash
   bun run dev  # Start dev server
   # Edit components with TypeScript checking
   ```

3. **Run quality checks**
   ```bash
   bun run quality-gate  # Must pass
   ```

4. **Build and test**
   ```bash
   bun run build
   bun run preview
   ```

5. **Commit and push**
   ```bash
   git add .
   git commit -m "feat(dashboard): add component"
   git push origin feature/dashboard-component
   ```

## 🐛 Troubleshooting

### Port already in use
```bash
# Vite will try next available port (3457, 3458, etc.)
# Or specify a different port:
vite --port 3500
```

### TypeScript errors
```bash
# Check types
bun run type-check

# Common issues:
# - Missing return type annotations
# - Implicit 'any' types
# - Unsafe array/object access
```

### ESLint errors
```bash
# Check lint
bun run lint

# Auto-fix
bun run lint:fix

# Common issues:
# - Missing explicit return types
# - Unused variables
# - React hooks dependencies
```

### API connection issues
```bash
# Ensure Kioku server is running
cd ..
bun run dev  # Start Kioku server on port 9090

# Check Vite proxy config in vite.config.ts
```

## 🚧 Current Status

**Phase 10: Under Construction**

### ✅ Completed
- Project structure
- TypeScript configuration (strict mode)
- ESLint configuration (matching main project)
- Tailwind CSS setup with Kioku colors
- Vite configuration with proxy
- API types definition
- Utility functions
- Basic App skeleton

### 🔄 In Progress
- UI components
- API integration
- Data fetching hooks
- Real-time polling

### ⏳ TODO
- REST API endpoints (backend)
- Dashboard CLI command
- Production deployment
- Documentation

## 📚 Resources

- [React Documentation](https://react.dev/)
- [Vite Documentation](https://vitejs.dev/)
- [Tailwind CSS](https://tailwindcss.com/)
- [TanStack Query](https://tanstack.com/query)
- [Recharts](https://recharts.org/)
- [D3.js](https://d3js.org/)

## 📄 License

Same as main Kioku project.
