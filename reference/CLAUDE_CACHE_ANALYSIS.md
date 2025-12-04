# claude-cache Learning Analysis

## Overview
claude-cache is the most important competitor for Squirrel - it's the ONLY project doing passive log-based learning with success detection. Despite having 0 stars, it solved the core problem we face.

**Repository**: https://github.com/jasonjmcghee/claude-cache
**Threat Level**: HIGH - directly competes with Squirrel's approach

## Core Insight: Success Detection

The fundamental problem with passive learning from AI tool logs:
- User tries 5 approaches, only #5 works
- Without success detection: Store all 5 as "patterns" (4 are wrong!)
- With success detection: Store #1-4 as pitfalls, #5 as recipe

**This is the core insight that makes claude-cache valuable and what Squirrel must implement.**

## Key Files Analyzed

### Success Detection System
- `src/claude_cache/success_detector.py` - Keyword-based success detection
- `src/claude_cache/intelligent_detector.py` - Multi-signal fusion approach
- `src/claude_cache/behavioral_detector.py` - Implicit success signals
- `src/claude_cache/conversation_analyzer.py` - Conversation flow analysis

### Log Processing
- `src/claude_cache/log_watcher.py` - Watches ~/.claude/projects/**/*.jsonl
- `src/claude_cache/log_processor.py` - Parses JSONL, extracts events

### MCP Integration
- `src/claude_cache/claude_code_mcp.py` - FastMCP server with tools

## Success Detection Patterns

### Explicit Success Signals
```python
success_indicators = {
    'test_keywords': ['passed', 'success', '✓', 'ok'],
    'completion_keywords': ['done', 'completed', 'finished', 'works', 'fixed'],
    'user_satisfaction': ['thanks', 'perfect', 'great', 'that worked', 'exactly'],
}
```

### Explicit Failure Signals
```python
failure_keywords = ['failed', 'error', 'broken', 'exception']
# Also: "That didn't work", "Still broken", "This is wrong"
```

### Implicit Success Signals (Behavioral)
```python
'implicit_success': ['now let', 'next', 'also', 'moving on'],
'workflow_progression': ['continue', 'proceed', 'go ahead'],
```

The key behavioral insight: **"AI says done + user moves to next task = implicit success"**

### Multi-Signal Fusion
```python
signal_weights = {
    'conversation_flow': 0.35,  # How conversation progressed
    'execution_results': 0.25,  # Test/build outputs
    'user_intent': 0.20,        # What user meant
    'behavioral_signals': 0.20  # User behavior patterns
}
```

## Pattern Classification

claude-cache classifies patterns by quality:

| Type | Confidence | Description |
|------|------------|-------------|
| Gold | 95-100% | Worked first time |
| Silver | 80-95% | 2-3 attempts |
| Bronze | 60-80% | 4+ attempts |
| Anti-pattern | 90-100% | Confirmed failure |
| Journey | 85-100% | Complete problem-solving sequence |

## Architecture Patterns for Squirrel

### 1. Dual-Path Learning
- SUCCESS → recipe/project_fact memories
- FAILURE → pitfall memories (what NOT to do)
- JOURNEY → capture complete problem-solving path

### 2. Detection Confidence Levels
```python
class DetectionConfidence(Enum):
    CERTAIN = "certain"      # > 90% confidence
    HIGH = "high"            # 70-90% confidence
    MEDIUM = "medium"        # 50-70% confidence
    LOW = "low"              # 30-50% confidence
    UNCERTAIN = "uncertain"  # < 30% confidence
```

### 3. IntelligentDetectionResult Structure
```python
@dataclass
class IntelligentDetectionResult:
    is_success: bool
    confidence: DetectionConfidence
    success_probability: float
    pattern_quality: str           # gold/silver/bronze/anti
    problem: str                   # What user was trying to do
    solution: str                  # What worked (or didn't)
    key_insights: List[str]        # Critical learnings
    evidence: Dict[str, Any]       # Supporting data
    recommendation: str            # Next action
```

## Key Differences from Squirrel

| Aspect | claude-cache | Squirrel |
|--------|--------------|----------|
| Language | Python only | Rust daemon + Python service |
| Storage | SQLite | SQLite + sqlite-vec |
| Embeddings | sentence-transformers | ONNX (portable) |
| CLI Support | Claude Code only | 4 CLIs (Claude, Codex, Gemini, Cursor) |
| Task Segmentation | Per-message analysis | Episode-based (4-hour window) |
| LLM Usage | Heavy (per-message) | Minimal (per-episode) |

## What Squirrel Should Adopt

1. **Success Detection as Core Feature**
   - Not optional - required for passive learning
   - LLM classifies outcomes: SUCCESS / FAILURE / UNCERTAIN

2. **Behavioral Signal Detection**
   - "AI says done + user moves on" = implicit success
   - Task transition without complaints = success
   - Same error reappears = failure

3. **Dual-Path Memory Extraction**
   - SUCCESS → recipe, project_fact
   - FAILURE → pitfall
   - UNCERTAIN → skip (not enough info)

4. **Pattern Quality Classification**
   - Track confidence levels
   - Gold/silver/bronze for retrieval ranking

## What Squirrel Should NOT Adopt

1. **Per-message LLM calls** - Too expensive, use episode batching
2. **Python-only architecture** - Need Rust for performance
3. **Claude Code only** - Support multiple CLIs
4. **Complex detector hierarchy** - Simplify to single Router Agent

## Implementation Priority

1. **CRITICAL**: Success detection in Router Agent INGEST mode
2. **HIGH**: Behavioral signal detection (implicit success)
3. **MEDIUM**: Pattern quality classification
4. **LOW**: Journey pattern tracking (v1.1)

## Conclusion

claude-cache's core insight - that passive learning REQUIRES success detection - is the most valuable pattern for Squirrel. Without knowing what succeeded, we'd blindly store all patterns including failed approaches.

The implementation is over-engineered (multiple detector classes, per-message LLM calls), but the concept is sound. Squirrel should simplify this to a single LLM call per Episode that:
1. Segments tasks within the episode
2. Classifies each task outcome
3. Extracts memories based on outcome

This is now reflected in Squirrel's DEVELOPMENT_PLAN.md and EXAMPLE.md.
