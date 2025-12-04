# Claude Cache v0.9.0 - Example Usage

Claude Cache v0.9.0 offers three distinct usage modes with revolutionary intelligent detection. Here are practical examples for each.

---

## 🚀 MCP Mode Examples (Native Claude Code Integration)

### Installation
```bash
pip install claude-cache[mcp]

# Add to .claude.json:
{
  "mcpServers": {
    "claude-cache": {
      "type": "stdio",
      "command": "cache-mcp"
    }
  }
}

# Restart Claude Code
```

### Real Usage Examples

#### Authentication Implementation
```
# Working in Claude Code:
You: "I need to implement user authentication"

# Search for existing patterns first:
You: "/mcp__claude-cache__query user authentication"

# Claude shows:
🔍 Found 3 results for 'user authentication'

**1. 🧠 Pattern** (Score: 0.945)
📁 Project: my-api-project
📝 JWT implementation with refresh tokens and middleware validation

**2. 🧠 Pattern** (Score: 0.823)
📁 Project: dashboard-app
📝 OAuth integration with Google and GitHub providers

# Use the first pattern:
You: "Implement the JWT pattern from my-api-project"
Claude: *implements JWT auth using your proven pattern*

# When it works:
You: "/mcp__claude-cache__learn"
description: "JWT authentication working in new project"
category: "authentication"
code_snippet: "const authMiddleware = (req, res, next) => { ... }"

Claude: "✅ Pattern Saved Successfully!"
```

#### Proactive Development
```
# Starting a new feature:
You: "/mcp__claude-cache__suggest"
context: "Building a React dashboard with real-time data"
intent: "add WebSocket connections"

Claude: "💡 Based on your context, I found these relevant patterns:
- WebSocket setup with Socket.io (95% relevance) from analytics-dashboard
- Real-time chart updates (87% relevance) from monitoring-app
- Error handling for connections (79% relevance) from chat-app"

You: "Use the Socket.io pattern"
Claude: *implements WebSocket based on your successful previous implementation*
```

#### Documentation Indexing
```
# Index team documentation:
You: "/mcp__claude-cache__browse"
url: "https://docs.mycompany.com/api-standards"
project: "new-service"
doc_type: "standards"

Claude: "✅ Documentation Indexed Successfully!
📊 Extracted Content:
- Lessons: 23
- Best Practices: 12
- API Standards: 8

🔍 Auto-indexed for vector search - Now searchable with cache_query!"

# Later, when building APIs:
You: "/mcp__claude-cache__query API standards"
Claude: *finds your company's documented standards instantly*
```

#### Knowledge Base Stats
```
You: "/mcp__claude-cache__stats"

Claude: "📊 Claude Cache Statistics

🌍 Global Knowledge Base
- Total Patterns: 234
- Projects Tracked: 8
- Total Requests: 1,247

🔍 Search Engine
- Mode: Semantic Search ✨ (Enhanced)
- Model: all-MiniLM-L6-v2
- Indexed Items: 234

📁 Current Project: dashboard-v2

🚀 Knowledge Base Active:
- Use cache_suggest for proactive recommendations
- Try specific searches with cache_query"
```

---

## ⚡ Enhanced Mode Examples (CLI + Semantic Search)

### Installation
```bash
pip install claude-cache[enhanced]

# Start monitoring
cache start
```

### Usage Examples

#### Semantic Pattern Search
```bash
# Traditional keyword search limitations:
cache query "auth"  # Only finds exact "auth" mentions

# Enhanced semantic search finds related concepts:
cache query "auth bug"
# Finds: JWT validation issues, login failures, session problems

cache query "slow database"
# Finds: query optimization, connection pooling, indexing solutions

cache query "test failing"
# Finds: debugging patterns, mock setup, assertion fixes
```

#### Project Management
```bash
# Work on multiple projects seamlessly
cd ~/projects/e-commerce-api
cache query "payment processing"
# Shows patterns specific to e-commerce-api

cd ~/projects/mobile-app
cache query "payment processing"
# Shows patterns specific to mobile-app (different approaches)

# Cross-project insights
cache stats
# Shows global patterns across all projects
```

#### Documentation Integration
```bash
# Index external documentation
cache browse https://docs.stripe.com/payments
# Indexes Stripe payment docs for searchable knowledge

# Later, semantic search finds it:
cache query "payment methods"
# Returns both your patterns AND indexed Stripe documentation
```

---

## 🔧 Basic Mode Examples (CLI Only)

### Installation
```bash
pip install claude-cache

# Start monitoring
cache start
```

### Usage Examples

#### Keyword Pattern Search
```bash
# Find patterns with specific keywords
cache query "authentication"
# Returns patterns containing "authentication" keyword

cache query "database migration"
# Returns patterns about database migrations

# Project-specific search
cache query "API endpoint" --project my-service
```

