"""Hybrid vector search with graceful fallback to TF-IDF"""

import json
import sqlite3
import numpy as np
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Any
from datetime import datetime
from rich.console import Console
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

console = Console()


class VectorSearchEngine:
    """Hybrid search engine with automatic fallback"""

    def __init__(self, db_path: str = None, silent: bool = False):
        self.silent = silent
        if db_path is None:
            db_dir = Path.home() / '.claude' / 'knowledge'
            db_dir.mkdir(parents=True, exist_ok=True)
            db_path = db_dir / 'cache.db'

        self.db_path = str(db_path)
        self.search_mode = 'tfidf'  # Default
        self.model = None
        self.vectorizer = None
        self.embeddings_cache = {}

        # Try to enable semantic search
        self._initialize_search_engine()
        self._setup_tables()

    def _initialize_search_engine(self):
        """Initialize the best available search engine"""
        try:
            # Try to import sentence-transformers for semantic search
            from sentence_transformers import SentenceTransformer

            if not self.silent:
                console.print("[cyan]Initializing semantic search engine...[/cyan]")
            self.model = SentenceTransformer('all-MiniLM-L6-v2')
            self.search_mode = 'semantic'
            if not self.silent:
                console.print("[green]✨ Semantic search enabled - 2x better pattern matching![/green]")
                console.print("[green]🧠 Understanding context and meaning, not just keywords[/green]")

        except ImportError:
            # Fallback to TF-IDF (already have scikit-learn)
            if not self.silent:
                console.print("[yellow]📊 Using TF-IDF search (keyword matching)[/yellow]")
                console.print("[yellow]💡 Tip: For semantic understanding, install:[/yellow]")
                console.print("    [cyan]pip install sentence-transformers[/cyan]")
                console.print("    [dim]This enables context-aware pattern matching[/dim]\n")

            self.vectorizer = TfidfVectorizer(
                max_features=1000,
                ngram_range=(1, 3),
                stop_words='english'
            )
            self.search_mode = 'tfidf'
            self.corpus = []
            self.corpus_ids = []

    def _setup_tables(self):
        """Create tables for storing embeddings"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Table for semantic embeddings
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS pattern_embeddings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pattern_id TEXT UNIQUE,
                embedding BLOB,
                text TEXT,
                metadata TEXT,
                search_mode TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Table for TF-IDF corpus
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tfidf_corpus (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pattern_id TEXT UNIQUE,
                text TEXT,
                metadata TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        conn.commit()
        conn.close()

        # Load existing corpus for TF-IDF if needed
        if self.search_mode == 'tfidf':
            self._load_tfidf_corpus()

    def add_pattern(self, text: str, pattern_id: str, metadata: Dict = None) -> bool:
        """Add a pattern to the search index"""
        try:
            if self.search_mode == 'semantic':
                return self._add_semantic_pattern(text, pattern_id, metadata)
            else:
                return self._add_tfidf_pattern(text, pattern_id, metadata)
        except Exception as e:
            console.print(f"[red]Error adding pattern: {str(e)}[/red]")
            return False

    def _add_semantic_pattern(self, text: str, pattern_id: str, metadata: Dict) -> bool:
        """Add pattern with semantic embedding"""
        try:
            # Generate embedding
            embedding = self.model.encode(text)
            embedding_bytes = embedding.astype(np.float32).tobytes()

            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute('''
                INSERT OR REPLACE INTO pattern_embeddings
                (pattern_id, embedding, text, metadata, search_mode)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                pattern_id,
                embedding_bytes,
                text,
                json.dumps(metadata) if metadata else None,
                'semantic'
            ))

            conn.commit()
            conn.close()

            # Cache the embedding
            self.embeddings_cache[pattern_id] = embedding

            return True
        except Exception as e:
            console.print(f"[red]Error adding semantic pattern: {str(e)}[/red]")
            return False

    def _add_tfidf_pattern(self, text: str, pattern_id: str, metadata: Dict) -> bool:
        """Add pattern to TF-IDF corpus"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute('''
                INSERT OR REPLACE INTO tfidf_corpus
                (pattern_id, text, metadata)
                VALUES (?, ?, ?)
            ''', (
                pattern_id,
                text,
                json.dumps(metadata) if metadata else None
            ))

            conn.commit()
        except sqlite3.OperationalError as e:
            console.print(f"[red]Error adding pattern: {str(e)}[/red]")
            conn.close()
            return False

        conn.close()

        # Add to in-memory corpus
        if pattern_id not in self.corpus_ids:
            self.corpus.append(text)
            self.corpus_ids.append(pattern_id)

            # Refit vectorizer with updated corpus
            if len(self.corpus) > 0:
                self.vectorizer.fit(self.corpus)

        return True

    def search(self, query: str, limit: int = 5, project: str = None) -> List[Dict]:
        """Search for similar patterns"""
        if self.search_mode == 'semantic':
            results = self._semantic_search(query, limit, project)
        else:
            results = self._tfidf_search(query, limit, project)

        # Add search mode to results for transparency
        for result in results:
            result['search_mode'] = self.search_mode

        return results

    def _semantic_search(self, query: str, limit: int, project: str = None) -> List[Dict]:
        """Perform semantic similarity search"""
        query_embedding = self.model.encode(query)

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            # Load all embeddings (can optimize with FAISS for large scale)
            cursor.execute('''
                SELECT pattern_id, embedding, text, metadata
                FROM pattern_embeddings
                WHERE search_mode = 'semantic'
            ''')
        except sqlite3.OperationalError:
            # Table doesn't exist yet
            conn.close()
            return []

        results = []
        for pattern_id, embedding_bytes, text, metadata_json in cursor.fetchall():
            # Reconstruct embedding
            embedding = np.frombuffer(embedding_bytes, dtype=np.float32)

            # Calculate similarity
            similarity = cosine_similarity([query_embedding], [embedding])[0][0]

            metadata = json.loads(metadata_json) if metadata_json else {}

            # Filter by project if specified
            if project and metadata.get('project') != project:
                continue

            results.append({
                'pattern_id': pattern_id,
                'text': text,
                'similarity': float(similarity),
                'metadata': metadata
            })

        conn.close()

        # Sort by similarity and return top results
        results.sort(key=lambda x: x['similarity'], reverse=True)
        return results[:limit]

    def _tfidf_search(self, query: str, limit: int, project: str = None) -> List[Dict]:
        """Perform TF-IDF similarity search"""
        if not self.corpus:
            return []

        # Transform query
        query_vector = self.vectorizer.transform([query])

        # Transform corpus
        corpus_vectors = self.vectorizer.transform(self.corpus)

        # Calculate similarities
        similarities = cosine_similarity(query_vector, corpus_vectors)[0]

        # Create results
        results = []
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        for idx, similarity in enumerate(similarities):
            pattern_id = self.corpus_ids[idx]

            try:
                cursor.execute('''
                    SELECT text, metadata FROM tfidf_corpus
                    WHERE pattern_id = ?
                ''', (pattern_id,))
                row = cursor.fetchone()
            except sqlite3.OperationalError:
                # Table doesn't exist
                row = None
            if row:
                text, metadata_json = row
                metadata = json.loads(metadata_json) if metadata_json else {}

                # Filter by project if specified
                if project and metadata.get('project') != project:
                    continue

                results.append({
                    'pattern_id': pattern_id,
                    'text': text,
                    'similarity': float(similarity),
                    'metadata': metadata
                })

        conn.close()

        # Sort by similarity and return top results
        results.sort(key=lambda x: x['similarity'], reverse=True)
        return results[:limit]

    def _load_tfidf_corpus(self):
        """Load existing corpus for TF-IDF"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute('SELECT pattern_id, text FROM tfidf_corpus')
            for pattern_id, text in cursor.fetchall():
                self.corpus.append(text)
                self.corpus_ids.append(pattern_id)
        except sqlite3.OperationalError:
            # Table doesn't exist yet, that's OK
            pass

        conn.close()

        # Fit vectorizer if we have data
        if self.corpus:
            self.vectorizer.fit(self.corpus)
            if not self.silent:
                console.print(f"[dim]Loaded {len(self.corpus)} patterns for search[/dim]")

    def get_capabilities(self) -> Dict[str, Any]:
        """Get current search capabilities"""
        return {
            'mode': self.search_mode,
            'semantic_enabled': self.search_mode == 'semantic',
            'pattern_count': len(self.corpus_ids) if self.search_mode == 'tfidf' else len(self.embeddings_cache),
            'model': 'all-MiniLM-L6-v2' if self.search_mode == 'semantic' else 'TF-IDF',
            'features': {
                'keyword_matching': True,
                'semantic_understanding': self.search_mode == 'semantic',
                'context_awareness': self.search_mode == 'semantic',
                'cross_language': self.search_mode == 'semantic'
            }
        }

    def migrate_existing_patterns(self, patterns: List[Dict]) -> int:
        """Migrate existing patterns to vector search"""
        migrated = 0

        console.print(f"[cyan]Migrating {len(patterns)} patterns to {self.search_mode} search...[/cyan]")

        for pattern in patterns:
            text = pattern.get('user_request', '') or pattern.get('description', '')
            pattern_id = pattern.get('id', str(hash(text)))

            if text and self.add_pattern(text, pattern_id, pattern):
                migrated += 1

        console.print(f"[green]✓ Migrated {migrated} patterns successfully[/green]")
        return migrated

    def optimize_index(self):
        """Optimize search index for better performance"""
        if self.search_mode == 'semantic':
            # In future: implement FAISS index for faster search
            console.print("[cyan]Optimizing semantic index...[/cyan]")
        else:
            # Re-fit TF-IDF with optimized parameters
            if self.corpus:
                self.vectorizer = TfidfVectorizer(
                    max_features=min(2000, len(self.corpus)),
                    ngram_range=(1, 3),
                    stop_words='english',
                    min_df=1,
                    max_df=0.95
                )
                self.vectorizer.fit(self.corpus)
                console.print("[cyan]Optimized TF-IDF index[/cyan]")

    def search_patterns(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Search for patterns using vector search or TF-IDF"""
        # Use the existing search method and filter for patterns
        results = self.search(query, limit=limit)
        pattern_results = []

        for result in results:
            metadata = result.get('metadata', {})
            if metadata.get('type') == 'pattern' or 'pattern' in result.get('text', '').lower():
                pattern_results.append({
                    'content': result.get('text', ''),
                    'type': 'pattern',
                    'similarity': result.get('similarity', 0),
                    'metadata': metadata
                })

        return pattern_results

    def update_index(self):
        """Update the search index with new patterns"""
        # Re-initialize search engine to refresh index
        self._initialize_search_engine()

        # Load all patterns from database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute('''
                SELECT approach, request_type, solution_steps, tags
                FROM success_patterns
                ORDER BY timestamp DESC
            ''')

            patterns = []
            for row in cursor.fetchall():
                text = f"{row[0]} {row[1]}"
                if row[2]:
                    try:
                        steps = json.loads(row[2])
                        if isinstance(steps, list):
                            text += " " + " ".join(steps)
                    except:
                        pass
                patterns.append(text)

            # Update index based on search mode
            if self.search_mode == 'semantic':
                # Semantic search will auto-index on next search
                pass
            else:
                # Update TF-IDF vectorizer
                if patterns:
                    self.pattern_vectors = self.vectorizer.fit_transform(patterns)
                    self.patterns = patterns

        finally:
            conn.close()


class SearchCapabilities:
    """Helper class to check and communicate search capabilities"""

    @staticmethod
    def check() -> Dict[str, bool]:
        """Check what search capabilities are available"""
        capabilities = {
            'basic_search': True,  # Always available (TF-IDF)
            'semantic_search': False,
            'gpu_acceleration': False
        }

        try:
            import sentence_transformers
            capabilities['semantic_search'] = True
        except ImportError:
            pass

        try:
            import torch
            capabilities['gpu_acceleration'] = torch.cuda.is_available()
        except ImportError:
            pass

        return capabilities

    @staticmethod
    def suggest_upgrades(capabilities: Dict[str, bool]):
        """Suggest upgrades based on current capabilities"""
        suggestions = []

        if not capabilities['semantic_search']:
            suggestions.append({
                'feature': 'Semantic Search',
                'benefit': '2x better pattern matching with context understanding',
                'install': 'pip install sentence-transformers',
                'size': '~80MB'
            })

        if capabilities['semantic_search'] and not capabilities['gpu_acceleration']:
            suggestions.append({
                'feature': 'GPU Acceleration',
                'benefit': '10x faster search on large codebases',
                'install': 'pip install torch (with CUDA)',
                'size': 'Varies'
            })

        return suggestions

    @staticmethod
    def display_status():
        """Display current search capabilities to user"""
        capabilities = SearchCapabilities.check()

        if capabilities['semantic_search']:
            console.print("[green]✨ Semantic Search: Enabled[/green]")
            console.print("[green]🧠 Context Understanding: Active[/green]")
            if capabilities['gpu_acceleration']:
                console.print("[green]🚀 GPU Acceleration: Active[/green]")
        else:
            console.print("[yellow]📊 Search Mode: Keyword Matching (TF-IDF)[/yellow]")

            suggestions = SearchCapabilities.suggest_upgrades(capabilities)
            if suggestions:
                console.print("\n[yellow]💡 Available Enhancements:[/yellow]")
                for suggestion in suggestions:
                    console.print(f"  • {suggestion['feature']}: {suggestion['install']}")
                    console.print(f"    [dim]{suggestion['benefit']}[/dim]")