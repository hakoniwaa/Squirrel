# Kioku Visual Dashboard - Complete Guide

## 🎯 What Is The Dashboard?

The Kioku Dashboard is a **web-based visual interface** that lets you see what Kioku "knows" about your project in real-time. Think of it as a **window into Kioku's brain**.

Instead of running CLI commands to inspect context, you open a browser and see everything at a glance.

---

## 🤔 Why Do We Need It?

### Problem Without Dashboard:
```bash
# Current way (CLI only):
$ kioku show context          # See raw YAML
$ kioku status                # See text status
$ cat .context/sessions.db    # Need SQL to query
$ grep "error" logs/          # Hunt through logs
```

**Issues:**
- Text-only output is hard to parse
- No visual patterns or trends
- Can't see relationships (which files → which modules → which sessions)
- Debugging requires multiple commands
- No real-time monitoring

### Solution With Dashboard:
```
Open browser → http://localhost:3456 → See everything visually!
```

**Benefits:**
- **Visual patterns**: See which modules are "hot" (frequently accessed)
- **Interactive graphs**: Click on sessions to expand details
- **Real-time updates**: Context window fills up? You see it live!
- **Faster debugging**: "Why didn't Kioku find this file?" → Check dashboard → See it's not in embeddings
- **Health monitoring**: Is background service running? Dashboard shows green/red status

---

## 📊 Dashboard Features (What You'll See)

### 1. **Project Overview Card** (Top of page)

```
┌─────────────────────────────────────────────────┐
│  📁 Kioku Project Overview                      │
├─────────────────────────────────────────────────┤
│  Name: kioku                                    │
│  Type: Node.js (TypeScript)                     │
│  Tech Stack: Bun, SQLite, Chroma, MCP          │
│                                                  │
│  📂 Modules: 48                                 │
│  📄 Total Files: 1,247                          │
│  💾 Database Size: 45.2 MB                      │
│                                                  │
│  Status: ● Active Session (12 min ago)         │
│  Context Window: [████████░░] 82% (82K/100K)   │
└─────────────────────────────────────────────────┘
```

**What it tells you:**
- Is Kioku running? (Green dot = yes)
- How full is the context window? (Approaching limit?)
- How many modules/files does Kioku track?

---

### 2. **Session Timeline** (Visual history)

```
┌─────────────────────────────────────────────────┐
│  📅 Session Timeline                            │
├─────────────────────────────────────────────────┤
│  Today, 2:34 PM - 2:46 PM (12 min)              │
│  ├─ Files: auth.ts, user-service.ts (5 files)  │
│  ├─ Topics: authentication, JWT tokens          │
│  ├─ Discoveries: 3 patterns found               │
│  └─ [Click to expand ▼]                         │
│                                                  │
│  Today, 10:15 AM - 10:42 AM (27 min)            │
│  ├─ Files: chunk-extractor.ts, ast-parser.ts   │
│  ├─ Topics: AST parsing, code chunking          │
│  └─ [Click to expand ▼]                         │
│                                                  │
│  Yesterday, 4:22 PM - 5:11 PM (49 min)          │
│  └─ [Click to expand ▼]                         │
└─────────────────────────────────────────────────┘
```

**What it tells you:**
- What have you been working on?
- Which files were accessed in each session?
- Are patterns being discovered?

**When expanded (click on a session):**
```
┌─────────────────────────────────────────────────┐
│  Session: Today, 2:34 PM - 2:46 PM              │
├─────────────────────────────────────────────────┤
│  Files Accessed:                                │
│  ├─ src/auth.ts               [████░] 18 refs  │
│  ├─ src/user-service.ts       [███░░] 12 refs  │
│  ├─ src/middleware/auth.ts    [██░░░] 7 refs   │
│  ├─ tests/auth.test.ts        [█░░░░] 3 refs   │
│  └─ src/types/user.ts         [█░░░░] 2 refs   │
│                                                  │
│  Topics Discussed:                              │
│  - JWT token generation                         │
│  - User authentication flow                     │
│  - Middleware error handling                    │
│                                                  │
│  Discoveries Extracted:                         │
│  ✓ Pattern: "Always validate JWT before auth"  │
│  ✓ Decision: "Use bcrypt for password hashing" │
│  ✓ Constraint: "Token expiry = 24 hours"       │
└─────────────────────────────────────────────────┘
```

**Heatmap colors:**
- 🟥 Red = Heavily accessed (20+ references)
- 🟧 Orange = Frequently accessed (10-19 refs)
- 🟨 Yellow = Moderately accessed (5-9 refs)
- 🟦 Blue = Lightly accessed (1-4 refs)

