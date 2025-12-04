# 🚀 Claude Cache - Quick Start Guide

**Get perfect AI memory in 2 minutes**

Never solve the same problem twice. Claude Cache remembers every successful solution and provides instant access when you need it.

---

## 🎯 Choose Your Mode

### 🚀 MCP Mode (Recommended)
**Native Claude Code tools - the ultimate experience**
- 5 native tools accessible via `/mcp__cache__*`
- Zero context switching
- Instant pattern queries
- Proactive suggestions
- Real-time learning

### ⚡ Enhanced Mode
**CLI + semantic search - 2x better accuracy**
- All CLI commands
- Semantic vector search
- Context understanding
- Automatic fallback to keyword search

### 🔧 Basic Mode
**CLI only - works everywhere**
- Core CLI functionality
- TF-IDF keyword search
- CLAUDE.md generation
- No dependencies

---

## 🎯 Step 1: Choose and Install Your Mode

### 🚀 MCP Mode Installation (5 minutes)

**1. Install with MCP support:**
```bash
pip install claude-cache[mcp]
```

**2. Start Background Learning:**
```bash
# Recommended: Simple background process
cache background

# Alternative: Full system with enhanced features
cache run
```

**3. Start MCP Server (for Claude Code):**
```bash
cache-mcp
```

**4. Configure Claude Code** - Add to your project's `.claude.json`:
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

**5. Restart Claude Code**

**6. Test the tools:**
```
Type "/" in Claude Code to see:
/mcp__cache__query
/mcp__cache__learn
/mcp__cache__suggest
/mcp__cache__stats
/mcp__cache__browse
```

**7. Verify Everything is Working:**
```bash
# Check background learning status
cache stats

# Test terminal interface
cache query "test patterns"
```

### ⚡ Enhanced Mode Installation (3 minutes)
```bash
pip install claude-cache[enhanced]

# Start background learning
cache background

# Or with full features
cache run
```

### 🔧 Basic Mode Installation (2 minutes)
```bash
pip install claude-cache

# Start background learning
cache background

# Or foreground mode
cache start --watch
```

---

## 🏃 Step 2: Using Your Chosen Mode

### 🚀 MCP Mode Usage (Revolutionary)

**No additional setup needed!** Just use the native tools:

```
# In Claude Code, type:
/mcp__cache__query authentication

# Instant results:
🔍 Found 3 results for 'authentication'

**1. 🧠 Pattern** (Score: 0.945)
📁 Project: my-react-app
📝 JWT implementation with refresh tokens...
```

**When something works:**
```
/mcp__cache__learn
description: "JWT login working perfectly"
category: "authentication"

✅ Pattern Saved Successfully!
```

**Get proactive suggestions:**
```
/mcp__cache__suggest
context: "Setting up Express API routes"
intent: "add authentication middleware"

💡 Based on your context, I found these patterns...
```

### ⚡ Enhanced Mode Usage (CLI + Semantic Search)

**1. Start monitoring:**
```bash
cache start
# Keep this running in background
```

**2. Query with semantic understanding:**
```bash
cache query "auth bug"
# Finds JWT solutions even without exact keywords!

cache query "slow database"
# Finds performance optimizations, connection pooling
```

### 🔧 Basic Mode Usage (CLI Only)

**1. Start monitoring:**
```bash
cache start
```

**2. Query with keyword search:**
```bash
cache query "authentication"
cache stats
cache browse https://docs.example.com
```

---

## 🔍 Step 3: Verify Your Installation

### 🚀 MCP Mode Verification
```
# In Claude Code, type "/" and look for:
/mcp__cache__query
/mcp__cache__learn
/mcp__cache__suggest
/mcp__cache__stats
/mcp__cache__browse

# Test with:
/mcp__cache__stats
# Should show your knowledge base info
```

### ⚡ Enhanced Mode Verification
```bash
# Check semantic search is available:
python -c "import sentence_transformers; print('✅ Enhanced search ready')"

# Test query:
cache query "test search"
# Should show search mode: semantic ✨
```

### 🔧 Basic Mode Verification
```bash
# Test basic functionality:
cache --version
cache stats

# Should work without errors
```

---

## 📋 Step 4: Understanding the Differences

### What Each Mode Gives You

| Feature | Basic | Enhanced | MCP |
|---------|-------|----------|-----|
| CLI Commands | ✅ | ✅ | ✅ |
| CLAUDE.md Generation | ✅ | ✅ | ✅ |
| TF-IDF Search | ✅ | ✅ | ✅ |
| Semantic Search | ❌ | ✅ | ✅ |
| Context Understanding | ❌ | ✅ | ✅ |
| Native Claude Code Tools | ❌ | ❌ | ✅ |
| Zero Context Switch | ❌ | ❌ | ✅ |
| Proactive Suggestions | ❌ | ❌ | ✅ |

### Mode Comparison Examples

**Query: "auth bug"**
- **Basic**: Finds patterns with exact "auth" or "bug" keywords
- **Enhanced**: Finds JWT issues, login problems, session errors
- **MCP**: Same as Enhanced + available directly in Claude Code

