# Session Management in Kioku

## Overview

Kioku automatically tracks coding sessions to understand your work patterns and maintain context continuity. Sessions are created when the MCP server starts and end when it stops or after 30 minutes of inactivity.

## How Sessions Work

### Session Lifecycle

```
MCP Server Start → Session Created (active)
       ↓
File Access / Tool Calls → Activity Tracked
       ↓
MCP Server Stop OR 30min Inactivity → Session Ended (completed)
       ↓
Discovery Extraction (future) → Context Enriched
```

### Session States

- **`active`** - Session is ongoing, tracking file access and activity
- **`completed`** - Session has ended normally (server stopped or timeout)
- **`archived`** - Session archived due to context pruning (future feature)

### Automatic Features

#### 1. Graceful Shutdown

The MCP server now properly handles shutdown signals:

```bash
# Press Ctrl+C to stop
^C
# Server automatically:
# 1. Ends active session
# 2. Stops background services
# 3. Closes database connections
```

#### 2. Inactivity Timeout (30 minutes)

Sessions automatically end after 30 minutes of no activity:

- Activity is tracked on every file access or tool call
- Background service checks every 5 minutes
- Prevents orphaned sessions from accumulating
- Configurable timeout: `SessionManager.INACTIVITY_TIMEOUT_MS`

#### 3. Session Cleanup Command

For orphaned sessions that weren't properly ended:

```bash
# Preview what would be cleaned up
kioku cleanup-sessions --dry-run

# Clean up sessions older than 1 hour (default)
kioku cleanup-sessions

# Clean up sessions older than 2 hours
kioku cleanup-sessions --older-than 2

# Skip confirmation prompt
kioku cleanup-sessions --force
```

## Troubleshooting

### Problem: Orphaned Sessions

**Symptoms:**
- Multiple "active" sessions in database
- Database growing unnecessarily
- Old sessions never marked as "completed"

**Causes:**
- Server crashed or was force-killed (before fix)
- Multiple server instances running simultaneously
- System restart without graceful shutdown

**Solution:**

1. **Clean up existing orphaned sessions:**
   ```bash
   kioku cleanup-sessions --dry-run  # Preview
   kioku cleanup-sessions             # Execute
   ```

2. **Check for multiple server processes:**
   ```bash
   ps aux | grep kioku | grep serve
   ```

3. **Kill old processes if needed:**
   ```bash
   pkill -f "kioku.*serve"  # Kill all
   # Then restart with: kioku serve
   ```

### Problem: Session Never Ends

**Symptoms:**
- Session stays "active" even after closing editor
- Session lasts for days

**Diagnosis:**
```bash
# Check active sessions
sqlite3 .context/sessions.db "SELECT id, datetime(started_at/1000, 'unixepoch', 'localtime') as started, status FROM sessions WHERE status='active';"
```

**Solution:**

1. **If MCP server is still running:**
   - Stop it gracefully with Ctrl+C
   - Session will end automatically

2. **If MCP server already stopped:**
   - Use cleanup command to mark as completed
   ```bash
   kioku cleanup-sessions --older-than 0
   ```

### Problem: Multiple Server Instances

**Symptoms:**
- Multiple `kioku serve` processes running
- High CPU usage
- Database locked errors

**Diagnosis:**
```bash
ps aux | grep "kioku.*serve" | grep -v grep | wc -l
```

**Solution:**

1. **Kill all instances:**
   ```bash
   pkill -f "kioku.*serve"
   ```

2. **Restart cleanly:**
   ```bash
   # In your project directory
   kioku serve
   ```

3. **For editors that auto-start MCP:**
   - Close all editor windows
   - Kill orphaned processes
   - Restart editor

## Database Maintenance

### Check Session Statistics

```bash
# Count sessions by status
sqlite3 .context/sessions.db "SELECT status, COUNT(*) FROM sessions GROUP BY status;"

# List recent sessions
sqlite3 .context/sessions.db "SELECT id, status, datetime(started_at/1000, 'unixepoch', 'localtime') as started FROM sessions ORDER BY started_at DESC LIMIT 10;"

# Find old active sessions
sqlite3 .context/sessions.db "SELECT id, datetime(started_at/1000, 'unixepoch', 'localtime') as started FROM sessions WHERE status='active' AND started_at < strftime('%s','now','-1 day')*1000;"
```