---

### 3. **Module Dependency Graph** (Interactive visualization)

```
┌─────────────────────────────────────────────────┐
│  🕸️ Module Dependency Graph                     │
├─────────────────────────────────────────────────┤
│                                                  │
│         [domain] ●────────┐                     │
│              │            │                     │
│              ↓            ↓                     │
│      [application] ●  [shared] ●               │
│              │                                  │
│              ↓                                  │
│     [infrastructure] ●                          │
│          ↙   ↓   ↘                             │
│    [mcp] ● [storage] ● [cli] ●                 │
│                                                  │
│  Legend:                                        │
│  ● Green = Active (accessed today)              │
│  ● Yellow = Recent (accessed this week)         │
│  ● Gray = Stale (not accessed recently)         │
└─────────────────────────────────────────────────┘
```

**What it tells you:**
- Which modules depend on which? (Architecture validation)
- Which modules are "hot"? (Frequently worked on)
- Are there circular dependencies? (Would show cycles)

**Interactive features:**
- Click node → See files in that module
- Hover edge → See import count
- Zoom/pan for large codebases

---

### 4. **Embeddings Statistics** (AI context health)

```
┌─────────────────────────────────────────────────┐
│  🧠 Embeddings Statistics                       │
├─────────────────────────────────────────────────┤
│  Total Embeddings: 1,247                        │
│  Last Generated: 2 minutes ago                  │
│  Queue Size: 0 (all processed ✓)                │
│  Disk Usage: 18.3 MB                            │
│                                                  │
│  Generation Rate (last hour):                   │
│  [Chart showing embeddings/min over time]       │
│                                                  │
│  Error Log:                                     │
│  ✓ No errors in last 24 hours                  │
└─────────────────────────────────────────────────┘
```

**What it tells you:**
- Are embeddings being generated? (Queue should be near 0)
- Are there errors? (OpenAI API issues?)
- How much disk space used?

**When there ARE errors:**
```
│  Error Log:                                     │
│  ⚠️ 12 errors in last hour:                    │
│  └─ 10:45 AM: OpenAI rate limit exceeded       │
│  └─ 10:46 AM: Retry failed (max retries)       │
│  └─ 10:47 AM: File too large (skipped)         │
```

---

### 5. **Context Window Monitor** (Real-time gauge)

```
┌─────────────────────────────────────────────────┐
│  📊 Context Window Usage                        │
├─────────────────────────────────────────────────┤
│                                                  │
│         Current: 82,345 tokens                  │
│         Maximum: 100,000 tokens                 │
│                                                  │
│         [████████████████░░░░] 82%             │
│          │               │   │                  │
│       Safe (0-70%)    Warn   Critical          │
│                      (70-90%) (90%+)            │
│                                                  │
│  Status: ⚠️ Approaching limit                  │
│  Action: Pruning will trigger at 90%            │
└─────────────────────────────────────────────────┘
```

**What it tells you:**
- How close to context limit? (Important for AI responses)
- Will pruning happen soon?
- Is context window healthy?

**Color codes:**
- 🟢 Green (0-70%): Healthy, plenty of space
- 🟡 Yellow (70-90%): Warning, approaching limit
- 🔴 Red (90%+): Critical, pruning imminent

---

### 6. **Multi-Project View** (If using Phase 9 features)

```
┌─────────────────────────────────────────────────┐
│  🔗 Linked Projects                             │
├─────────────────────────────────────────────────┤
│  ✓ kioku-frontend   (available)  [View →]      │
│  ✓ kioku-backend    (available)  [View →]      │
│  ⚠️ kioku-mobile     (unavailable)              │
│                                                  │
│  Cross-Project References: 127                  │
│  └─ frontend → backend: 89 imports              │
│  └─ backend → shared: 38 imports                │
└─────────────────────────────────────────────────┘
```

**What it tells you:**
- Which projects are linked?
- Are they all accessible?
- How many cross-references exist?

---

### 7. **Background Services Status** (Health monitor)

```
┌─────────────────────────────────────────────────┐
│  ⚙️ Background Services                         │
├─────────────────────────────────────────────────┤
│  ● MCP Server         Running (port 9090)       │
│  ● File Watcher       Running (47 files)        │
│  ● Embeddings Queue   Idle (queue: 0)           │
│  ● Context Scorer     Last run: 3 min ago       │
│  ● Context Pruner     Standby (usage: 82%)      │
└─────────────────────────────────────────────────┘
```