**Learning Patterns:**
- **Basic/Enhanced**: Automatic via log monitoring + manual CLI
- **MCP**: Automatic + instant `/mcp__cache__learn` tool

---

## 📝 Step 5: Understanding the File Structure (All Modes)

All modes create this structure in your projects:

```
your-project/
├── .claude/
│   ├── CLAUDE.md           # Auto-read by Claude (5-10KB)
│   └── lessons/            # Organized by category
│       ├── authentication_lessons.md
│       ├── database_lessons.md
│       └── api_lessons.md
```

**MCP Mode Bonus**: Access this via native tools without file navigation!

---

## 💡 Step 6: Best Practices by Mode

### 🚀 MCP Mode Best Practices

**Learning Patterns:**
```
# When something works perfectly:
/mcp__cache__learn
description: "JWT refresh token rotation working"
category: "authentication"
code_snippet: "// Your working code here"
```

**Getting Suggestions:**
```
# Before starting work:
/mcp__cache__suggest
context: "Building user dashboard"
intent: "add real-time updates"
```

**Quick Queries:**
```
# Find relevant patterns instantly:
/mcp__cache__query database performance
/mcp__cache__query React hooks
```

### ⚡ Enhanced & 🔧 Basic Mode Best Practices

**Give Feedback for Learning:**
When Claude helps and it works, say:
- ✅ "Perfect! That worked!"
- ✅ "Thanks, that fixed it!"
- ✅ "Great, tests pass now!"

**Use CLI Commands:**
```bash
# Query your patterns
cache query "authentication"

# Check your progress
cache stats

# Add documentation
cache browse https://docs.example.com/api
```

---

## 🎆 Step 7: Real Usage Examples

### 🚀 MCP Mode Workflow
```
# Working in Claude Code:
You: "I need to add authentication"

# Instead of guessing, search first:
You: "/mcp__cache__query authentication"
Claude: "🔍 Found JWT pattern from my-api project..."

# Use the suggested approach
You: "Implement that JWT pattern"
Claude: *implements based on your successful pattern*

# When it works:
You: "/mcp__cache__learn JWT auth working in new project"
Claude: "✅ Pattern saved for future use!"
```

### ⚡ Enhanced Mode Workflow
```bash
# Terminal 1: Keep cache running
cache start

# Work in Claude Code normally
# When you need patterns:
cache query "authentication"
# Copy relevant results to Claude

# When something works:
# Give positive feedback to Claude
# Cache learns automatically
```

### 🔧 Basic Mode Workflow
Same as Enhanced, but with keyword-only search.

---

## ⚡ Performance Comparison

### Response Times
- **MCP Mode**: <100ms (native tools)
- **Enhanced Mode**: ~2s (semantic search)
- **Basic Mode**: <500ms (TF-IDF search)

### Accuracy
- **MCP Mode**: Best (semantic + proactive)
- **Enhanced Mode**: 2x better than Basic
- **Basic Mode**: Good keyword matching

### Setup Complexity
- **MCP Mode**: Medium (Claude Code config)
- **Enhanced Mode**: Low (just install)
- **Basic Mode**: Lowest (just install)

---

## 🎯 Migration Path

You can easily upgrade between modes:

### Basic → Enhanced
```bash
pip install sentence-transformers
# Automatically enables semantic search!
```

### Enhanced → MCP
```bash
pip install mcp
# Add .claude.json configuration
# Restart Claude Code
```

### Basic → MCP (Direct)
```bash
pip install claude-cache[mcp]
# Configure Claude Code
# Get all features immediately
```

---

## 📊 Step 8: Monitor Your Progress

### View Statistics
```bash
cache stats

# You'll see:
# ✨ Claude Cache Statistics ✨
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 🧠 Total Patterns    | 42    | 🚀 Thriving!
# 📁 Projects          | 3     | ~14 patterns each
# 💬 Total Requests    | 156   | 73% success rate
```

### Monitor in Real-Time
```bash
# See what's happening live
cache start  # (without --daemon flag)

# Watch as it:
# - Detects new Claude Code sessions
# - Identifies successful patterns
# - Updates your knowledge base
```

---

## 🗂️ Multiple Projects (All Modes)

**All modes handle multiple projects automatically:**

- Each project gets its own `.claude/CLAUDE.md`
- Patterns don't mix between projects
- MCP tools are project-aware

**Check your projects:**
```bash
# CLI (Basic/Enhanced)
cache stats
cache stats --project "my-app"

# MCP Mode
/mcp__cache__stats
# Shows current project info automatically
```

---

## 🎮 Command Reference

### MCP Mode Commands (In Claude Code)
```
/mcp__cache__query [query] [project] [limit]
/mcp__cache__learn [description] [category] [code_snippet]
/mcp__cache__suggest [context] [intent] [limit]
/mcp__cache__stats [project] [detailed]
/mcp__cache__browse [url] [project] [doc_type]
```

