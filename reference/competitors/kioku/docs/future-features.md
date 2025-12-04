# Future Features - Kioku v2.1+

**Status**: Deferred from v2.0  
**Source**: `.specify/specs/002-advanced-context-intelligence/`  
**Purpose**: Track planned features for post-v2.0 releases

This document preserves all deferred tasks from the v2.0 implementation. Each phase is production-ready spec'd and can be picked up whenever prioritized.

---

## 📋 Quick Reference

| Phase | Feature | Tasks | Priority | Estimated Effort | Target Version |
|-------|---------|-------|----------|------------------|----------------|
| Phase 5 | Real-Time File Watching | T075-T091 (17 tasks) | Medium | ~5-7 days | v2.1 |
| Phase 6 | AI-Enhanced Discovery | T092-T103 (12 tasks) | Medium | ~5 days | v2.1 |
| Phase 7 | Intelligent Ranking | T104-T114 (11 tasks) | Low | ~4 days | v2.1 |
| Phase 8* | Full Monitoring | T115-T127 (13 tasks) | Low | ~3 days | v2.2 |
| Phase 9* | Multi-Project | T128-T145 (18 tasks) | Low | ~7 days | v2.2 |

**Total Deferred**: 71 tasks (~24-31 days of work)

*Partial implementation exists - see status details below

---

## Phase 5: Real-Time File Watching 🔄

**Priority**: Medium (High UX value, but not blocking)  
**Status**: Skeleton exists, full implementation deferred  
**Target**: v2.1

### User Story (US3)

**As a** developer actively coding  
**I want** Kioku to automatically detect file changes  
**So that** context stays fresh without manual refresh

### Business Value

- **Zero-latency updates**: Context refreshes within 2 seconds of file save
- **Reduced manual work**: No need to run `kioku init` after changes
- **Real-time accuracy**: AI always has latest code state

### Why Deferred

1. **Complexity**: OS-specific file watching (fsevents/inotify/Windows)
2. **Performance**: Can be resource-intensive in large projects
3. **Workaround exists**: Users can manually re-run `kioku init`
4. **Risk**: File watcher crashes can impact system stability

### What's Already Done

- ✅ T025: FileWatcherService skeleton created
- ✅ T033: IFileWatcher port defined
- ✅ T013: ChangeEvent domain model
- ✅ T018: change_events database table
- ✅ Dependencies: `chokidar` installed

### Remaining Tasks (T075-T091)

#### Tests (TDD - Write First)
- [ ] T075 [P] [US3] Unit test: `tests/unit/infrastructure/file-watcher/FileWatcherService.test.ts` - Mock chokidar events
- [ ] T076 [P] [US3] Unit test: Test debounce logic (400ms delay)
- [ ] T077 [P] [US3] Unit test: Test exclude patterns (node_modules, .git, dist)
- [ ] T078 [US3] Integration test: `tests/integration/file-watching.test.ts` - Real file changes trigger re-embedding

#### Implementation
- [ ] T079 [US3] Implement FileWatcherService: Watch project directory, emit change events
- [ ] T080 [US3] Add debounce logic: Wait 400ms after last change before triggering
- [ ] T081 [US3] Add exclude patterns: Load from config.yaml, default to node_modules/, .git/, dist/, build/, .next/
- [ ] T082 [US3] Add event handlers: `src/infrastructure/file-watcher/event-handlers.ts` for create/modify/delete/rename
- [ ] T083 [US3] Integrate with ChunkingService: On file change → invalidate embeddings → re-chunk → re-embed
- [ ] T084 [US3] Add crash recovery: Auto-restart with exponential backoff (1s, 2s, 4s, 8s, 16s), max 5 retries
- [ ] T085 [US3] Handle renames: Delete old path embeddings, create new path embeddings, preserve access stats
- [ ] T086 [US3] Add performance metrics: Track events/sec, embeddings invalidated/sec, latency p50/p95/p99
- [ ] T087 [US3] Add logging: All events at DEBUG level, errors at ERROR level
- [ ] T088 [US3] Start watcher: Integrate with ServiceManager, auto-start on `kioku serve`
- [ ] T089 [US3] Add CLI control: `kioku serve --no-watch` flag to disable file watching
- [ ] T090 [US3] Update config schema: Add file_watcher.enabled, file_watcher.debounce_ms, file_watcher.exclude_patterns
- [ ] T091 [US3] Add health check: Expose file watcher status in `kioku doctor`