**What it tells you:**
- Are all services running? (Green = yes, Red = no)
- Is file watcher active? (Updates happening?)
- When did scorer last run? (Should run every 5 min)

---

## 🎬 How You'll Use The Dashboard

### Use Case 1: **Debugging "AI didn't find my file"**

```
Problem: "Kioku didn't suggest my new auth.ts file"

Steps:
1. Open dashboard → http://localhost:3456
2. Check "Embeddings Statistics"
   → See queue has 5 files waiting
   → auth.ts is in queue!
3. Check "Background Services"
   → Embeddings Queue shows "Processing (queue: 5)"
   → Wait 30 seconds, refresh
4. Confirm auth.ts now in embeddings
   → Total embeddings count increased by 1
   
Resolution: File was pending, just needed processing time!
```

---

### Use Case 2: **Monitoring Context Window Health**

```
Scenario: Long coding session, worried about context saturation

Steps:
1. Keep dashboard open in second monitor
2. Watch "Context Window Usage" gauge in real-time
3. See gauge rising: 65% → 72% → 78%
4. Notice yellow warning at 78%
5. Continue working, gauge hits 90%
6. See notification: "Pruner activated, removing stale context"
7. Gauge drops back to 65%

Benefit: Visual confidence that pruning works automatically!
```

---

### Use Case 3: **Understanding Session Patterns**

```
Scenario: Want to review what I worked on yesterday

Steps:
1. Dashboard → Session Timeline
2. See yesterday's sessions listed
3. Click on longest session (49 min)
4. See heatmap:
   - auth.ts: 28 references (heavily edited)
   - user-service.ts: 14 references (moderate)
   - tests: 6 references (light)
5. Read "Topics Discussed":
   - JWT implementation
   - Error handling
   - Test coverage

Benefit: Quick recall of yesterday's work without git log!
```

---

### Use Case 4: **Validating Architecture**

```
Scenario: Ensuring Onion Architecture compliance

Steps:
1. Dashboard → Module Dependency Graph
2. Visual check:
   - domain has NO outgoing arrows ✓ (good!)
   - application only points to domain ✓
   - infrastructure points to both ✓
3. Spot problem: application → infrastructure edge! ❌
4. Click edge → See the violating import
5. Fix in code, watch graph update in real-time

Benefit: Instant visual architecture validation!
```

---

### Use Case 5: **Monitoring AI Health**

```
Scenario: OpenAI API having issues?

Steps:
1. Dashboard → Embeddings Statistics
2. See error log:
   "⚠️ 47 errors in last hour"
   "Rate limit exceeded" (repeated)
3. Check graph: embeddings/min dropped to 0
4. Realize: Need to slow down embedding rate
5. Update config, see errors stop

Benefit: Immediate visibility into API health!
```

---

## 🏗️ Technical Architecture

### How It Works:

```
┌─────────────────┐         ┌──────────────────┐
│   Browser       │         │   Kioku Server   │
│  (localhost:    │◄────────┤  (localhost:     │
│   3456)         │  HTTP   │   9090)          │
│                 │         │                  │
│  React App      │         │  REST API        │
│  - Charts       │         │  /api/project    │
│  - Graphs       │         │  /api/sessions   │
│  - Live updates │         │  /api/modules    │
│                 │         │  /api/embeddings │
│                 │         │  /api/context    │
└─────────────────┘         └──────────────────┘
        ↑                            ↓
        │                            │
        └────── Poll every 5s ───────┘
```

