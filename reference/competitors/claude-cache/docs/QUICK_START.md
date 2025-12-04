# 🚀 Claude Cache Quick Start

Get your personal coding intelligence up and running in under 2 minutes!

## Prerequisites

- Python 3.8+
- Claude Code (VS Code with Claude extension or Cursor)
- You've used Claude Code at least once before

## Installation

### 1. Basic Install (Most Users)

```bash
pip install claude-cache
```

### 2. Enhanced Install (Semantic Search)

```bash
pip install "claude-cache[enhanced]"
```

*Includes ML-powered semantic search for 2x better pattern matching*

### 3. Full Install (With MCP Integration)

```bash
pip install "claude-cache[mcp]"
```

*Includes native Claude Code integration via MCP*

## First Run

### Step 1: Start Claude Cache

Choose your mode:

**Option A: Real-time Learning (Recommended)**
```bash
cache start --watch
```
- Processes existing history once
- Continuously monitors for new Claude Code sessions
- Learns patterns automatically in real-time
- Runs in background while you code

**Option B: One-time Processing**
```bash
cache start
```
- Processes existing history once
- Exits after processing (no real-time monitoring)
- Use this for initial setup or manual processing
- Run again manually when you want to update patterns

You'll see:

```
✓ Knowledge base initialized at ~/.claude/knowledge/cache.db
Processing 47 existing log files...
  Processing: YourProject/session1.jsonl
  Processing: YourApp/session2.jsonl
  ...
✓ Learned 23 patterns from your history
Starting real-time monitoring...
```

**What's happening?**
- Claude Cache found all your past Claude Code sessions
- It's analyzing your historical coding patterns
- Learning from your successes AND failures
- Building your personal knowledge base

**Which Mode Should I Use?**

🌟 **Use `cache start --watch` if you:**
- Want Claude Cache to learn automatically while you code
- Plan to keep coding with Claude Code regularly
- Want the most seamless experience
- Like background processes that "just work"

📝 **Use `cache start` if you:**
- Want manual control over when patterns are updated
- Are doing a one-time analysis of existing code
- Have limited system resources
- Prefer running processes on-demand

### Step 2: Let It Learn (One-Time)

The first run processes all your history. This takes:
- **< 10 sessions**: ~30 seconds
- **10-50 sessions**: 1-2 minutes
- **50-200 sessions**: 3-5 minutes
- **200+ sessions**: 5-10 minutes

After this initial processing, it runs in real-time with zero lag.

### 🤖 New in v0.9.0: Intelligent Detection

Claude Cache now uses **truly intelligent pattern detection** that understands your conversations:

- **Behavioral Understanding**: Detects success when Claude says "done" and you move to the next task
- **Multi-Signal Analysis**: Combines conversation flow, test results, user intent, and behavior
- **Auto-Save**: Automatically saves high-confidence patterns without interrupting your workflow
- **Context Awareness**: Knows if you're exploring vs implementing solutions

**What This Means**: Instead of saying "Perfect!" to save patterns, Claude Cache now understands when something works by analyzing your behavior and conversation context.

### Step 3: Start Coding!

Just use Claude Code normally. Claude Cache now:
- ✅ Watches your coding sessions in real-time
- ✅ Learns from successful solutions
- ✅ Captures what doesn't work
- ✅ Builds journey patterns automatically

## Using Claude Cache

### Interactive Monitoring

Monitor and interact with Claude Cache in real-time:

```bash
# Start interactive monitoring dashboard
cache monitor
```

**Interactive Commands (while monitoring):**
- **`h`** - Help system with comprehensive usage guide
- **`t`** - Interactive tutorial (perfect for new users)
- **`q`** - Quick guidance on querying patterns
- **`s`** - Show live statistics
- **`w`** - Learn how to mark successes
- **`f`** - Learn how to mark failures
- **`p`** - Project switching guidance
- **`ESC`** - Exit monitoring

### Query Your Knowledge

```bash
# Search for patterns
cache query "authentication"

# Get suggestions for current work
cache suggest

# See what you've learned
cache stats

# NEW v0.9.0: Analyze sessions with intelligent detection
cache analyze --recent              # Analyze most recent session
cache analyze --project myapp       # Analyze sessions from project
```

### Example Output

