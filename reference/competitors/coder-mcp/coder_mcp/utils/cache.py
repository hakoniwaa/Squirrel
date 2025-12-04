#!/usr/bin/env python3
"""
Thread-Safe Caching Utilities
Extracted from the original server for modularity
"""

import logging
import threading
import time
from collections import Counter
from typing import Any, Dict, Optional, Tuple

logger = logging.getLogger(__name__)


class ThreadSafeCache:
    """Thread-safe cache with TTL support and automatic eviction"""

    def __init__(self, max_size: int = 1000, default_ttl: int = 3600):
        self._lock = threading.RLock()
        self._cache: Dict[str, Any] = {}
        self._timestamps: Dict[str, Tuple[float, int]] = {}  # (timestamp, ttl)
        self._max_size = max_size
        self._default_ttl = default_ttl

    def get(self, key: str) -> Optional[Any]:
        """Get item from cache with TTL check"""
        with self._lock:
            if key in self._cache:
                timestamp, ttl = self._timestamps[key]
                if time.time() - timestamp < ttl:
                    return self._cache[key]
                else:
                    # Expired, remove
                    del self._cache[key]
                    del self._timestamps[key]
            return None

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set item in cache with TTL"""
        with self._lock:
            # Evict if at max size
            if len(self._cache) >= self._max_size and key not in self._cache:
                self._evict_oldest()

            self._cache[key] = value
            self._timestamps[key] = (time.time(), ttl or self._default_ttl)

    def _evict_oldest(self) -> None:
        """Evict the oldest entry (LRU-style)"""
        if not self._timestamps:
            return

        oldest_key = min(self._timestamps.keys(), key=lambda k: self._timestamps[k][0])
        del self._cache[oldest_key]
        del self._timestamps[oldest_key]

    def clear(self) -> None:
        """Clear all cache entries"""
        with self._lock:
            self._cache.clear()
            self._timestamps.clear()

    def size(self) -> int:
        """Get current cache size"""
        with self._lock:
            return len(self._cache)

    def cleanup_expired(self) -> int:
        """Remove expired entries and return count of removed items"""
        removed_count = 0
        current_time = time.time()

        with self._lock:
            expired_keys = []
            for key, (timestamp, ttl) in self._timestamps.items():
                if current_time - timestamp >= ttl:
                    expired_keys.append(key)

            for key in expired_keys:
                del self._cache[key]
                del self._timestamps[key]
                removed_count += 1

        if removed_count > 0:
            logger.debug(f"Cleaned up {removed_count} expired cache entries")

        return removed_count

    def stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        with self._lock:
            total_size = len(self._cache)
            if total_size == 0:
                return {
                    "size": 0,
                    "max_size": self._max_size,
                    "hit_rate": 0.0,
                    "expired_entries": 0,
                }

            current_time = time.time()
            expired_count = sum(
                1 for timestamp, ttl in self._timestamps.values() if current_time - timestamp >= ttl
            )

            return {
                "size": total_size,
                "max_size": self._max_size,
                "utilization": total_size / self._max_size,
                "expired_entries": expired_count,
            }


class ThreadSafeMetrics:
    """Thread-safe metrics collection with bounded memory"""

    def __init__(self, max_tool_count: int = 100, max_latencies: int = 500):
        self._lock = threading.RLock()
        self._metrics: Dict[str, Any] = {
            "cache_hits": 0,
            "cache_misses": 0,
            "redis_operations": 0,
            "vector_searches": 0,
            "tool_usage": Counter(),
            "latencies": [],
        }
        self._max_tool_count = max_tool_count
        self._max_latencies = max_latencies

    def increment(self, metric_name: str, value: int = 1) -> None:
        """Thread-safe metric increment"""
        with self._lock:
            if metric_name in ["cache_hits", "cache_misses", "redis_operations", "vector_searches"]:
                self._metrics[metric_name] += value
            else:
                # Handle arbitrary metrics for extensibility
                if metric_name not in self._metrics:
                    self._metrics[metric_name] = 0
                self._metrics[metric_name] += value

    def track_tool_usage(self, tool_name: str) -> None:
        """Thread-safe tool usage tracking with bounded memory"""
        with self._lock:
            # Limit tool usage tracking to prevent memory growth
            if len(self._metrics["tool_usage"]) > self._max_tool_count:
                # Keep only top 50% tools
                keep_count = self._max_tool_count // 2
                top_tools = dict(self._metrics["tool_usage"].most_common(keep_count))
                self._metrics["tool_usage"] = Counter(top_tools)

            self._metrics["tool_usage"][tool_name] += 1

    def track_latency(self, latency_ms: float) -> None:
        """Thread-safe latency tracking with bounded memory"""
        with self._lock:
            self._metrics["latencies"].append(latency_ms)
            # Keep only recent latencies to prevent memory leak
            if len(self._metrics["latencies"]) > self._max_latencies:
                self._metrics["latencies"] = self._metrics["latencies"][-self._max_latencies :]

    def get_snapshot(self) -> Dict[str, Any]:
        """Get thread-safe snapshot of metrics"""
        with self._lock:
            # Create a deep copy of all metrics
            snapshot = {}

            for key, value in self._metrics.items():
                if key == "tool_usage":
                    snapshot[key] = dict(value)  # Convert Counter to dict
                elif key == "latencies":
                    snapshot[key] = value.copy()  # Copy the list
                else:
                    snapshot[key] = value  # Copy primitive values

            return snapshot

    def reset(self) -> None:
        """Reset all metrics"""
        with self._lock:
            self._metrics = {
                "cache_hits": 0,
                "cache_misses": 0,
                "redis_operations": 0,
                "vector_searches": 0,
                "tool_usage": Counter(),
                "latencies": [],
            }

    def should_save_metrics(self, interval: int = 100) -> bool:
        """Check if metrics should be saved (thread-safe)"""
        with self._lock:
            redis_ops = self._metrics.get("redis_operations", 0)
            if isinstance(redis_ops, int):
                return redis_ops % interval == 0
            return False

    def get_performance_summary(self) -> Dict[str, Any]:
        """Get a performance summary with calculated metrics"""
        snapshot = self.get_snapshot()

        # Calculate derived metrics
        cache_hits = int(snapshot.get("cache_hits", 0))
        cache_misses = int(snapshot.get("cache_misses", 0))
        total_cache_ops = cache_hits + cache_misses
        cache_hit_rate = cache_hits / max(1, total_cache_ops)

        latencies = snapshot.get("latencies", [])
        if isinstance(latencies, list):
            avg_latency = sum(latencies) / max(1, len(latencies))
        else:
            avg_latency = 0.0

        tool_usage = snapshot.get("tool_usage", {})
        if isinstance(tool_usage, dict):
            total_operations = sum(tool_usage.values())
            top_tools = dict(Counter(tool_usage).most_common(5))
        else:
            total_operations = 0
            top_tools = {}

        return {
            "cache_hit_rate": cache_hit_rate,
            "avg_latency_ms": avg_latency,
            "total_operations": total_operations,
            "top_tools": top_tools,
            "redis_operations": snapshot.get("redis_operations", 0),
            "vector_searches": snapshot.get("vector_searches", 0),
        }
