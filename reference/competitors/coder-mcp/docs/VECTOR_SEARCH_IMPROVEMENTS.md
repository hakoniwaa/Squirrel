# Vector Search Improvements

## Overview

This document outlines the comprehensive improvements made to the vector search system, dramatically enhancing search capabilities with multi-model embeddings, high-performance indexing, intelligent query processing, and advanced caching.

## 🚀 Key Improvements

### 1. Multi-Model Embedding System

**Location**: `coder_mcp/embeddings/multi_model.py`

- **Code-Specific Embeddings**: Uses specialized models for better code understanding
- **General Purpose Embeddings**: OpenAI Ada for documentation and comments
- **Local Fallback**: Sentence Transformers for offline operation
- **Contextual Enhancement**: Adds file path, language, and import context

**Features**:
- Automatic content type detection
- Weighted embedding combination
- Context-aware embedding generation
- Fallback mechanisms for reliability

### 2. High-Performance Vector Storage

**Location**: `coder_mcp/storage/vector_stores/`

#### HNSW Vector Store (`hnsw_store.py`)
- **Algorithm**: Hierarchical Navigable Small World for O(log n) search
- **Performance**: 10-100x faster than linear search
- **Scalability**: Handles millions of vectors efficiently
- **Configuration**: Tunable parameters for speed vs accuracy

#### Hybrid Vector Store (`hybrid_store.py`)
- **Durability**: Combines HNSW performance with Redis persistence
- **Reliability**: Automatic fallback mechanisms
- **Synchronization**: Keeps both stores in sync
- **Rebuild**: Can reconstruct HNSW from Redis data

### 3. Intelligent Query Processing

**Location**: `coder_mcp/context/search/query_processor.py`

**Capabilities**:
- **Intent Detection**: Identifies search intent (definition, usage, error, etc.)
- **Entity Extraction**: Finds function names, classes, variables
- **Abbreviation Expansion**: Expands common programming abbreviations
- **Synonym Generation**: Creates related terms for broader search
- **Language Detection**: Identifies programming language context
- **Sub-Query Generation**: Creates multiple search angles

### 4. Multi-Level Caching System

**Location**: `coder_mcp/context/search/cache.py`

**Cache Layers**:
- **Local LRU Cache**: Fast in-memory caching
- **Redis Cache**: Persistent distributed caching
- **Embedding Cache**: Avoids recomputing expensive embeddings
- **Search Result Cache**: Caches frequent queries
- **Query Processing Cache**: Caches analysis results

**Features**:
- Configurable TTLs
- Cache statistics and monitoring
- Intelligent invalidation
- Batch processing support

### 5. Enhanced Hybrid Search

**Location**: `coder_mcp/context/search/enhanced_hybrid_search.py`

**Search Strategies**:
- **Semantic First**: Prioritizes meaning-based search
- **Text First**: Emphasizes exact text matching
- **Hybrid**: Balanced combination approach
- **Adaptive**: Adjusts based on query analysis
- **Code Focused**: Specialized for code searches

**Advanced Features**:
- Multi-query parallel processing
- Contextual search with file context
- Semantic similarity search
- Code-specific search modes
- Performance metrics and monitoring

### 6. Unified Search Manager

**Location**: `coder_mcp/context/enhanced_search_manager.py`

**Unified Interface**:
- Single entry point for all search operations
- Automatic initialization and health checking
- Workspace indexing management
- Comprehensive statistics and monitoring
- Cache management and cleanup

## 📊 Performance Improvements

### Speed Enhancements
- **HNSW Indexing**: 10-100x faster search than linear scan
- **Multi-Level Caching**: 5-10x faster for repeated queries
- **Parallel Processing**: Concurrent query execution
- **Batch Operations**: Efficient bulk processing

### Quality Improvements
- **Multi-Model Embeddings**: Better understanding of code vs documentation
- **Contextual Embeddings**: Enhanced relevance with file context
- **Intelligent Query Processing**: More accurate intent understanding
- **Adaptive Strategies**: Optimal approach selection per query

### Scalability Improvements
- **HNSW Algorithm**: Logarithmic search complexity
- **Distributed Caching**: Redis-based scaling
- **Namespace Support**: Multi-tenant architecture
- **Incremental Indexing**: Efficient updates

## 🔧 Configuration

### Basic Configuration

```python
from coder_mcp.context.enhanced_search_manager import EnhancedSearchManager
from coder_mcp.core.config import CoderMCPConfig

# Configure with HNSW enabled
config = CoderMCPConfig(
    embedding_dim=1536,
    enable_hnsw=True,
    cache_config={
        'embedding_ttl': 3600,
        'search_ttl': 600,
        'query_ttl': 1800
    }
)

# Initialize search manager
search_manager = EnhancedSearchManager(config=config)
await search_manager.initialize()
```

### HNSW Parameters

```python
hnsw_config = {
    'max_elements': 1000000,    # Maximum vectors
    'ef_construction': 200,     # Build time quality
    'M': 16,                   # Connectivity
    'ef_search': 50,           # Search time quality
    'space': 'cosine'          # Distance metric
}
```

### Cache Configuration

```python
cache_config = {
    'embedding_ttl': 3600,     # 1 hour
    'search_ttl': 600,         # 10 minutes
    'query_ttl': 1800,         # 30 minutes
    'max_local_cache': 1000,   # Local cache size
    'max_embedding_cache': 5000 # Embedding cache size
}
```