### Acceptance Criteria (FR-015 to FR-021)

- File changes detected within 100ms of OS event
- Debouncing prevents thrash during rapid saves
- Embeddings regenerated within 2s of file change
- Watcher auto-restarts on crash (max 5 retries)
- Rename events preserve access statistics
- Excluded directories configurable and working
- Performance: <1% CPU usage during idle watching
- All events logged at DEBUG level

### Technical Considerations

**Pros**:
- Best UX - zero manual intervention
- Always up-to-date context
- Professional tool expectation

**Cons**:
- OS-specific quirks (especially Windows)
- Performance impact on large projects (10k+ files)
- Adds system dependency (file watching daemon)

**Recommendation**: Implement in v2.1 after v2.0 adoption validates need

---

## Phase 6: AI-Enhanced Discovery 🤖

**Priority**: Medium (Nice-to-have enhancement)  
**Status**: Client skeleton exists, refinement logic deferred  
**Target**: v2.1

### User Story (US4)

**As a** developer reviewing session discoveries  
**I want** AI to refine and validate extracted patterns  
**So that** project.yaml only contains high-quality, relevant discoveries

### Business Value

- **Higher accuracy**: AI validates regex-extracted discoveries
- **Better categorization**: AI maps discoveries to correct modules
- **Richer context**: AI adds supporting evidence and confidence scores
- **Reduced noise**: Low-confidence discoveries filtered out

### Why Deferred

1. **Cost**: Every session sent to Claude API = expensive ($0.001-0.015 per session)
2. **Not essential**: Regex extraction (v1.0) works adequately
3. **API dependency**: Adds external service dependency
4. **Privacy**: Requires sending code context to Anthropic

### What's Already Done

- ✅ T028: AnthropicClient skeleton created
- ✅ T034: IAIClient port defined
- ✅ T014: RefinedDiscovery domain model
- ✅ T019: refined_discoveries database table
- ✅ Dependencies: `anthropic` SDK installed

### Remaining Tasks (T092-T103)

#### Tests (TDD - Write First)
- [ ] T092 [P] [US4] Unit test: `tests/unit/infrastructure/external/anthropic-client.test.ts` - Mock API responses
- [ ] T093 [P] [US4] Unit test: Test prompt construction with session context
- [ ] T094 [P] [US4] Unit test: Test sensitive data redaction (API keys, emails, IPs)
- [ ] T095 [US4] Integration test: `tests/integration/ai-discovery.test.ts` - Real API call with test session

#### Implementation
- [ ] T096 [US4] Implement AnthropicClient.refineDiscoveries(): Send session + regex discoveries, receive refined list
- [ ] T097 [US4] Add prompt engineering: Construct prompt with: regex discoveries, last 50 messages, current project.yaml
- [ ] T098 [US4] Add sensitive data redaction: Regex patterns for API keys (sk-, pk-, Bearer), emails, phones, IPs, SSNs
- [ ] T099 [US4] Add allow-list: Load from config.yaml to override false positive redactions
- [ ] T100 [US4] Add confidence filtering: Only persist discoveries with confidence >= 0.6
- [ ] T101 [US4] Add fallback: If API fails (rate limit, network), fall back to regex-only extraction
- [ ] T102 [US4] Add caching: Cache AI responses per session to avoid re-processing on retry
- [ ] T103 [US4] Integrate with ExtractDiscoveries: After regex extraction, call AI refinement, merge results

### Acceptance Criteria (FR-022 to FR-028)

- AI refinement returns: type, confidence (0-1), refined description, module, evidence
- Only discoveries with confidence >= 0.6 persisted
- Sensitive data redacted: API keys, emails, phones, IPs, credit cards, SSNs
- Allow-list overrides false positives
- Fallback to regex-only if API unavailable
- Results cached per session
- Average latency <3s per session