```bash
$ cache query "auth redirect"

🔍 Found 3 relevant patterns:

1. ✅ Success Pattern (React)
   "useEffect cleanup prevents auth redirect loops"
   Project: YourApp | Confidence: 92%

2. 🚫 Anti-Pattern
   "Don't store auth tokens in localStorage"
   Failed in: YourApp, AnotherApp | Alternative: Use httpOnly cookies

3. 🗺️ Journey Pattern
   "Auth loop fix: localStorage ❌ → cookies ❌ → useEffect ✅"
   Time saved next time: ~45 minutes
```

### Manual Learning

When you solve something particularly clever:

```bash
cache learn "Fixed auth by using httpOnly cookies with SameSite=strict"
```

## MCP Integration (Optional)

For seamless Claude Code integration, add to your `.claude.json`:

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

Now you can use these intelligent MCP tools directly in Claude Code:
- `cache_query("topic")` - Intelligent pattern search with behavioral context
- `cache_suggest()` - Proactive suggestions based on conversation analysis
- `cache_analyze()` - Real-time analysis of current session
- `cache_save()` - Smart pattern saving with quality classification
- `cache_stats()` - Knowledge base intelligence dashboard
- `/cache learn [solution]` - Save a pattern

## Background Mode

Run Claude Cache as a background service:

```bash
# Start in background
cache background

# Stop background service
cache stop
```

## What Gets Captured?

### ✅ Automatically Captured:
- Solutions that work (you say "thanks", "perfect", "works")
- Approaches that fail (errors occur, you say "broken", "failed")
- Complete problem→solution journeys
- Patterns that repeat across projects

### ❌ Not Captured:
- Every single edit or keystroke
- Low-confidence patterns
- Project-specific hacks
- Trial-and-error noise

## Privacy & Data

- **100% Local**: All data stays on your machine
- **Your patterns**: Never shared or uploaded
- **No telemetry**: We don't track your usage
- **SQLite database**: Located at `~/.claude/knowledge/cache.db`
- **You control everything**: Export, delete, or modify anytime

## Common Patterns You'll See

After a few days, Claude Cache will recognize patterns like:

```python
# 🏆 Gold Pattern (worked first time)
"useState in event handlers causes stale closures - use useRef"

# 🚫 Anti-Pattern (confirmed failure)
"fs.readFileSync in Next.js API routes causes build failures"

# 🗺️ Journey Pattern (the path to solution)
"CORS error → tried proxy ❌ → tried headers ❌ → configured server ✅"

# ⚠️ Caution Pattern (works but risky)
"Force unwrap in TypeScript bypasses error but hides type issues"
```

## Tips for Best Results

1. **Be expressive**: Say "perfect!", "that worked", "failed", etc.
2. **Let it run**: Keep Claude Cache running during coding sessions
3. **Trust the patterns**: When it says "don't do X", it learned that from YOUR experience
4. **Review periodically**: Run `cache stats` to see what you've learned

## Next Steps

- 📖 Read the [Philosophy](PHILOSOPHY.md) to understand dual-path learning
- 🔧 Check [Configuration](CONFIGURATION.md) for advanced options
- 🧠 Learn [How It Works](HOW_IT_WORKS.md) for technical details
- 💡 See [Use Cases](USE_CASES.md) for real-world examples

## Quick Reference

### Essential Commands
```bash
cache start --watch            # Real-time background learning (recommended)
cache start                    # One-time processing (no monitoring)
cache monitor                  # Interactive monitoring dashboard
cache query "search term"      # Find relevant patterns
cache stats                    # See what you've learned
cache suggest                  # Get contextual suggestions
```

### Interactive Monitoring Hotkeys
When running `cache monitor`, press:
- **`h`** → Full help system
- **`t`** → Interactive tutorial
- **`q`** → Query guidance
- **`s`** → Live statistics
- **`w`** → Mark success guidance
- **`f`** → Mark failure guidance
- **`p`** → Project switching
- **`ESC`** → Exit

### Active Learning
```bash
cache win                      # Mark current work successful
cache fail "reason"            # Learn from failures
cache learn "solution" --tags  # Manual pattern saving
```

## Troubleshooting

### No patterns found?
- Make sure you've used Claude Code before
- Check `~/.claude/projects/` exists
- Run `cache process` to manually process logs

### Not detecting new patterns?
- Ensure Claude Cache is running (`cache start`)
- Be explicit about success/failure ("works!", "failed")
- Check you're in a git repository

### Need help?
```bash
cache --help
```

---

**Ready to never repeat the same mistake twice?** You're all set! Claude Cache is now building your personal coding intelligence. 🎉