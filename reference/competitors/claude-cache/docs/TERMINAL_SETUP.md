# Claude Cache Terminal Setup Guide

Complete guide for running Claude Cache in terminal with multiple startup methods and background process options.

## 🚀 Quick Start Commands

### **Recommended: Simple Background**
```bash
cache background
```
**Best for**: Set-and-forget background learning

### **Alternative: Updated Run Command**
```bash
cache run
```
**Best for**: Background learning + terminal interface

### **Basic: Direct Start**
```bash
cache start --watch
```
**Best for**: Foreground monitoring and testing

## 📋 All Startup Methods

### 1. **Background Process (Recommended)**
```bash
cache background
```

**What it does:**
- ✅ Starts in background using subprocess (no daemon)
- ✅ Survives terminal closure
- ✅ Logs to `/tmp/claude-cache.log`
- ✅ Monitors Claude Code every 30 seconds
- ✅ Vector search and pattern intelligence active

**Control:**
```bash
# Stop
pkill -f 'cache start'

# View logs
tail -f /tmp/claude-cache.log

# Check if running
ps aux | grep 'cache start'
```

### 2. **Enhanced Run Command**
```bash
cache run                    # Background mode
cache run --foreground       # Foreground mode
cache run --with-mcp         # Include MCP server
```

**What it does:**
- ✅ Direct agent subprocess (no daemon)
- ✅ Background learning + full terminal interface
- ✅ Optional MCP server integration
- ✅ Enhanced intelligence with vector search

**Control:**
```bash
# Stop
pkill -f 'CacheAgent'

# With MCP server
pkill cache-mcp
```

### 3. **Direct Start (Simple)**
```bash
cache start --watch         # Foreground
cache start --daemon         # Daemon mode (if working)
```

**What it does:**
- ✅ Proven to work (we tested this)
- ✅ Real-time monitoring
- ✅ Processes existing + new logs
- ✅ Generates slash commands automatically

**Control:**
```bash
# Stop (if foreground)
Ctrl+C

# Stop (if background)
pkill -f 'cache start'
```

### 4. **One-Time Processing**
```bash
cache process
```

**What it does:**
- ✅ Processes existing Claude Code logs only
- ✅ Builds knowledge base from past conversations
- ✅ No monitoring or background running
- ✅ Perfect for initial setup

## 🔄 Advanced Background Methods

### **Using nohup**
```bash
# Start in background
nohup cache start --watch > cache.log 2>&1 &

# Save process ID
echo $! > ~/.cache-pid

# Stop using saved PID
kill $(cat ~/.cache-pid)
```

### **Using screen (Detachable Sessions)**
```bash
# Start detached session
screen -S claude-cache -d -m cache start --watch

# List sessions
screen -list

# Reattach to session
screen -r claude-cache

# Detach from session (inside screen)
Ctrl+A, then D

# Kill session
screen -S claude-cache -X quit
```

### **Using tmux (Session Management)**
```bash
# Start detached session
tmux new-session -d -s claude-cache 'cache start --watch'

# List sessions
tmux list-sessions

# Attach to session
tmux attach -t claude-cache

# Detach from session (inside tmux)
Ctrl+B, then D

# Kill session
tmux kill-session -t claude-cache
```

### **Auto-start on Login (macOS/Linux)**

Add to `~/.bashrc` or `~/.zshrc`:
```bash
# Auto-start Claude Cache if not running
if ! pgrep -f 'cache start' > /dev/null; then
    cache background
fi
```

Add to `~/.profile` (runs once per login):
```bash
# Start Claude Cache in background
cache background 2>/dev/null || true
```

## 🔍 Monitoring and Control

### **Check What's Running**
```bash
# Check for any Claude Cache processes
ps aux | grep cache

# Check specific patterns
ps aux | grep 'cache start'
ps aux | grep 'CacheAgent'
ps aux | grep 'cache-mcp'
```

### **View Logs**
```bash
# Background command logs
tail -f /tmp/claude-cache.log

# Custom log location (if using nohup)
tail -f cache.log

# Check knowledge base status
cache stats
```