#### Statistics and Monitoring
```bash
# Check overall progress
cache stats
# Shows: patterns learned, projects tracked, success rates

# Project-specific stats
cache stats --project my-app
# Shows patterns just for my-app

# Monitor learning in real-time
cache start
# Shows live updates as Claude Cache learns new patterns
```

#### Pattern Export/Import
```bash
# Backup your patterns
cache export my-patterns.json --project my-app

# Share with team
cache import team-patterns.json

# Process existing logs
cache process
# Analyzes all historical Claude Code sessions
```

---

## 🔄 Migration Examples

### Upgrading from Basic to Enhanced
```bash
# You're currently using Basic mode
cache query "auth bug"  # Limited keyword results

# Upgrade to Enhanced
pip install sentence-transformers

# Now same query finds semantic matches
cache query "auth bug"  # Finds JWT issues, login problems, etc.
```

### Upgrading to MCP Mode
```bash
# Add MCP support
pip install mcp

# Configure Claude Code
echo '{
  "mcpServers": {
    "claude-cache": {
      "type": "stdio",
      "command": "cache-mcp"
    }
  }
}' > .claude.json

# Restart Claude Code
# Now you have native tools available!
```

---

## 📊 Performance Comparison Examples

### Response Time Test
```bash
# Basic Mode
time cache query "authentication"
# ~0.3 seconds (keyword search)

# Enhanced Mode
time cache query "authentication"
# ~1.8 seconds (semantic search + better results)

# MCP Mode (in Claude Code)
/mcp__claude-cache__query authentication
# <0.1 seconds (native tool, no context switching)
```

### Accuracy Test
```bash
# Query: "login not working"

# Basic Mode Results:
# - Pattern 1: "user login implementation" (keyword match)
# - Pattern 2: "login form validation" (keyword match)

# Enhanced Mode Results:
# - Pattern 1: "JWT token expiration bug fix" (semantic match!)
# - Pattern 2: "Authentication middleware troubleshooting" (semantic match!)
# - Pattern 3: "Session timeout handling" (semantic match!)

# MCP Mode: Same Enhanced results + instant access in Claude Code
```

---

## 🎯 Real-World Workflow Examples

### Debugging Session (MCP Mode)
```
1. Bug appears in production
2. You: "/mcp__claude-cache__query similar error message"
3. Claude: Shows 3 previous similar bugs and their solutions
4. You apply the solution
5. You: "/mcp__claude-cache__learn production bug fixed with XYZ approach"
6. Next time: Instant resolution from patterns
```

### Feature Development (Enhanced Mode)
```bash
1. Start new feature: cache query "user dashboard"
2. Find relevant patterns from past projects
3. Implement using proven approaches
4. When successful, Claude Cache auto-learns from your session
5. Future dashboards: Built faster using learned patterns
```

### Team Knowledge Sharing (All Modes)
```bash
# Senior developer exports patterns
cache export senior-patterns.json

# Junior developer imports them
cache import senior-patterns.json

# MCP Mode: Instant access to senior patterns via native tools
# Enhanced/Basic: CLI access to proven solutions
```

---

## 💡 Pro Tips for Each Mode

### 🚀 MCP Mode Tips
- Use `/mcp__claude-cache__suggest` before starting any new feature
- Save patterns immediately with `/mcp__claude-cache__learn` when something works
- Index team documentation with `/mcp__claude-cache__browse`

### ⚡ Enhanced Mode Tips
- Use semantic queries: "performance issue" instead of "slow code"
- Let it run continuously to build semantic understanding
- Combine with Basic mode CLI for backup access

### 🔧 Basic Mode Tips
- Use specific keywords for better matches
- Give clear feedback ("Perfect!") to trigger learning
- Great for environments with limited dependencies

---

## 🎉 Success Stories

### Before Claude Cache
```
1. Encounter authentication bug
2. Google for solutions
3. Try various Stack Overflow answers
4. Spend 2 hours debugging
5. Finally fix it
6. Forget solution details
7. Repeat same process next time
```

### After Claude Cache (MCP Mode)
```
1. Encounter authentication bug
2. "/mcp__claude-cache__query auth bug"
3. See exactly how you fixed it before
4. Apply proven solution
5. Fixed in 10 minutes
6. "/mcp__claude-cache__learn" to reinforce pattern
7. Next time: Instant fix
```

**Result**: 90% faster debugging with proven solutions!

---

## 📚 Next Steps

1. **Choose your mode** based on your needs and environment
2. **Install** using the appropriate command
3. **Start learning** by using Claude Code normally
4. **Query patterns** when you need help
5. **Save successes** to build your knowledge base

**The more you use Claude Cache, the smarter Claude becomes for YOUR specific coding style and projects!**