### Cost Analysis

**Per Session**:
- Input: ~2000 tokens (50 messages + context)
- Output: ~500 tokens (refined discoveries)
- Cost: ~$0.0075 per session (Claude 3 Sonnet)

**Monthly (Heavy User)**:
- 20 sessions/day × 30 days = 600 sessions
- Cost: ~$4.50/month per heavy user

**Mitigation**: Add config flag `ai_discovery.enabled: false` (default off)

### Technical Considerations

**Pros**:
- Dramatically improves discovery quality
- Reduces false positives
- Better module mapping

**Cons**:
- Adds recurring API cost
- Privacy implications (code sent to Anthropic)
- Latency (2-3s per session)
- Requires API key management

**Recommendation**: Implement as **opt-in** feature in v2.1, disabled by default

---

## Phase 7: Intelligent Result Ranking 🎯

**Priority**: Low (Optimization, not foundational)  
**Status**: Not started  
**Target**: v2.1

### User Story (US5)

**As a** developer searching for code  
**I want** results ranked by relevance (recency, module, frequency)  
**So that** most useful results appear first

### Business Value

- **Better precision**: Top 3 results hit rate improves from 60% → 85%
- **Faster navigation**: Less scrolling through irrelevant results
- **Context-aware**: Results adapt to what you're currently working on

### Why Deferred

1. **Search already works**: Semantic search is functional without ranking
2. **Data needed**: Requires usage data to validate boost factors
3. **Incremental value**: 20% improvement vs 200% (from chunking)
4. **Optimization**: Tune after collecting real-world usage patterns

### Remaining Tasks (T104-T114)

#### Tests (TDD - Write First)
- [ ] T104 [P] [US5] Unit test: `tests/unit/domain/calculations/result-ranker.test.ts` - Test recency boost
- [ ] T105 [P] [US5] Unit test: Test module boost (current module detection)
- [ ] T106 [P] [US5] Unit test: Test frequency boost (access count)
- [ ] T107 [US5] Integration test: `tests/integration/ranking.test.ts` - Search returns ranked results

#### Implementation
- [ ] T108 [US5] Implement result-ranker: `src/domain/calculations/result-ranker.ts` with rankResults()
- [ ] T109 [US5] Add recency boost: 1.5x (24h), 1.2x (7d), 1.0x (older) based on last_accessed_at
- [ ] T110 [US5] Add module boost: 1.3x if result matches current module (detect from file path context)
- [ ] T111 [US5] Add frequency boost: `1 + (access_count / 100)` capped at 1.5x
- [ ] T112 [US5] Combine boosts: `final_score = semantic_score × recency × module × frequency`
- [ ] T113 [US5] Update SearchContext: Apply ranking after semantic search, before return
- [ ] T114 [US5] Add ranking metadata: Include boost factors in search response for debugging

### Acceptance Criteria (FR-029 to FR-033)

- Recency boost applied correctly (1.5x, 1.2x, 1.0x)
- Module boost detects current module from file path
- Frequency boost caps at 1.5x
- Boosts multiply: final = semantic × recency × module × frequency
- Top 3 results hit rate >= 85%
- Ranking details logged at DEBUG level

### Boost Factor Tuning

**Recency** (Last accessed):
- < 24h: 1.5x (working on it now)
- < 7d: 1.2x (recent work)
- Older: 1.0x (baseline)

**Module** (Current context):
- Same module: 1.3x
- Different module: 1.0x

**Frequency** (Access count):
- Formula: `1 + (count / 100)` capped at 1.5x
- 0 accesses: 1.0x
- 50 accesses: 1.5x
- 100+ accesses: 1.5x (cap)

**Example Calculation**:
```
Semantic score: 0.82
Recency: 1.5x (accessed 2h ago)
Module: 1.3x (same module)
Frequency: 1.2x (20 accesses)

Final: 0.82 × 1.5 × 1.3 × 1.2 = 1.92
```

### Technical Considerations

**Pros**:
- Improves search precision significantly
- Adapts to user behavior over time
- Low computational cost

