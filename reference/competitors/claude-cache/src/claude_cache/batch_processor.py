"""
Batch processing for improved performance
Processes logs in batches rather than one at a time
"""

import time
from typing import List, Dict, Any
from collections import deque
from threading import Timer, Lock


class BatchProcessor:
    """
    Batch processor for log entries.
    Accumulates entries and processes them in batches for better performance.
    """

    def __init__(self, process_func, batch_size: int = 10, max_wait_seconds: float = 5.0):
        """
        Initialize batch processor.

        Args:
            process_func: Function to process a batch of entries
            batch_size: Maximum batch size before triggering processing
            max_wait_seconds: Maximum time to wait before processing partial batch
        """
        self.process_func = process_func
        self.batch_size = batch_size
        self.max_wait_seconds = max_wait_seconds

        self.batch = deque()
        self.lock = Lock()
        self.timer = None
        self.last_process_time = time.time()

    def add(self, entry: Dict[str, Any]):
        """Add an entry to the batch"""
        with self.lock:
            self.batch.append(entry)

            # Process if batch is full
            if len(self.batch) >= self.batch_size:
                self._process_batch()
            else:
                # Schedule processing if not already scheduled
                if self.timer is None:
                    self.timer = Timer(self.max_wait_seconds, self._timeout_process)
                    self.timer.start()

    def _process_batch(self):
        """Process the current batch"""
        with self.lock:
            if not self.batch:
                return

            # Cancel any pending timer
            if self.timer:
                self.timer.cancel()
                self.timer = None

            # Extract batch
            batch_to_process = list(self.batch)
            self.batch.clear()

            # Process outside of lock
            self.last_process_time = time.time()

        # Process the batch
        try:
            self.process_func(batch_to_process)
        except Exception as e:
            # Log error but don't crash
            print(f"Batch processing error: {e}")

    def _timeout_process(self):
        """Process batch when timeout occurs"""
        self._process_batch()

    def flush(self):
        """Force process any remaining entries"""
        self._process_batch()


class CachedPatternMatcher:
    """
    Cache pattern matching results to avoid reprocessing identical sessions.
    Uses LRU cache with configurable size.
    """

    def __init__(self, max_cache_size: int = 100):
        self.cache = {}
        self.access_order = deque()
        self.max_cache_size = max_cache_size

    def get_cached_result(self, session_hash: str) -> Any:
        """Get cached result if available"""
        if session_hash in self.cache:
            # Move to end (most recently used)
            self.access_order.remove(session_hash)
            self.access_order.append(session_hash)
            return self.cache[session_hash]
        return None

    def cache_result(self, session_hash: str, result: Any):
        """Cache a result"""
        # Check cache size
        if len(self.cache) >= self.max_cache_size:
            # Remove least recently used
            lru = self.access_order.popleft()
            del self.cache[lru]

        # Add new result
        self.cache[session_hash] = result
        self.access_order.append(session_hash)

    def compute_session_hash(self, entries: List[Dict]) -> str:
        """Compute hash for a session"""
        import hashlib
        import json

        # Create simplified representation
        simplified = []
        for entry in entries:
            simplified.append({
                'type': entry.get('type'),
                'content': entry.get('content', '')[:100]  # First 100 chars
            })

        # Compute hash
        data = json.dumps(simplified, sort_keys=True)
        return hashlib.md5(data.encode()).hexdigest()


class AsyncFileWriter:
    """
    Asynchronous file writing to reduce I/O blocking.
    Batches write operations and performs them in background.
    """

    def __init__(self, write_interval: float = 2.0):
        self.write_interval = write_interval
        self.pending_writes = {}
        self.lock = Lock()
        self.timer = None

    def queue_write(self, filepath: str, content: str):
        """Queue content to be written to file"""
        with self.lock:
            self.pending_writes[filepath] = content

            if self.timer is None:
                self.timer = Timer(self.write_interval, self._perform_writes)
                self.timer.start()

    def _perform_writes(self):
        """Perform all pending writes"""
        with self.lock:
            if not self.pending_writes:
                return

            writes_to_perform = dict(self.pending_writes)
            self.pending_writes.clear()
            self.timer = None

        # Perform writes
        for filepath, content in writes_to_perform.items():
            try:
                with open(filepath, 'w') as f:
                    f.write(content)
            except Exception as e:
                print(f"Write error for {filepath}: {e}")

    def flush(self):
        """Force write all pending data"""
        self._perform_writes()


class OptimizedLogProcessor:
    """
    Optimized log processor using batch processing and caching.
    """

    def __init__(self, knowledge_base, detector):
        self.kb = knowledge_base
        self.detector = detector

        # Initialize optimizers
        self.batch_processor = BatchProcessor(
            self._process_log_batch,
            batch_size=20,
            max_wait_seconds=3.0
        )

        self.pattern_cache = CachedPatternMatcher(max_cache_size=200)
        self.file_writer = AsyncFileWriter(write_interval=5.0)

    def add_log_entry(self, entry: Dict):
        """Add a log entry for processing"""
        self.batch_processor.add(entry)

    def _process_log_batch(self, entries: List[Dict]):
        """Process a batch of log entries"""
        # Group by session for efficiency
        sessions = self._group_by_session(entries)

        for session_id, session_entries in sessions.items():
            # Check cache first
            session_hash = self.pattern_cache.compute_session_hash(session_entries)
            cached_result = self.pattern_cache.get_cached_result(session_hash)

            if cached_result:
                # Use cached result
                self._store_pattern(cached_result)
            else:
                # Process and cache
                result = self.detector.detect_success(session_entries)
                if result[0]:  # If success detected
                    pattern = self._extract_pattern(session_entries, result)
                    self.pattern_cache.cache_result(session_hash, pattern)
                    self._store_pattern(pattern)

    def _group_by_session(self, entries: List[Dict]) -> Dict[str, List[Dict]]:
        """Group entries by session"""
        sessions = {}
        for entry in entries:
            session_id = entry.get('session_id', 'unknown')
            if session_id not in sessions:
                sessions[session_id] = []
            sessions[session_id].append(entry)
        return sessions

    def _extract_pattern(self, entries: List[Dict], detection_result: tuple) -> Dict:
        """Extract pattern from session"""
        success, strength, quality = detection_result

        return {
            'entries': entries,
            'success': success,
            'strength': strength.value,
            'quality': quality.value,
            'timestamp': time.time()
        }

    def _store_pattern(self, pattern: Dict):
        """Store pattern in knowledge base"""
        # Queue for async storage
        self.file_writer.queue_write(
            f"/tmp/pattern_{pattern['timestamp']}.json",
            str(pattern)
        )

    def flush(self):
        """Flush all pending operations"""
        self.batch_processor.flush()
        self.file_writer.flush()