### CLI Commands (Enhanced/Basic)
```bash
# Core commands
cache start           # Start monitoring
cache query "text"    # Search patterns
cache stats          # View statistics
cache browse url     # Index documentation

# Background running
tmux new -s cache    # Start in tmux
tmux attach -t cache # Reattach session
```

---

## ❓ How Do I Know It's Working?

### 🚀 MCP Mode Signs
1. Type "/" in Claude Code - see mcp__cache tools
2. `/mcp__cache__stats` shows your data
3. Tools respond instantly with results

### ⚡ Enhanced Mode Signs
1. `cache query "test"` shows "semantic" search mode
2. Finds relevant patterns even with different keywords
3. `cache stats` shows growing pattern count

### 🔧 Basic Mode Signs
1. `cache stats` shows data
2. `.claude/CLAUDE.md` exists in projects
3. `cache query` returns keyword matches

---

## 🔧 Troubleshooting by Mode

### 🚀 MCP Mode Issues
```bash
# Tools don't appear in Claude Code
1. Check .claude.json configuration
2. Restart Claude Code
3. Test: cache-mcp --version

# Tools error
1. Check: pip list | grep mcp
2. Reinstall: pip install claude-cache[mcp]
```

### ⚡ Enhanced Mode Issues
```bash
# Semantic search not working
1. Check: python -c "import sentence_transformers"
2. Install: pip install sentence-transformers

# Falls back to basic search
1. Check memory usage
2. Model download might be needed
```

### 🔧 Basic Mode Issues
```bash
# Cache command not found
1. pip install --upgrade claude-cache
2. Check PATH includes pip install location

# No patterns detected
1. Use Claude Code for a few sessions
2. Give positive feedback when things work
3. Check: cache stats
```

---

## 🎉 Success Checklist by Mode

### 🚀 MCP Mode
- [ ] Installed: `pip install claude-cache[mcp]`
- [ ] Added .claude.json configuration
- [ ] Restarted Claude Code
- [ ] See tools when typing "/" in Claude Code
- [ ] `/mcp__cache__stats` works

### ⚡ Enhanced Mode
- [ ] Installed: `pip install claude-cache[enhanced]`
- [ ] Started: `cache start` (keep running)
- [ ] Query shows "semantic" search mode
- [ ] Better results than keyword-only search

### 🔧 Basic Mode
- [ ] Installed: `pip install claude-cache`
- [ ] Started: `cache start`
- [ ] `cache stats` shows data
- [ ] `.claude/CLAUDE.md` exists in projects

---

## 💡 Pro Tips by Mode

### 🚀 MCP Mode Tips
1. **Use suggest tool proactively** - Get recommendations before you start
2. **Learn patterns immediately** - Don't wait, save successful solutions instantly
3. **Browse documentation** - Index team docs for searchable knowledge

### ⚡ Enhanced Mode Tips
1. **Try semantic queries** - "auth bug" instead of "authentication error"
2. **Let semantic search learn** - More patterns = better context understanding

### 🔧 Basic Mode Tips
1. **Use specific keywords** - "JWT authentication" vs "auth"
2. **Give clear feedback** - "Perfect!" triggers pattern learning

### Universal Tips (All Modes)
1. **Let it run for a week** - More data = smarter suggestions
2. **Check stats regularly** - Monitor your knowledge growth
3. **Each project is separate** - No pattern mixing between projects

---

## 🎯 What Happens Next?

### 🚀 MCP Mode Experience
1. **Type "/" in Claude Code** → Instant access to all patterns
2. **Ask for help** → Claude proactively suggests relevant patterns
3. **Success happens** → Save with `/mcp__cache__learn`
4. **Zero friction** → Everything happens in Claude Code

### ⚡ Enhanced Mode Experience
1. **Background monitoring** → Learns from every session
2. **Semantic understanding** → Finds patterns by meaning, not just keywords
3. **CLI queries** → `cache query` gives contextual results
4. **Automatic improvement** → Gets smarter over time

### 🔧 Basic Mode Experience
1. **Reliable foundation** → Works everywhere, no dependencies
2. **Keyword matching** → Solid pattern retrieval
3. **CLAUDE.md integration** → Automatic context for Claude
4. **Upgrade ready** → Easy path to Enhanced or MCP

**All modes**: The longer you use Claude Cache, the more personalized and effective Claude becomes for YOUR specific coding style and projects!

---

## 📚 Learn More

- **Installation Guide**: See INSTALLATION.md for detailed setup
- **How It Works**: Read HOW_IT_WORKS.md for technical details
- **Version Info**: Run `cache --version` or `cache-mcp --version`
- **GitHub**: [claude-cache repository](https://github.com/ga1ien/claude-cache)

## 🌟 Recommended Path

1. **New users**: Start with Basic mode, try for a week
2. **Power users**: Go directly to MCP mode for ultimate experience
3. **Teams**: Use MCP mode with shared .claude.json configuration

**Happy coding with Claude Cache v0.9.0! 🚀**