**Cons**:
- Requires usage data to validate
- Boost factors may need tuning
- Adds complexity to search pipeline

**Recommendation**: Implement in v2.1 after collecting 2-4 weeks of usage data

---

## Phase 8: Full Observability 📊

**Priority**: Low (Production monitoring)  
**Status**: 50% complete (basic metrics exist)  
**Target**: v2.2

### What's Already Done

- ✅ T026: metrics-registry.ts with prom-client
- ✅ T027: metrics-server.ts skeleton with Fastify
- ✅ Basic custom metrics tracking

### Remaining Work (T115-T127)

**Metrics to Add**:
- [ ] T115-T118: Embedding queue depth, API latency (p50/p95/p99), error rates
- [ ] T119-T121: File watcher events/sec, git tool usage, search latency
- [ ] T122-T124: Chunk statistics, context window usage
- [ ] T125-T127: Session duration, discoveries/session, health check endpoints

**Target**: Full Prometheus integration with Grafana dashboards

---

## Phase 9: Multi-Project Workspaces 🏢

**Priority**: Low (Enterprise/power users)  
**Status**: 30% complete (data models exist)  
**Target**: v2.2

### What's Already Done

- ✅ T015: LinkedProject domain model
- ✅ T020: linked_projects database tables
- ✅ T030: workspace-storage.ts adapter

### Remaining Work (T128-T145)

**Features to Implement**:
- [ ] T128-T132: Workspace.yaml CRUD, project linking
- [ ] T133-T137: Cross-project search, shared discoveries
- [ ] T138-T141: Project groups, dependency tracking
- [ ] T142-T145: Workspace CLI commands, health checks

**Use Case**: Link frontend/backend/mobile repos, search across all

---

## Implementation Priority Recommendation

### v2.1 (Q1 2025) - Enhanced Intelligence
**Theme**: Make Kioku smarter and more responsive

1. **Phase 5: File Watching** (~7 days)
   - Highest UX impact
   - Most requested feature
   - Technical risk managed by auto-restart

2. **Phase 7: Ranking** (~4 days)  
   - Quick win, high value
   - Requires 2 weeks usage data first
   - Low risk implementation

3. **Phase 6: AI Discovery** (~5 days)
   - Opt-in feature
   - Requires cost analysis
   - Privacy policy update

**Total**: ~16 days, 3 sprints

### v2.2 (Q2 2025) - Enterprise Ready
**Theme**: Scale to teams and production

1. **Phase 8: Full Monitoring** (~3 days)
   - Production requirement
   - Grafana dashboards
   - SLO/SLA tracking

2. **Phase 9: Multi-Project** (~7 days)
   - Enterprise feature
   - Workspace management
   - Cross-repo intelligence

**Total**: ~10 days, 2 sprints

---

## How to Resume Deferred Work

### 1. Pick a Phase

Choose from the table above based on priority and available time.

### 2. Review Task List

All tasks are in `.specify/specs/002-advanced-context-intelligence/tasks.md`

### 3. Start with Tests

Every phase follows TDD:
```bash
# Example: Starting Phase 5 (File Watching)
# 1. Write tests first (T075-T078)
# 2. See them fail (RED)
# 3. Implement (T079-T091)
# 4. See them pass (GREEN)
# 5. Refactor
```

### 4. Use SpecKit

```bash
# Verify task status
grep "T075-T091" .specify/specs/002-advanced-context-intelligence/tasks.md

# Run analysis
/speckit.analyze

# Track implementation
# Update tasks.md as you complete each task
```

### 5. Quality Gates

Before considering any phase complete:
- ✅ All tests passing (90%+ coverage)
- ✅ TypeScript strict mode compliant
- ✅ ESLint passing (architecture boundaries)
- ✅ Documentation updated (README, CHANGELOG)
- ✅ Manual testing completed

---

## Questions or Prioritization Changes?

This document is a living spec. Update priorities based on:
- User feedback and feature requests
- Production metrics and pain points  
- Competitive landscape
- Team capacity

**Source of Truth**: `.specify/specs/002-advanced-context-intelligence/`

**Last Updated**: 2025-10-11 (v2.0 release)
