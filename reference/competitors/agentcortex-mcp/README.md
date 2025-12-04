# AgentCortex MCP Client

[![NPM Version](https://img.shields.io/npm/v/agentcortex)](https://www.npmjs.com/package/agentcortex)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![GitHub Stars](https://img.shields.io/github/stars/sage-hq/agentcortex)](https://github.com/sage-hq/agentcortex)

> 🎯 **The only AI memory system that solves the context-switching problem**
> 
> Never lose context when jumping between projects. AgentCortex creates isolated, persistent memory banks for each codebase, so your AI assistant remembers everything—exactly where it belongs.

## 🔥 Why AgentCortex Changes Everything

**The Problem**: AI assistants forget everything between conversations. Worse, when you work on multiple projects, context bleeds between codebases—your React patterns from Project A contaminate your Vue.js work on Project B.

**The Solution**: **Project-isolated persistent memory**. Each project gets its own intelligent memory bank that grows smarter over time, never interfering with your other work.

## ✨ Core Features

### 🎯 **Project Context Separation** *(The Game Changer)*
- **Isolated memory banks** per project/codebase
- **Zero context bleeding** between different repos
- **Automatic project detection** and context switching
- **Clean slate** for each new project, **full memory** for existing ones

### 🧠 **Persistent Cross-Session Memory**
- **Never lose context** again across all conversations
- **Cumulative learning** that builds on every interaction
- **Semantic search** finds relevant memories instantly
- **Intelligent importance** ranking and auto-cleanup

### 📋 **AI-Powered Task Management** 
- **Break down complex PRDs** into actionable tasks
- **Smart task suggestions** based on project context
- **Progress tracking** with dependency management
- **Context-aware subtask generation**

### ⚡ **Enterprise Performance**
- **Sub-200ms response times** with optimized queries
- **Vector search** with 1536-dimensional embeddings
- **99.9% uptime SLA** with enterprise security
- **Scales infinitely** with your growing codebase

## 🚀 Quick Start

### 1. Get Your API Key
```bash
# Sign up at agentcortex.dev and grab your API key
curl -X POST https://api.agentcortex.dev/auth/signup \
  -H "Content-Type: application/json" \
  -d '{"email":"you@company.com"}'
```

### 2. Install & Configure
```bash
# Install globally
npm install -g agentcortex

# Or run directly
npx agentcortex
```

### 3. Add to Your AI Assistant

#### **Claude Desktop**
Add to your `claude_desktop_config.json` file:
```json
{
  "mcpServers": {
    "agentcortex": {
      "command": "npx",
      "args": ["agentcortex"],
      "env": {
        "AGENTCORTEX_API_KEY": "your_api_key_here"
      }
    }
  }
}
```

#### **Cursor IDE**
Add to Cursor Settings → MCP or your `cursor_settings.json`:
```json
{
  "mcp.servers": {
    "agentcortex": {
      "command": "npx",
      "args": ["agentcortex"],
      "env": {
        "AGENTCORTEX_API_KEY": "your_api_key_here"
      }
    }
  }
}
```

#### **Windsurf IDE**
Add to your Windsurf configuration file:
```json
{
  "mcp": {
    "servers": {
      "agentcortex": {
        "command": "npx",
        "args": ["agentcortex"],
        "env": {
          "AGENTCORTEX_API_KEY": "your_api_key_here"
        }
      }
    }
  }
}
```

#### **Claude Code (VS Code Extension)**
Add to your VS Code User Settings (JSON) or `.vscode/mcp.json`:
```json
{
  "mcp": {
    "servers": {
      "agentcortex": {
        "command": "npx",
        "args": ["agentcortex"],
        "env": {
          "AGENTCORTEX_API_KEY": "your_api_key_here"
        }
      }
    }
  }
}
```

## 💡 Real-World Usage Examples

### Project Context Isolation in Action

```bash
# Working on your React e-commerce app
Human: We're using React 18 with TypeScript and Zustand for state management
AI: ✅ Stored in TaskMem → Project: "ecommerce-frontend"

# Switch to your Python API project  
Human: Switch to my Python API project
AI: 🔄 Switched to "payment-api" project context

# Now working in Python context - React knowledge doesn't interfere
Human: What framework should I use for the API?
AI: 🔍 Based on your "payment-api" project: FastAPI with Pydantic for validation
    (No mention of React/TypeScript - clean context separation!)

# Back to React project later
Human: Switch back to ecommerce frontend
AI: 🔄 Switched to "ecommerce-frontend" 
    💭 Remembers: React 18, TypeScript, Zustand state management
```

### Semantic Memory That Actually Works

```bash
Human: What did we decide about error handling?
AI: 🔍 Found 3 relevant memories:
    
    1. [94% match] "Use React Error Boundaries for component failures"
    2. [89% match] "Log errors to Sentry in production"  
    3. [85% match] "Show user-friendly messages, never expose stack traces"
    
    All from your current project context.
```

### Intelligent Task Breakdown

```bash
Human: Break down the user authentication system implementation
AI: 📋 Task broken down into 6 subtasks:

    ✅ Research authentication patterns for React 18
    🔄 Set up Supabase Auth integration  
    ⏳ Implement login/signup forms
    ⏳ Add protected route middleware
    ⏳ Create user profile management
    ⏳ Add session persistence logic
    
    Estimated: 2-3 days based on your project complexity
```

## 🛠️ Complete Tool Reference

| Tool | What It Does | When To Use |
|------|-------------|-------------|
| **Project Management** |
| `create_project` | Create new isolated project context | Starting work on a new codebase |
| `set_current_project` | Switch between project contexts | Moving between different repos |
| `get_current_project` | Show active project info | Confirm which project you're in |
| `list_projects` | List all your project contexts | See all your codebases |
| `get_project_context` | Full project overview & summary | Get up to speed on a project |
| **Memory Operations** |
| `store_memory` | Save important project information | Record decisions, patterns, configs |
| `search_memory` | Find memories with semantic search | "What did we decide about...?" |
| `get_memories` | List memories with filtering | Browse project knowledge base |
| `update_memory_importance` | Adjust memory priority (1-10) | Boost critical information |
| **Task Management** |
| `create_task` | Add new task to project | Track feature work, bugs, tech debt |
| `list_tasks` | View tasks with status filtering | See what's pending/in progress |
| `update_task_status` | Change task progress | Mark tasks complete |
| `suggest_next_task` | AI-powered task recommendations | "What should I work on next?" |
| `break_down_task` | Split complex work into subtasks | Turn PRDs into actionable steps |

## 🎯 Advanced Usage Patterns

### Team Workflows

```bash
# Share project context with team members
Human: Export this project's memory for onboarding
AI: 📦 Generated onboarding package for "ecommerce-frontend"
    → Includes: Architecture decisions, coding standards, setup guides
    → Share with: new team members for instant context

# Import team knowledge
Human: Import the backend team's API documentation memories  
AI: ✅ Imported 47 memories from "payment-api" project
    → Now available when working on frontend integrations
```

### Cross-Project Insights

```bash
# Learn from patterns across projects
Human: What authentication patterns have I used before?
AI: 🔍 Across your projects:
    
    - ecommerce-frontend: Supabase Auth + React Context
    - admin-dashboard: Auth0 + JWT tokens  
    - mobile-app: Firebase Auth + AsyncStorage
    
    Recommendation: Supabase for consistency with your React patterns
```

## 🔧 Configuration

### Environment Variables

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `AGENTCORTEX_API_KEY` | Your API key from [agentcortex.dev](https://agentcortex.dev) | ✅ | - |
| `AGENTCORTEX_API_URL` | API endpoint override | ❌ | `https://api.agentcortex.dev` |
| `AGENTCORTEX_PROJECT_AUTO_DETECT` | Auto-detect project from git repo | ❌ | `true` |
| `AGENTCORTEX_DEFAULT_IMPORTANCE` | Default memory importance level | ❌ | `5` |

### Advanced Configuration

**Claude Desktop**:
```json
{
  "mcpServers": {
    "agentcortex": {
      "command": "npx",
      "args": ["agentcortex"],
      "env": {
        "AGENTCORTEX_API_KEY": "your_api_key",
        "AGENTCORTEX_PROJECT_AUTO_DETECT": "true",
        "AGENTCORTEX_DEFAULT_IMPORTANCE": "7"
      }
    }
  }
}
```

**Cursor/Windsurf/Claude Code**:
```json
{
  "mcp": {
    "servers": {
      "agentcortex": {
        "command": "npx",
        "args": ["agentcortex"],
        "env": {
          "AGENTCORTEX_API_KEY": "your_api_key",
          "AGENTCORTEX_PROJECT_AUTO_DETECT": "true",
          "AGENTCORTEX_DEFAULT_IMPORTANCE": "7"
        }
      }
    }
  }
}
```

## 🔐 Pricing

| Plan | Price | Projects | Memories/Month | Task Management | Support |
|------|-------|----------|----------------|-----------------|---------|
| **Developer** | **Free** | 1 project | 1,000 memories | Basic | Community |
| **Pro** | **$29/mo** | Unlimited | Unlimited | Advanced | Priority |
| **Team** | **$99/mo** | Unlimited | Unlimited | Collaboration | Dedicated |

**All plans include**:
- ✅ Project context separation
- ✅ Semantic search
- ✅ 99.9% uptime SLA
- ✅ Enterprise security
- ✅ MCP protocol support

## 🧪 Development & Contributing

```bash
# Clone and setup
git clone https://github.com/sage-hq/agentcortex.git
cd agentcortex/apps/mcp
npm install

# Development with hot reload
npm run dev

# Build for production  
npm run build

# Run tests
npm test

# Publish to npm
npm run publish
```

### Contributing Guidelines

1. **Fork** the repository
2. **Create** a feature branch: `git checkout -b feature/amazing-feature`
3. **Add tests** for new functionality
4. **Ensure** TypeScript types are correct
5. **Test** with multiple MCP clients
6. **Submit** a Pull Request

## 🤝 Community & Support

- 📖 **Documentation**: [docs.agentcortex.dev](https://docs.agentcortex.dev)
- 💬 **Discussions**: [GitHub Discussions](https://github.com/sage-hq/agentcortex/discussions)
- 🐛 **Bug Reports**: [GitHub Issues](https://github.com/sage-hq/agentcortex/issues)
- 🚀 **Feature Requests**: [Feature Board](https://agentcortex.dev/features)
- 📧 **Email Support**: support@agentcortex.dev

## 🏆 Why Developers Love AgentCortex

> *"Finally, an AI that doesn't forget my React patterns when I switch to my Python API project. Game changer."*  
> **— Sarah Chen, Senior Engineer @ Stripe**

> *"AgentCortex solved our biggest pain point: onboarding new developers. Now they get instant context on our 20+ microservices."*  
> **— Marcus Rodriguez, Tech Lead @ DataDog**

> *"The project isolation is incredible. My AI assistant actually knows the difference between my TypeScript and Go codebases."*  
> **— Alex Kim, Principal Engineer @ Vercel**

## 📈 Roadmap

- 🔄 **Auto-sync with Git**: Automatic project detection from repositories
- 🤖 **Code Analysis**: AI-powered codebase understanding and suggestions  
- 🔍 **Advanced Search**: Full-text search across code, docs, and conversations
- 🎯 **Smart Suggestions**: Proactive memory and task recommendations
- 🌐 **VS Code Extension**: Direct integration with popular editors
- 👥 **Team Collaboration**: Shared project contexts and knowledge bases

## 📝 License

MIT License - see [LICENSE](LICENSE) file for details.

---

**🚀 Ready to give your AI perfect memory?**

```bash
npx agentcortex
```

*Never lose context again. Start free today.*