**Flow:**
1. You run: `kioku dashboard`
2. Server starts on port 9090 (REST API)
3. Dashboard starts on port 3456 (React app)
4. Browser auto-opens to http://localhost:3456
5. React app polls /api/* every 5 seconds
6. Dashboard updates in real-time

---

## 📁 File Structure

```
kioku/
├── src/
│   └── infrastructure/
│       └── monitoring/
│           ├── metrics-server.ts        (Already exists)
│           └── api-endpoints.ts         (NEW - REST API)
│
├── dashboard/                            (NEW - React app)
│   ├── package.json
│   ├── src/
│   │   ├── components/
│   │   │   ├── ProjectOverview.tsx
│   │   │   ├── SessionTimeline.tsx
│   │   │   ├── ModuleGraph.tsx
│   │   │   ├── EmbeddingsStats.tsx
│   │   │   └── ContextGauge.tsx
│   │   ├── services/
│   │   │   └── api-client.ts           (Polling logic)
│   │   ├── App.tsx
│   │   └── index.tsx
│   └── public/
│       └── index.html
│
└── tests/
    ├── unit/infrastructure/monitoring/
    │   └── api-endpoints.test.ts       (NEW - API tests)
    └── integration/
        └── dashboard-api.test.ts       (NEW - E2E tests)
```

---

## 🎨 Visual Design (Mockup)

```
┌────────────────────────────────────────────────────────────┐
│  🧠 Kioku Dashboard                            [Refresh ⟳] │
├────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────────────┐  ┌───────────────────────────┐  │
│  │ 📁 Project Overview  │  │ 📊 Context Window         │  │
│  │ Name: kioku          │  │ [████████░░] 82%          │  │
│  │ Modules: 48          │  │ 82K / 100K tokens         │  │
│  │ Files: 1,247         │  │ Status: ⚠️ Approaching    │  │
│  └──────────────────────┘  └───────────────────────────┘  │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐  │
│  │ 📅 Session Timeline                         [View ↓]│  │
│  │ ● Today, 2:34 PM (12 min)  [5 files] [3 discoveries]│  │
│  │ ○ Today, 10:15 AM (27 min) [8 files] [1 discovery]  │  │
│  │ ○ Yesterday, 4:22 PM (49 min) [12 files]            │  │
│  └─────────────────────────────────────────────────────┘  │
│                                                             │
│  ┌────────────────────┐  ┌────────────────────────────┐  │
│  │ 🕸️ Module Graph    │  │ 🧠 Embeddings Stats        │  │
│  │ [Interactive viz]  │  │ Total: 1,247               │  │
│  │ (D3.js graph)      │  │ Queue: 0                   │  │
│  │                    │  │ Errors: None ✓             │  │
│  └────────────────────┘  └────────────────────────────┘  │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐  │
│  │ ⚙️ Background Services                    [Status ✓]│  │
│  │ ● MCP Server (9090)  ● File Watcher (47 files)      │  │
│  │ ● Embeddings Queue   ● Context Scorer (3 min ago)   │  │
│  └─────────────────────────────────────────────────────┘  │
│                                                             │
│  Last updated: 2 seconds ago                    [Auto ✓]  │
└────────────────────────────────────────────────────────────┘
```

---

## ⚡ Key Features Summary

| Feature | Purpose | Benefit |
|---------|---------|---------|
| **Project Overview** | See project stats at-a-glance | Quick health check |
| **Session Timeline** | Visual history of work | Recall past context |
| **Module Graph** | Interactive dependency viz | Validate architecture |
| **Embeddings Stats** | Monitor AI context health | Debug search issues |
| **Context Gauge** | Real-time usage monitor | Prevent saturation |
| **Multi-Project** | See linked projects | Cross-repo awareness |
| **Services Status** | Background health | Ensure all running |
| **Auto-refresh** | Poll every 5 seconds | Live updates |
| **Read-only** | No mutations allowed | Safe to explore |

---

## 🚀 When You'll Use It

**During Development:**
- Second monitor showing dashboard while coding
- Quick glance to see context health
- Visual confirmation features are working

**During Debugging:**
- "Why didn't AI find this file?" → Check embeddings
- "Is file watcher working?" → Check services
- "Context window full?" → Check gauge

**During Architecture Review:**
- Show module graph to team
- Validate onion architecture visually
- Spot circular dependencies

**During Demos:**
- Show stakeholders what Kioku tracks
- Visual proof of AI context learning
- Impressive real-time updates!

---

## 🎯 Bottom Line

**The Dashboard is your "Mission Control" for Kioku.**

Instead of:
```bash
$ kioku show context
$ cat .context/sessions.db
$ grep "error" logs/*.log
```

You get:
```
Open browser → See everything → Click to explore → Live updates!
```

**It transforms Kioku from a "black box" into a "glass box"** - you can see exactly what it knows, what it's doing, and why.

---

## 📝 Next Steps (If Building)

1. ✅ Read this guide
2. ⏳ Review spec.md User Story 7 (detailed requirements)
3. ⏳ Review tasks.md Phase 10 (task breakdown)
4. ⏳ Start with backend REST API (api-endpoints.ts)
5. ⏳ Build React dashboard components
6. ⏳ Add polling logic
7. ⏳ Test with real Kioku project
8. ⏳ Iterate based on actual usage

**Estimated Time:** 5-7 days for full implementation

**Worth it?** If you want visual insight into Kioku's brain - YES!

---

**Questions? Let me know what specific features or use cases you want to understand better!**
