# 🧠 How Claude Cache Works

**A comprehensive guide to understanding and using Claude Cache effectively**

## Table of Contents
1. [Core Concept](#core-concept)
2. [Architecture Overview](#architecture-overview)
3. [Installation & Setup](#installation--setup)
4. [The Learning Engine](#the-learning-engine)
5. [Search Technologies](#search-technologies)
6. [MCP Tools Deep Dive](#mcp-tools-deep-dive)
7. [CLI Mastery](#cli-mastery)
8. [Knowledge Organization](#knowledge-organization)
9. [Optimization Strategies](#optimization-strategies)
10. [Advanced Patterns](#advanced-patterns)
11. [Troubleshooting](#troubleshooting)

---

## Core Concept

Claude Cache transforms every coding session into permanent knowledge through **dual-path learning** - capturing both what works AND what doesn't work. It's like giving your AI assistant a perfect memory that learns from your complete journey.

### The Revolutionary Approach
- **Traditional tools**: Only save successful code snippets
- **Claude Cache**: Learns from successes, failures, and the journey between them

### Why Dual-Path Learning Matters

Consider this real scenario:
```
Monday: Debug authentication for 2 hours
  - Try localStorage (fails - security risk)
  - Try sessionStorage (fails - doesn't persist)
  - Try cookies (fails - CORS issues)
  - Try httpOnly cookies (SUCCESS!)

Friday: Hit similar auth issue
```

**Without Claude Cache**: You might try localStorage again
**With Claude Cache**:
- ⚠️ "Don't use localStorage for auth tokens (security risk)"
- 🚫 "SessionStorage won't persist across tabs"
- ✅ "Use httpOnly cookies with SameSite=strict"
- 🗺️ "Journey: localStorage → sessionStorage → cookies → httpOnly ✓"

### Five Pillars of Intelligence (v0.9.0)

1. **🤖 Multi-Signal Detection** - Combines conversation flow, execution results, user intent, and behavioral patterns
2. **🧠 Behavioral Understanding** - Detects implicit success when "AI says done + user moves on"
3. **⚡ Auto-Save Intelligence** - Automatically saves high-confidence patterns without interrupting workflow
4. **🎯 Context Awareness** - Knows if you're exploring vs implementing vs testing
5. **📊 Quality Classification** - GOLD/SILVER/BRONZE/ANTI with confidence levels

### Privacy & Security

**Everything stays on your machine**:
- **No cloud storage** - All data stored locally in `~/.claude/`
- **No external API calls** - Works completely offline
- **No tracking or telemetry** - Your code and patterns stay private
- **No data sharing** - Each project's knowledge is isolated
- **You own your data** - Simple SQLite database you can inspect, export, or delete

---

## Architecture Overview

```
┌─────────────────────────────────────────────────┐
│                  Claude Code                     │
│  ┌───────────────────────────────────────────┐  │
│  │         MCP Tools (/mcp__cache__)          │  │
│  │    Telemetry Logs (~/.claude/projects/)    │  │
│  └────────────────┬──────────────────────────┘  │
└───────────────────┼──────────────────────────────┘
                    │
        ┌───────────▼──────────────┐
        │   FastMCP Server (stdio)  │
        └───────────┬───────────────┘
                    │
    ┌───────────────▼────────────────────┐
    │    🤖 Intelligent Learning Engine   │
    │  ┌─────────────────────────────┐   │
    │  │  🧠 IntelligentDetector      │   │
    │  │   ├─ Conversation Analyzer  │   │
    │  │   ├─ Execution Monitor      │   │
    │  │   ├─ Intent Detector        │   │
    │  │   └─ Behavioral Analyzer    │   │
    │  │  ⚡ Multi-Signal Fusion     │   │
    │  │  🎯 Pattern Classifier      │   │
    │  │  💾 Auto-Save Engine        │   │
    │  └─────────────────────────────┘   │
    └────────────────────────────────────┘
                    │
    ┌───────────────▼────────────────────┐
    │         Knowledge Base              │
    │  ┌─────────────────────────────┐   │
    │  │  SQLite Database            │   │
    │  │  - Success Patterns (Gold+) │   │
    │  │  - Anti-Patterns (Don'ts)   │   │
    │  │  - Journey Patterns (Paths) │   │
    │  │  - Cross-Project Intel      │   │
    │  └─────────────────────────────┘   │
    └────────────────────────────────────┘
                    │
    ┌───────────────▼────────────────────┐
    │      Intelligent Search             │
    │  ┌─────────────────────────────┐   │
    │  │  Semantic Understanding     │   │
    │  │  Pattern Matching           │   │
    │  │  Context Awareness          │   │
    │  └─────────────────────────────┘   │
    └────────────────────────────────────┘
```

### Key Components

1. **MCP Server** - Native integration with Claude Code via stdio transport
2. **Knowledge Base** - SQLite storage with pattern relationships
3. **Search Engine** - Hybrid semantic + keyword search
4. **Learning System** - Multi-signal pattern detection
5. **Project Isolation** - Separate knowledge per project with global patterns

---

## Installation & Setup

### Choose Your Power Level

#### 🔧 Basic Mode - Simple & Reliable
```bash
pip install claude-cache

# Start background learning
cache background

# Or foreground monitoring
cache start --watch
```
- TF-IDF keyword search
- All CLI commands
- Background process options
- Pattern learning
- Works everywhere

#### ⚡ Enhanced Mode - Semantic Intelligence
```bash
pip install "claude-cache[enhanced]"

# Start with full system
cache run

# Or background only
cache background
```
- Everything in Basic +
- Semantic vector search (2x better accuracy)
- Enhanced pattern intelligence
- Context understanding
- ML-powered suggestions

#### 🚀 MCP Mode - Ultimate Experience
```bash
pip install "claude-cache[mcp]"
```

Then add to `.claude.json`:
```json
{
  "mcpServers": {
    "cache": {
      "type": "stdio",
      "command": "cache-mcp"
    }
  }
}
```
- Everything in Enhanced +
- Native Claude Code tools
- Zero context switching
- Proactive suggestions
- Real-time pattern access

### First-Time Setup Optimization

```bash
# 1. Install with all features
pip install "claude-cache[mcp]"

# 2. Configure Claude Code (create .claude.json)
echo '{
  "mcpServers": {
    "cache": {
      "type": "stdio",
      "command": "cache-mcp"
    }
  }
}' > .claude.json

# 3. Restart Claude Code

# 4. Verify tools are available
# Type "/" in Claude Code - should see:
# /mcp__cache__query
# /mcp__cache__learn
# etc.
```

---

## The Dual-Path Learning Engine

### How Claude Cache Learns from Everything

#### 1. Success Pattern Detection
Identifies and classifies successful solutions:

**🏆 Gold Patterns** (Worked first time):
- "Perfect!"
- "That worked immediately!"
- Clean, elegant solutions
- High confidence (95%+)

**🥈 Silver Patterns** (Worked after 2-3 attempts):
- "Good, that fixed it"
- Required minor adjustments
- Moderate confidence (80-95%)

**🥉 Bronze Patterns** (Eventually worked):
- "Finally got it working"
- Multiple attempts needed
- Lower confidence (60-80%)

#### 2. Anti-Pattern Detection
Learns from failures to prevent repetition:

**🚫 Confirmed Failures**:
- "That didn't work"
- "Failed with error"
- "This approach is broken"
- Stores WHY it failed
- Suggests alternatives

**Example Anti-Pattern**:
```python
# DETECTED: localStorage for auth tokens
Problem: "Storing JWT in localStorage"
Why Failed: "XSS vulnerability - accessible to any script"
Alternative: "Use httpOnly cookies with SameSite=strict"
Projects Failed In: ["app1", "app2", "app3"]
Confidence: 95% (failed consistently)
```

#### 3. Journey Pattern Tracking
Captures complete problem-solving sequences:

**🗺️ Complete Journeys**:
```python
# Journey: Fix Authentication Loop
Attempt 1: Check localStorage → Failed (not the issue)
Attempt 2: Debug cookies → Failed (cookies were fine)
Attempt 3: Check redirect logic → Failed (logic was correct)
Attempt 4: Add useEffect cleanup → SUCCESS!

Key Learning: "Auth loops often caused by missing cleanup"
Time Saved Next Time: ~45 minutes
Pattern Type: JOURNEY
```

#### 4. Pattern Classification System

| Type | Symbol | When Captured | Confidence |
|------|--------|--------------|------------|
| **Gold** | 🏆 | Immediate success | 95-100% |
| **Silver** | 🥈 | 2-3 attempts | 80-95% |
| **Bronze** | 🥉 | 4+ attempts | 60-80% |
| **Anti-Pattern** | 🚫 | Confirmed failure | 90-100% |
| **Journey** | 🗺️ | Complete sequence | 85-100% |
| **Caution** | ⚠️ | Works with caveats | 70-85% |

#### 5. Failure Signal Detection

**Explicit Failure Signals**:
- "That broke"
- "Doesn't work"
- "Failed"
- "Error occurred"
- "This is wrong"

**Implicit Failure Signals**:
- Error messages in output
- Test failures
- Build failures
- Type errors
- Runtime exceptions

#### 6. Context-Aware Learning

```python
# Same problem, different contexts
Context: "React 18"
Solution: "useEffect with cleanup"

Context: "Vue 3"
Solution: "onBeforeUnmount hook"

Context: "Angular"
Solution: "ngOnDestroy lifecycle"

# Claude Cache maintains context for accurate retrieval
```

### Processing Claude Code Telemetry

Claude Cache reads telemetry logs from `~/.claude/projects/` to learn:

#### What Gets Extracted:
```python
# From each log entry:
- User messages (requests, feedback)
- Tool calls (Read, Edit, Write, Bash)
- Assistant responses and reasoning
- Error messages and resolutions
- Success indicators
- Project context (cwd field)
- Complete conversation flow
```

#### Historical Processing (First Run):
```bash
cache start
# Output:
✓ Found 184 Claude Code session logs
✓ Processing: project1/session1.jsonl
✓ Processing: project2/session2.jsonl
...
✓ Extracted 523 patterns from history
  - 234 Success patterns
  - 89 Anti-patterns
  - 67 Journey patterns
  - 133 Contextual solutions
```

#### Real-Time Monitoring:
```python
# Watches for new entries in logs
# Processes incrementally (no re-processing)
# Zero lag - patterns available immediately
# Maintains file position tracking
```

### Manual Pattern Capture

#### Via Natural Language (Best)
Simply express success or failure:
- "Perfect! That worked!"
- "This failed, let me try something else"
- "Great solution, thanks!"
- Claude Cache captures automatically

#### Via MCP Tools
```
/mcp__cache__learn
solution: "Fixed auth with httpOnly cookies"
context: "Was using localStorage (XSS risk)"
tags: "auth,security,cookies"
```

#### Via CLI
```bash
# Save a success
cache learn "JWT with httpOnly cookies" \
  --tags "auth,jwt,security" \
  --confidence 95

# Record an anti-pattern
cache learn-anti "Never use eval() for JSON" \
  --reason "Security vulnerability" \
  --alternative "Use JSON.parse()"
```

---

## Search Technologies

### Semantic Search (Enhanced/MCP Modes)

Uses `sentence-transformers` with `all-MiniLM-L6-v2` model:

```python
# How it works internally:
1. Query: "auth broken"
2. Embedding: [0.23, -0.45, 0.67, ...] (384 dimensions)
3. Similarity search against pattern embeddings
4. Returns: JWT issues, OAuth problems, session errors
```

**Semantic Understanding Examples**:
- "slow db" → finds: query optimization, connection pooling, indexing
- "test fail" → finds: mock setup, async testing, fixture issues
- "memory leak" → finds: cleanup patterns, garbage collection, profiling

### TF-IDF Search (All Modes)

Keyword matching with term frequency weighting:

```python
# How it works:
1. Query: "authentication JWT"
2. Tokenization: ["authentication", "jwt"]
3. TF-IDF scoring against pattern corpus
4. Returns: Patterns with highest keyword relevance
```

**Best Practices**:
- Use specific terms: "JWT refresh token" vs "auth"
- Include technology: "React useState hook" vs "state"
- Add context: "PostgreSQL connection pool" vs "database"

### Hybrid Search Strategy

```python
# Claude Cache automatically chooses:
if sentence_transformers_available:
    results = semantic_search(query)
    if len(results) < min_threshold:
        results += tfidf_search(query)
else:
    results = tfidf_search(query)
```

---

## MCP Tools Deep Dive

### `/mcp__cache__query`

**Purpose**: Instant pattern search with semantic understanding

**Parameters**:
- `query` (required): What to search for
- `limit` (optional): Max results (default: 5)

**Advanced Usage**:
```
# Simple query
/mcp__cache__query "authentication"

# With limit
/mcp__cache__query
query: "database optimization"
limit: 10

# Complex semantic query
/mcp__cache__query "slow API response times"
# Finds: caching, query optimization, connection pooling
```

**Returns**:
- Pattern content
- Similarity score
- Project origin
- Timestamp
- Related patterns

### `/mcp__cache__learn`

**Purpose**: Save successful solutions permanently

**Parameters**:
- `solution` (required): What worked
- `context` (optional): Additional context
- `tags` (optional): Comma-separated tags
- `project_name` (optional): Project association

**Strategic Usage**:
```
# After fixing a bug
/mcp__cache__learn
solution: "Fixed CORS by adding proxy middleware"
context: "Next.js API routes with external API"
tags: "cors,api,middleware,nextjs"

# After optimizing performance
/mcp__cache__learn
solution: "Reduced load time with React.lazy"
context: "Large component tree causing slow initial load"
tags: "performance,react,lazy-loading"
```

### `/mcp__cache__suggest`

**Purpose**: Proactive pattern recommendations

**Parameters**:
- `context` (optional): Current work context

**Power User Tips**:
```
# Before starting work
/mcp__cache__suggest
context: "Building user dashboard with real-time updates"
# Returns: WebSocket patterns, state management, polling strategies

# When stuck
/mcp__cache__suggest
context: "TypeError: Cannot read property 'map' of undefined"
# Returns: Null checking patterns, optional chaining, defensive coding
```

### `/mcp__cache__stats`

**Purpose**: Knowledge base analytics

**Returns**:
- Total patterns
- Search capabilities
- Project breakdown
- Recent activity
- Top categories

**Using Stats Strategically**:
```
/mcp__cache__stats
# Check if you have patterns for current work
# See which projects have most knowledge
# Identify knowledge gaps
```

### `/mcp__cache__browse`

**Purpose**: Index documentation instantly

**Parameters**:
- `url` (required): Documentation URL
- `project_name` (optional): Project association

**Documentation Mining**:
```
# Index API docs
/mcp__cache__browse
url: "https://docs.stripe.com/api"
project_name: "payment-system"

# Index team knowledge
/mcp__cache__browse
url: "https://wiki.company.com/engineering"

# Index GitHub README
/mcp__cache__browse
url: "https://github.com/facebook/react/blob/main/README.md"
```

---

## CLI Mastery

### Background Monitoring

#### 🚀 Recommended: Simple Background Process
```bash
# Best for most users
cache background

# Check if running
ps aux | grep cache

# View logs
tail -f /tmp/claude-cache.log

# Stop
pkill -f 'cache start'
```

#### ⚙️ Enhanced: Full System
```bash
# Background learning + terminal interface
cache run

# Background with MCP server
cache run --with-mcp

# Foreground mode
cache run --foreground
```

#### 🔄 Advanced: Session Management
```bash
# Using tmux (recommended for power users)
tmux new -s cache -d "cache start --watch"
tmux attach -t cache  # View logs
tmux detach  # Ctrl+B, then D

# Using screen
screen -S cache -d -m cache start --watch
screen -r cache  # Reattach

# Using nohup (simple background)
nohup cache start --watch > cache.log 2>&1 &
```

#### 🏃 One-Time Processing
```bash
# Process existing logs only (no monitoring)
cache process

# Check what was learned
cache stats
```

**📚 Complete setup guide**: See [docs/TERMINAL_SETUP.md](TERMINAL_SETUP.md) for all options.
```

### Advanced Queries

```bash
# Search with context
cache query "authentication" --limit 10

# Project-specific search
cache query "database" --project "my-app"

# Export patterns
cache export --format json > patterns.json

# Import team patterns
cache import patterns.json
```

### Batch Operations

```bash
# Index multiple docs
for url in $(cat docs.txt); do
  cache browse "$url"
done

# Learn from commit messages
git log --oneline | while read commit; do
  cache learn "$commit" --tags "git,history"
done
```

---

## Knowledge Organization

### Enhanced Database Structure

```
~/.claude/
├── knowledge/
│   ├── cache.db                 # Global knowledge base
│   │   ├── patterns            # Success patterns
│   │   ├── anti_patterns       # What doesn't work
│   │   ├── journey_patterns    # Complete paths
│   │   ├── cross_project       # Shared intelligence
│   │   └── pattern_metrics     # Efficiency tracking
│   └── project_my-app.db       # Project-specific
├── projects/                    # Claude Code telemetry
│   ├── project1/
│   │   └── *.jsonl             # Session logs
│   └── project2/
│       └── *.jsonl
├── lessons/                     # Organized learnings
│   ├── authentication_lessons.md
│   ├── database_lessons.md
│   └── api_lessons.md
└── state/
    └── processor_state.json    # Incremental processing
```

### Pattern Storage Schema

```sql
-- Success Patterns
CREATE TABLE patterns (
    id INTEGER PRIMARY KEY,
    content TEXT,           -- What worked
    context TEXT,           -- When/why it worked
    pattern_type TEXT,      -- gold/silver/bronze
    confidence REAL,        -- 0.0 to 1.0
    success_count INTEGER,  -- Times it worked
    project_name TEXT,
    created_at TIMESTAMP
);

-- Anti-Patterns (NEW)
CREATE TABLE anti_patterns (
    id INTEGER PRIMARY KEY,
    pattern TEXT,           -- What doesn't work
    reason TEXT,            -- Why it fails
    alternatives TEXT,      -- What to do instead
    failure_count INTEGER,  -- Times it failed
    projects_failed TEXT,   -- Where it failed
    confidence REAL,
    created_at TIMESTAMP
);

-- Journey Patterns (NEW)
CREATE TABLE journey_patterns (
    id INTEGER PRIMARY KEY,
    problem TEXT,           -- Initial problem
    attempts TEXT,          -- JSON array of attempts
    solution TEXT,          -- Final solution
    key_learning TEXT,      -- Critical insight
    time_saved INTEGER,     -- Minutes saved next time
    pattern_quality TEXT,   -- gold/silver/bronze
    created_at TIMESTAMP
);
```

### CLAUDE.md Generation

Claude Cache automatically maintains `.claude/CLAUDE.md` in your projects:

```markdown
# Claude Code Knowledge Base - my-app

## Recent Patterns
1. JWT refresh token implementation
2. PostgreSQL connection pooling
3. React performance optimization

## Warnings
- Always validate JWT signatures
- Connection pool size affects memory

## Best Practices
- Use environment variables for secrets
- Implement request rate limiting
```

### Category System

Patterns auto-categorize into:
- `authentication` - Auth flows, JWT, OAuth
- `database` - Queries, connections, migrations
- `api` - REST, GraphQL, webhooks
- `performance` - Optimization, caching
- `testing` - Unit tests, mocks, fixtures
- `deployment` - CI/CD, Docker, cloud
- `debugging` - Error handling, logging

---

## Optimization Strategies

### 1. Maximize Learning Quality

```bash
# Process all historical Claude Code sessions
cache start
# Processes ~/.claude/projects/ automatically

# Be expressive about outcomes
"Perfect!"        # Saves as gold pattern
"That failed"     # Saves as anti-pattern
"Finally works"   # Saves as journey pattern

# Import existing documentation
cache browse https://your-docs.com
```

### 2. Optimize Search Performance

```python
# Use specific queries
Good: "React useEffect cleanup memory leak"
Bad: "React problem"

# Combine with context
/mcp__cache__suggest
context: "const [data, setData] = useState();"

# Tag strategically
/mcp__cache__learn
tags: "react,hooks,state,typescript"
```

### 3. Project-Specific Intelligence

```bash
# Configure per-project
cd my-project
echo "PROJECT_NAME=my-app" > .env

# Separate patterns by technology
cache learn "Vue 3 Composition API" --project "vue-app"
cache learn "React hooks pattern" --project "react-app"
```

### 4. Team Knowledge Sharing

```bash
# Export team knowledge
cache export --shared-only > team-patterns.json

# Import on new machine
cache import team-patterns.json

# Sync via git
git add .claude/lessons/
git commit -m "Share team patterns"
```

---

## Advanced Patterns

### Learning from Failures

```python
# Anti-pattern prevention
/mcp__cache__query "authentication storage"
# Returns:
# 🚫 "Don't use localStorage (XSS risk)"
# 🚫 "Avoid sessionStorage (doesn't persist)"
# ✅ "Use httpOnly cookies"

# Journey replay
/mcp__cache__query "fixing render loops"
# Returns:
# 🗺️ "Journey: deps array → useCallback → useMemo → SUCCESS"
# Time saved: ~30 minutes
```

### Pattern Quality Analysis

```python
# See pattern classification
cache stats --by-quality
# Output:
# 🏆 Gold patterns: 45 (worked first time)
# 🥈 Silver patterns: 67 (2-3 attempts)
# 🥉 Bronze patterns: 23 (4+ attempts)
# 🚫 Anti-patterns: 89 (confirmed failures)
# 🗺️ Journey patterns: 34 (complete paths)
# ⚠️ Caution patterns: 12 (works with caveats)
```

### Pattern Chaining

```python
# Build on patterns avoiding past failures
1. /mcp__cache__query "API setup"
2. Check anti-patterns for common mistakes
3. /mcp__cache__query "auth anti-patterns"
4. Build solution avoiding known pitfalls
5. /mcp__cache__learn "Bulletproof authenticated API"
```

### Context Injection

```python
# Pre-load relevant patterns
/mcp__cache__query "testing strategies"
# Now Claude has testing context for your session

# Build on loaded context
"Implement the unit test pattern for my UserService"
```

### Differential Analysis

```bash
# Compare approaches
cache query "state management" --compare
# Shows: Redux (45min) vs Zustand (15min) vs Context (10min)

# Learn from comparisons
cache learn "Zustand for simple state" --metric "time:15min"
```

### Cross-Project Learning

```python
# Find transferable patterns
/mcp__cache__query "authentication"
# Returns patterns from ALL projects

# Apply to current project
"Adapt the JWT pattern from project-a to this Next.js app"
```

---

## Troubleshooting

### MCP Tools Not Appearing

```bash
# 1. Check installation
pip show claude-cache
# Should show: Version: 0.6.1 or higher

# 2. Test MCP server
cache-mcp
# Should start without errors

# 3. Verify .claude.json
cat .claude.json
# Must have mcpServers configuration

# 4. Restart Claude Code completely
# Quit and reopen (not just reload)

# 5. Check Claude Code logs
# Help menu → Diagnostic logs
```

### Search Not Finding Patterns

```bash
# 1. Check pattern count
cache stats
# Should show patterns > 0

# 2. Test search directly
cache query "test"
# Should return results

# 3. Verify search mode
cache query "test" --verbose
# Shows: "Search mode: semantic" or "keyword"

# 4. Rebuild search index
cache rebuild-index
```

### Patterns Not Being Captured

```bash
# 1. Check monitoring is active
cache status
# Should show: "Monitoring active"

# 2. Verify Claude Code log access
ls ~/.claude/projects/
# Should have .jsonl files

# 3. Check incremental processing
cache status --verbose
# Shows: "Last processed position: byte 45678"

# 4. Test detection
cache test-detection "Perfect! That worked!"
# Should show: "Success pattern detected"

cache test-detection "That failed completely"
# Should show: "Anti-pattern detected"

# 5. Force reprocessing if needed
cache process --force
```

### Performance Issues

```bash
# 1. Check database size
du -h ~/.claude/knowledge/cache.db

# 2. Vacuum database
cache optimize

# 3. Limit search results
/mcp__cache__query
query: "pattern"
limit: 3

# 4. Disable semantic search if needed
export CLAUDE_CACHE_SEMANTIC=false
cache start
```

---

## Best Practices Checklist

### Daily Workflow
- [ ] Start Claude Cache when you begin coding
- [ ] Express outcomes clearly ("works!", "failed", "perfect!")
- [ ] Use `/mcp__cache__suggest` before implementing features
- [ ] Check anti-patterns before trying solutions
- [ ] Query journey patterns when stuck

### Weekly Maintenance
- [ ] Review stats with `/mcp__cache__stats`
- [ ] Index new documentation with `/mcp__cache__browse`
- [ ] Export important patterns for backup
- [ ] Clean up duplicate patterns

### Project Setup
- [ ] Add `.claude.json` to each project
- [ ] Configure project-specific patterns
- [ ] Import relevant team patterns
- [ ] Document project-specific conventions

### Team Collaboration
- [ ] Share `.claude.json` configuration
- [ ] Export and commit lesson files
- [ ] Document pattern usage
- [ ] Regular knowledge sync sessions

---

## Performance Metrics

### What to Expect

**Query Performance**:
- Keyword search: <50ms
- Semantic search: <200ms
- 10,000 patterns: <100ms
- 100,000 patterns: <500ms

**Learning Performance**:
- Pattern detection: Real-time
- Index update: <1 second
- Database write: <100ms

**Memory Usage**:
- Base: ~50MB
- With semantic model: ~200MB
- Per 1000 patterns: ~5MB

**Accuracy**:
- Keyword matching: 40-60%
- Semantic matching: 60-90%
- With context: 80-95%

---

## The Power User's Workflow

### Morning Routine
```bash
# 1. Start dual-path learning
cache start --watch
# Processes historical logs + monitors real-time

# 2. Check what was learned overnight
cache stats --recent
# Shows: New patterns, anti-patterns, journeys

# 3. Review anti-patterns to avoid
cache query --anti-patterns --limit 5
# Shows: Top mistakes to avoid today
```

### Before Starting a Feature
```
# 1. Search existing patterns
/mcp__cache__query "similar feature"

# 2. Get suggestions
/mcp__cache__suggest
context: "building user authentication"

# 3. Learn from other projects
/mcp__cache__query "auth"
# Shows patterns from all projects
```

### After Solving a Problem
```
# 1. Express the outcome naturally
"Perfect! The useEffect cleanup fixed the race condition!"
# Automatically captured as gold pattern

# 2. If something didn't work
"localStorage approach failed - security issue"
# Automatically captured as anti-pattern

# 3. For complex journeys
"Finally got it working after trying 4 different approaches"
# Captured as journey pattern with all attempts
```

### End of Day
```bash
# 1. Review what was learned
cache stats --today

# 2. Export important patterns
cache export --today > $(date +%Y%m%d)-patterns.json

# 3. Sync with team
git add .claude/lessons/ && git commit -m "Daily patterns"
```

---

## Conclusion

Claude Cache revolutionizes AI coding assistance through dual-path learning:

1. **Dual-Path Intelligence** - Learns from successes AND failures
2. **Journey Patterns** - Captures complete problem-solving paths
3. **Anti-Pattern Prevention** - Never repeat the same mistake
4. **Pattern Classification** - Gold/Silver/Bronze quality scoring
5. **Automatic Learning** - Captures patterns from Claude Code telemetry
6. **Privacy First** - Everything stays local on your machine

The more you use Claude Cache, the smarter it becomes:
- Every success becomes a reusable pattern
- Every failure prevents future mistakes
- Every journey saves time next time

**Start immediately**: Just run `cache start`
**Express outcomes**: Say "perfect!" or "failed"
**Check anti-patterns**: Avoid past mistakes
**Follow journeys**: Skip to what works

Welcome to coding with complete intelligence - learning from everything, storing what matters.

*"The best developers aren't those who never fail, but those who learn from every failure and success alike."*

---

*For quick setup, see [QUICKSTART.md](QUICKSTART.md)*
*For installation options, see [INSTALLATION.md](INSTALLATION.md)*
*For MCP details, see [MCP_INTEGRATION.md](MCP_INTEGRATION.md)*