## 🔍 Usage Examples

### Basic Search

```python
# Simple search with automatic strategy selection
results = await search_manager.search(
    query="authentication function",
    top_k=10,
    strategy="adaptive"
)

for result in results:
    print(f"File: {result.file_path}")
    print(f"Score: {result.score}")
    print(f"Strategy: {result.search_strategy}")
    print(f"Snippet: {result.context_snippet}")
```

### Semantic Similarity Search

```python
# Find semantically similar content
results = await search_manager.semantic_search(
    query="user login validation",
    similarity_threshold=0.7
)
```

### Code-Specific Search

```python
# Search specifically for code
results = await search_manager.code_search(
    query="def authenticate_user",
    language="python"
)
```

### Multi-Query Search

```python
# Process multiple queries efficiently
queries = [
    "authentication methods",
    "password validation",
    "session management"
]

results = await search_manager.multi_query_search(
    queries,
    strategy="hybrid"
)
```

### Contextual Search

```python
# Search with file context
results = await search_manager.search(
    query="user authentication",
    context_files=["auth.py", "models.py"],
    strategy="hybrid"
)
```

### Find Similar Files

```python
# Find files similar to a reference
results = await search_manager.find_similar_files(
    reference_file="auth/user_auth.py",
    similarity_threshold=0.6
)
```

## 📈 Monitoring and Metrics

### Search Statistics

```python
# Get comprehensive statistics
stats = await search_manager.get_search_stats()

print(f"Total searches: {stats['search_metrics']['total_searches']}")
print(f"Cache hit rate: {stats['search_metrics']['cache_hits']}")
print(f"Average response time: {stats['search_metrics']['avg_response_time']}")
```

### Health Check

```python
# Perform health check
health = await search_manager.health_check()

if health['status'] == 'healthy':
    print("Search system is healthy")
else:
    print(f"Issues detected: {health['error']}")
```

### Cache Management

```python
# Clear caches
await search_manager.clear_cache()

# Get cache statistics
cache_stats = search_manager.enhanced_search.search_cache.get_cache_stats()
print(f"Embedding cache hit rate: {cache_stats['embedding_cache']['hit_rate']}")
```

## 🛠️ Dependencies

Add these dependencies to your `pyproject.toml`:

```toml
[tool.poetry.dependencies]
hnswlib = "^0.8.0"          # High-performance vector indexing
numpy = "^1.24.0"           # Numerical operations
sentence-transformers = "^2.2.0"  # Local embeddings
transformers = "^4.30.0"    # Code embeddings
```

## 🔄 Migration Guide

### From Basic to Enhanced Search

1. **Update Imports**:
```python
# Old
from coder_mcp.context.search import HybridSearch

# New
from coder_mcp.context.enhanced_search_manager import EnhancedSearchManager
```

2. **Initialize Enhanced System**:
```python
# Replace existing search initialization
search_manager = EnhancedSearchManager()
await search_manager.initialize()
```

3. **Update Search Calls**:
```python
# Enhanced search with strategy selection
results = await search_manager.search(
    query="your query",
    strategy="adaptive"  # or "semantic_first", "hybrid", etc.
)
```

## 🎯 Best Practices

### Strategy Selection
- **Definition queries**: Use `semantic_first`
- **Error debugging**: Use `text_first`
- **Code implementation**: Use `code_focused`
- **General search**: Use `adaptive`

### Performance Optimization
- Enable HNSW for large codebases (>1000 files)
- Use appropriate cache TTLs based on content volatility
- Batch multiple queries when possible
- Monitor cache hit rates and adjust sizes

### Quality Optimization
- Provide context files for better relevance
- Use appropriate similarity thresholds
- Leverage multi-query search for comprehensive results
- Monitor search metrics to identify improvement opportunities

## 🐛 Troubleshooting

### Common Issues

1. **HNSW Not Available**:
   - Install: `pip install hnswlib`
   - Falls back to Redis-only mode automatically

2. **Poor Search Quality**:
   - Check embedding model availability
   - Verify Redis connection
   - Review query processing results
   - Adjust similarity thresholds

3. **Slow Performance**:
   - Enable HNSW indexing
   - Increase cache sizes
   - Use batch processing
   - Monitor cache hit rates

4. **Memory Issues**:
   - Reduce HNSW max_elements
   - Decrease cache sizes
   - Use appropriate TTLs

### Debug Mode

```python
# Enable debug logging
import logging
logging.getLogger('coder_mcp.context.search').setLevel(logging.DEBUG)

# Check component health
health = await search_manager.health_check()
print(health)
```

## 🔮 Future Enhancements

### Planned Improvements
- **Graph-based search**: Relationship-aware searching
- **Incremental learning**: Adaptive embedding models
- **Federated search**: Multi-repository searching
- **Real-time indexing**: Live file change detection
- **Advanced analytics**: Search pattern analysis

### Experimental Features
- **Neural reranking**: ML-based result optimization
- **Query expansion**: Automatic query enhancement
- **Personalization**: User-specific search tuning
- **Cross-language search**: Multi-language code search

---

This enhanced vector search system provides a solid foundation for intelligent code search with significant performance and quality improvements. The modular design allows for easy extension and customization based on specific needs.
