# Advanced Search Techniques for Better Retrieval using SQL

This document outlines the SQL-based search capabilities in Memori v1.0, focusing on efficient memory retrieval without vector databases.

## Core Search Strategies

### 1. Full-Text Search (FTS5)

Memori v1.0 uses SQLite's FTS5 for advanced text search capabilities:

```sql
-- Search across all memory content
SELECT memory_id, memory_type, searchable_content, summary, category_primary
FROM memory_search_fts 
WHERE memory_search_fts MATCH ?
ORDER BY rank;
```

**Benefits:**
- Fast text search across large datasets
- Supports phrase queries, boolean operators
- Automatic ranking by relevance

### 2. Entity-Based Search

Search memories by specific entities (people, technologies, topics, skills, projects):

```sql
-- Find memories related to specific entities
SELECT m.memory_id, m.processed_data, m.importance_score, m.created_at,
       e.entity_type, e.entity_value, e.relevance_score
FROM long_term_memory m
JOIN memory_entities e ON m.memory_id = e.memory_id
WHERE e.entity_value LIKE ? AND e.entity_type = ?
ORDER BY e.relevance_score DESC, m.importance_score DESC;
```

**Use Cases:**
- "Find all memories about Python"
- "What projects has John worked on?"
- "Show me machine learning related conversations"

### 3. Category-Based Filtering

Filter memories by primary categories:

```sql
-- Search within specific memory categories
SELECT memory_id, processed_data, importance_score, created_at
FROM long_term_memory 
WHERE category_primary = ? 
  AND searchable_content LIKE ?
ORDER BY importance_score DESC, created_at DESC;
```

**Categories:**
- `fact`: Factual information, definitions, technical details
- `preference`: User preferences, settings, personal choices
- `skill`: Skills, abilities, learning progress
- `context`: Project context, work environment
- `rule`: Rules, policies, procedures, guidelines

### 4. Importance-Based Ranking

Prioritize high-importance memories:

```sql
-- Get high-importance memories first
SELECT memory_id, processed_data, importance_score, 
       novelty_score, relevance_score, actionability_score
FROM long_term_memory 
WHERE importance_score > 0.7
  AND (searchable_content LIKE ? OR summary LIKE ?)
ORDER BY importance_score DESC, novelty_score DESC;
```

### 5. Temporal Search

Search memories within specific time ranges:

```sql
-- Recent memories (last 30 days)
SELECT memory_id, processed_data, created_at, last_accessed
FROM long_term_memory 
WHERE created_at >= datetime('now', '-30 days')
  AND searchable_content LIKE ?
ORDER BY created_at DESC;

-- Frequently accessed memories
SELECT memory_id, processed_data, access_count, last_accessed
FROM long_term_memory 
WHERE access_count > 5
  AND searchable_content LIKE ?
ORDER BY access_count DESC, last_accessed DESC;
```

### 6. Hybrid Search Combinations

Combine multiple search strategies for better results:

```sql
-- Multi-dimensional search
WITH ranked_memories AS (
  -- FTS search results
  SELECT m.memory_id, m.processed_data, m.importance_score, 
         m.category_primary, m.created_at, 1.0 as search_score
  FROM memory_search_fts fts
  JOIN long_term_memory m ON fts.memory_id = m.memory_id AND fts.memory_type = 'long_term'
  WHERE fts MATCH ?
  
  UNION ALL
  
  -- Entity-based results
  SELECT m.memory_id, m.processed_data, m.importance_score,
         m.category_primary, m.created_at, e.relevance_score as search_score
  FROM long_term_memory m
  JOIN memory_entities e ON m.memory_id = e.memory_id
  WHERE e.entity_value LIKE ?
)
SELECT DISTINCT memory_id, processed_data, importance_score, 
       category_primary, created_at, MAX(search_score) as final_score
FROM ranked_memories
GROUP BY memory_id
ORDER BY final_score DESC, importance_score DESC
LIMIT ?;
```

## Search Query Optimization

### 1. Index Usage

Memori v1.0 includes optimized indexes for fast searches:

```sql
-- Leveraging composite indexes
EXPLAIN QUERY PLAN
SELECT memory_id FROM long_term_memory 
WHERE category_primary = 'skill' 
  AND importance_score > 0.5 
ORDER BY created_at DESC;
```

### 2. Query Performance Tips

**Use LIMIT for pagination:**
```sql
SELECT memory_id, summary FROM long_term_memory 
WHERE searchable_content LIKE '%python%'
ORDER BY importance_score DESC 
LIMIT 10 OFFSET ?;
```

**Prefer exact entity matches:**
```sql
-- Faster
WHERE entity_value = 'Python'
-- Slower  
WHERE entity_value LIKE '%Python%'
```

### 3. Search Result Scoring

Combine multiple relevance factors:

```sql
SELECT memory_id, processed_data,
       (importance_score * 0.4 + 
        novelty_score * 0.2 + 
        relevance_score * 0.3 + 
        actionability_score * 0.1) as composite_score
FROM long_term_memory 
WHERE searchable_content LIKE ?
ORDER BY composite_score DESC;
```

## Memory Retrieval Patterns

### 1. Context-Aware Retrieval

Get relevant context for new queries:

```sql
-- Get recent short-term memories for context
SELECT processed_data, created_at FROM short_term_memory 
WHERE namespace = ? 
ORDER BY created_at DESC LIMIT 5;

-- Get relevant rules and preferences
SELECT rule_text, rule_type, priority FROM rules_memory 
WHERE active = 1 AND namespace = ?
ORDER BY priority DESC;
```

### 2. Progressive Search

Start broad, then narrow down:

```sql
-- 1. Quick category check
SELECT COUNT(*) as memory_count, category_primary
FROM long_term_memory 
WHERE searchable_content LIKE ?
GROUP BY category_primary
ORDER BY memory_count DESC;

-- 2. Focused search in top categories
SELECT memory_id, summary, importance_score
FROM long_term_memory 
WHERE category_primary IN (?, ?) 
  AND searchable_content LIKE ?
ORDER BY importance_score DESC;
```

### 3. Relationship-Aware Search

Use memory relationships for expanded results:

```sql
-- Find related memories through relationships
WITH target_memories AS (
  SELECT memory_id FROM long_term_memory 
  WHERE searchable_content LIKE ? LIMIT 5
)
SELECT DISTINCT m.memory_id, m.summary, m.importance_score,
       r.relationship_type, r.strength
FROM long_term_memory m
JOIN memory_relationships r ON (
  r.target_memory_id = m.memory_id OR r.source_memory_id = m.memory_id
)
JOIN target_memories t ON (
  r.source_memory_id = t.memory_id OR r.target_memory_id = t.memory_id
)
WHERE m.memory_id NOT IN (SELECT memory_id FROM target_memories)
ORDER BY r.strength DESC, m.importance_score DESC;
```

## Best Practices

### 1. Query Construction
- Use parameterized queries to prevent SQL injection
- Combine FTS with entity search for comprehensive results
- Always include LIMIT to prevent performance issues

### 2. Result Processing
- Cache frequently accessed memories
- Update access_count and last_accessed for usage tracking
- Process search results through importance scoring

### 3. Performance Monitoring
- Monitor query execution times
- Use EXPLAIN QUERY PLAN for optimization
- Regular VACUUM and ANALYZE for SQLite maintenance

This SQL-based approach provides robust search capabilities while maintaining simplicity and performance for Memori v1.0.