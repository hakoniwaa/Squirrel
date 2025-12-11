# Squirrel Memory Policy

Declarative configuration for memory lifecycle management. These parameters control CR-Memory behavior without code changes.

---

## Policy File Location

```
~/.sqrl/memory_policy.toml      # User-level defaults
<repo>/.sqrl/memory_policy.toml # Project-level overrides (optional)
```

Project-level policies override user-level for that project.

---

## Policy Schema

### POLICY-001: Promotion Rules

When to promote memories from `provisional` to `active` (and optionally `tier='long_term'`).

```toml
[promotion.default]
min_opportunities = 5      # Minimum tasks that could have used this memory
min_use_ratio     = 0.6    # use_count / opportunities >= this ratio
min_regret_hits   = 2      # Minimum suspected_regret_hits

[promotion.invariant]
# Invariants can be promoted faster (they're stable facts)
min_opportunities = 3
min_use_ratio     = 0.5
min_regret_hits   = 1

[promotion.guard]
# Guards need more evidence before becoming long-term
min_opportunities = 10
min_use_ratio     = 0.3
min_regret_hits   = 3
```

**Semantics:**
- Memory must have at least `min_opportunities` before evaluation
- `use_ratio = use_count / opportunities`
- If `use_ratio >= min_use_ratio` AND `regret_hits >= min_regret_hits` → promote

---

### POLICY-002: Deprecation Rules

When to deprecate memories that aren't proving useful.

```toml
[deprecation.default]
min_opportunities = 10     # Must have enough chances first
max_use_ratio     = 0.1    # If used less than 10% of opportunities → deprecate

[deprecation.guard]
# Guards are more tolerant (they might rarely fire but still be valuable)
min_opportunities = 20
max_use_ratio     = 0.05

[deprecation.note]
# Notes are less valuable, deprecate faster
min_opportunities = 5
max_use_ratio     = 0.2
```

**Semantics:**
- If `opportunities >= min_opportunities` AND `use_ratio <= max_use_ratio` → deprecate

---

### POLICY-003: Decay Rules

Time-based decay for inactive memories.

```toml
[decay.guard]
max_inactive_days = 90     # Deprecate if not used in 90 days

[decay.pattern]
max_inactive_days = 180    # Patterns can stay longer

[decay.note]
max_inactive_days = 60     # Notes decay fastest

[decay.preference]
max_inactive_days = 365    # User preferences are stable

[decay.invariant]
max_inactive_days = null   # Invariants don't decay by time (only by deprecation rules)
```

**Semantics:**
- If `last_used_at` is older than `max_inactive_days` → deprecate
- `null` means no time-based decay (only opportunity-based deprecation)

---

### POLICY-004: Regret Calculation Weights

Weights for `estimated_regret_saved` calculation.

```toml
[regret_weights]
alpha_errors  = 1.0        # Weight for error reduction
beta_retries  = 0.5        # Weight for retry reduction
gamma_tokens  = 0.001      # Weight for token savings (optional, v2)
```

**Calculation:**
```
delta_err   = max(0, avg_errors_per_opportunity - actual_errors)
delta_retry = max(0, avg_retries_per_opportunity - actual_retries)

estimated_regret_saved += alpha * delta_err + beta * delta_retry
```

---

### POLICY-005: TTL Defaults

Default TTL values when Memory Writer doesn't specify.

```toml
[ttl.default]
short_term_days = 30       # Default TTL for tier='short_term'
emergency_days  = 7        # Default TTL for tier='emergency' guards

[ttl.on_promotion]
extend_by_days = 180       # Extend TTL when promoted to active
remove_on_long_term = true # Remove TTL entirely for tier='long_term'
```

---

### POLICY-006: Retrieval Weights

Weights for memory ranking during retrieval.

```toml
[retrieval.weights]
semantic_similarity = 0.5  # Base weight for embedding similarity
status_active_boost = 0.2  # Boost for status='active' over 'provisional'
tier_boost = 0.15          # Boost for emergency/long_term over short_term
kind_boost = 0.1           # Boost for invariant/preference over pattern/note
use_count_factor = 0.05    # log(1 + use_count) multiplied by this
```

---

## Full Example

```toml
# ~/.sqrl/memory_policy.toml

# === Promotion ===
[promotion.default]
min_opportunities = 5
min_use_ratio     = 0.6
min_regret_hits   = 2

[promotion.invariant]
min_opportunities = 3
min_use_ratio     = 0.5
min_regret_hits   = 1

[promotion.guard]
min_opportunities = 10
min_use_ratio     = 0.3
min_regret_hits   = 3

# === Deprecation ===
[deprecation.default]
min_opportunities = 10
max_use_ratio     = 0.1

[deprecation.guard]
min_opportunities = 20
max_use_ratio     = 0.05

[deprecation.note]
min_opportunities = 5
max_use_ratio     = 0.2

# === Time-based Decay ===
[decay.guard]
max_inactive_days = 90

[decay.pattern]
max_inactive_days = 180

[decay.note]
max_inactive_days = 60

[decay.preference]
max_inactive_days = 365

[decay.invariant]
max_inactive_days = null

# === Regret Calculation ===
[regret_weights]
alpha_errors  = 1.0
beta_retries  = 0.5

# === TTL ===
[ttl.default]
short_term_days = 30
emergency_days  = 7

[ttl.on_promotion]
extend_by_days = 180
remove_on_long_term = true

# === Retrieval ===
[retrieval.weights]
semantic_similarity = 0.5
status_active_boost = 0.2
tier_boost = 0.15
kind_boost = 0.1
use_count_factor = 0.05
```

---

## Policy Override Rules

1. Project-level policy overrides user-level for that project
2. Missing sections fall back to user-level, then to hardcoded defaults
3. Policies are loaded once at daemon startup and cached
4. Use `sqrl policy reload` to reload without restart (v2)

---

## CR-Memory Algorithm Reference

```python
def evaluate_memory(m, metrics, policy):
    opp  = metrics.opportunities
    uses = metrics.use_count
    hits = metrics.suspected_regret_hits

    promo = policy.promotion.get(m.kind, policy.promotion.default)
    deprec = policy.deprecation.get(m.kind, policy.deprecation.default)
    decay = policy.decay.get(m.kind)

    # Not enough evidence yet
    if opp < promo.min_opportunities:
        # Check time-based decay only
        if decay and decay.max_inactive_days:
            if days_since(metrics.last_used_at) > decay.max_inactive_days:
                return 'deprecated'
        return None  # No change

    use_ratio = uses / opp if opp > 0 else 0

    # Promotion check
    if use_ratio >= promo.min_use_ratio and hits >= promo.min_regret_hits:
        return 'promote'  # provisional → active, maybe tier → long_term

    # Deprecation check
    if opp >= deprec.min_opportunities and use_ratio <= deprec.max_use_ratio:
        return 'deprecated'

    # Time-based decay
    if decay and decay.max_inactive_days:
        if days_since(metrics.last_used_at) > decay.max_inactive_days:
            return 'deprecated'

    return None  # No change
```