### **Stop Everything**
```bash
# Stop all Claude Cache processes
pkill -f 'cache'

# Stop specific components
pkill -f 'cache start'     # Background learning
pkill -f 'CacheAgent'      # Direct agent
pkill cache-mcp            # MCP server
```

## 🧠 Using the Terminal Interface

Once Claude Cache is running, use these commands:

### **Search and Query**
```bash
# Search existing patterns
cache query "authentication patterns"
cache query "database optimization" --limit 3

# Get contextual suggestions
cache suggest --context "working on React components"
cache suggest --context "debugging API issues"

# Search documentation
cache search-docs "error handling"
```

### **Manual Learning**
```bash
# Save successful solutions
cache learn "JWT middleware with role validation" --tags "auth,jwt,security"

# Index documentation
cache browse https://docs.example.com
cache scan-docs .  # Scan current repo
cache scan-docs /path/to/project
```

### **Knowledge Base Management**
```bash
# View statistics
cache stats

# Export/import
cache export backup.json
cache import backup.json

# Rebuild from scratch
cache rebuild
```

## 🔗 Claude Code Integration

For Claude Code MCP integration (run separately):

```bash
# Start MCP server
cache-mcp

# Or include with run command
cache run --with-mcp
```

**In Claude Code, use:**
- `/mcp__cache__query "authentication patterns"`
- `/mcp__cache__stats`
- `/mcp__cache__suggest`
- `/mcp__cache__learn "solution" --tags "tag1,tag2"`

## 🛠️ Troubleshooting

### **Daemon Not Working**
Use alternative methods:
```bash
cache background    # Uses subprocess instead
cache run          # Uses direct agent
cache start --watch # Direct foreground
```

### **Permission Issues**
```bash
# Check file permissions
ls -la ~/.claude/knowledge/

# Fix permissions
chmod 755 ~/.claude/knowledge/
chmod 644 ~/.claude/knowledge/*.db
```

### **Process Not Starting**
```bash
# Check for conflicting processes
pkill -f cache

# Try foreground mode first
cache start --watch

# Check error logs
tail -f /tmp/claude-cache.log
```

### **Vector Search Not Working**
```bash
# Install enhanced dependencies
pip install claude-cache[enhanced]

# Or install directly
pip install sentence-transformers

# Verify installation
cache stats  # Should show "semantic" mode
```

### **Claude Code Not Detecting Patterns**
```bash
# Check if logs are being processed
cache stats

# Verify log location
ls -la ~/Library/Application\ Support/Claude/claude_desktop/logs/

# Process existing logs
cache process
```

## 📊 Recommended Workflow

### **Initial Setup**
```bash
# 1. Install
pip install claude-cache

# 2. Process existing logs
cache process

# 3. Start background learning
cache background

# 4. Test terminal interface
cache stats
cache query "test"
```

### **Daily Usage**
```bash
# Check status
cache stats

# Search for patterns
cache query "specific problem"

# Get suggestions
cache suggest --context "current work"

# Save new patterns
cache learn "working solution" --tags "relevant,tags"
```

### **For Claude Code Users**
```bash
# Start background learning
cache background

# Start MCP server (separate terminal/process)
cache-mcp

# Use in Claude Code
/mcp__cache__query "patterns"
```

## 💡 Tips

- **Use `cache background`** for simplest setup
- **Use `cache stats`** to verify everything is working
- **Use `cache process`** first to build from existing logs
- **Use screen/tmux** for more control over background processes
- **Check logs** if something isn't working: `tail -f /tmp/claude-cache.log`
- **Stop everything** before troubleshooting: `pkill -f cache`

## 🎯 Which Method to Choose

| Method | Best For | Pros | Cons |
|--------|----------|------|------|
| `cache background` | Set and forget | Simple, reliable, logs to file | Less control |
| `cache run` | Development | Full features, MCP option | More complex |
| `cache start --watch` | Testing | Proven to work, simple | Foreground only |
| `nohup + cache start` | Custom setups | Full control, custom logging | Manual setup |
| `screen/tmux` | Advanced users | Session management, flexibility | Learning curve |

**For most users**: Start with `cache background` ✅