### Manual Session Cleanup (SQL)

If you need to manually clean up sessions:

```sql
-- Mark all old active sessions as completed
UPDATE sessions 
SET 
  status = 'completed',
  ended_at = started_at + 3600000,  -- +1 hour
  updated_at = strftime('%s','now') * 1000
WHERE 
  status = 'active' 
  AND started_at < strftime('%s','now','-1 hour') * 1000;
```

## Best Practices

### For Development

1. **Always use Ctrl+C to stop the server**
   - Ensures graceful shutdown
   - Sessions properly ended
   - Database connections closed

2. **Run cleanup periodically during development:**
   ```bash
   kioku cleanup-sessions --older-than 1
   ```

3. **Check for orphaned processes:**
   ```bash
   # Weekly or after system crashes
   ps aux | grep kioku | grep serve
   ```

### For Production/Deployment

1. **Use process managers that support graceful shutdown:**
   - systemd with proper `KillSignal=SIGTERM`
   - PM2 with graceful reload
   - Docker with proper SIGTERM handling

2. **Monitor session health:**
   ```bash
   # Add to monitoring
   kioku cleanup-sessions --dry-run
   ```

3. **Automated cleanup in CI/CD:**
   ```bash
   # In deployment scripts
   kioku cleanup-sessions --force --older-than 24
   ```

## Configuration

### Session Timeout

Default: 30 minutes

To change (requires code modification):
```typescript
// packages/api/src/application/use-cases/SessionManager.ts
private static readonly INACTIVITY_TIMEOUT_MS = 30 * 60 * 1000; // milliseconds
```

### Cleanup Threshold

Default: 1 hour

To change:
```bash
kioku cleanup-sessions --older-than <hours>
```

## Architecture

### Session Manager

**Location:** `packages/api/src/application/use-cases/SessionManager.ts`

**Responsibilities:**
- Create sessions on MCP server start
- Track file access and activity
- Update last activity timestamp
- End sessions gracefully
- Check for inactivity timeout

### Background Services

**Location:** `packages/api/src/infrastructure/background/`

**SessionTimeoutChecker:**
- Runs every 5 minutes
- Checks if current session inactive > 30 minutes
- Auto-ends inactive sessions

**Integration:**
```typescript
// ServiceManager starts timeout checker automatically
this.serviceManager = new ServiceManager(sqliteAdapter, sessionManager);
```

### Cleanup Command

**Location:** `packages/cli/src/commands/cleanup-sessions.ts`

**Features:**
- Dry-run mode (preview changes)
- Configurable age threshold
- Confirmation prompt (skippable with --force)
- Batch processing of orphaned sessions

## Future Enhancements

### Planned Features (Post-MVP)

1. **Session History Visualization**
   - Dashboard showing session timeline
   - Activity heatmaps
   - Productivity metrics

2. **Session Analytics**
   - Average session length
   - Most active hours
   - File access patterns

3. **Smart Session Merging**
   - Merge sessions from same day
   - Detect break vs new session
   - Context continuity scoring

4. **Automated Health Checks**
   - `kioku doctor` integration
   - Session health warnings
   - Auto-cleanup suggestions

## Summary

✅ **Fixed Issues:**
- Sessions now end properly on Ctrl+C
- 30-minute inactivity timeout prevents leaks
- Cleanup command for orphaned sessions
- Graceful shutdown handlers

✅ **Improvements:**
- Background timeout checker
- Clean database maintenance
- Better process lifecycle management

✅ **User Benefits:**
- Clean session history
- Accurate session statistics
- No manual intervention needed
- Database stays healthy

For more help, see:
- [README.md](../README.md) - General usage
- [troubleshooting.md](./troubleshooting.md) - Common issues
- [architecture.md](./architecture.md) - System design
