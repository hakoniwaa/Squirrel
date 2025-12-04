"""Knowledge base storage and retrieval system"""

import sqlite3
import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from rich.console import Console
from .vector_search import VectorSearchEngine

console = Console()


class KnowledgeBase:
    """Store and retrieve successful patterns and project conventions"""

    def __init__(self, db_path: str = None, silent: bool = False):
        self.silent = silent
        if db_path is None:
            db_dir = Path.home() / '.claude' / 'knowledge'
            db_dir.mkdir(parents=True, exist_ok=True)
            db_path = db_dir / 'cache.db'

        self.db_path = str(db_path)
        self.setup_database()

        # Ensure all tables exist (migration for existing users)
        self.ensure_all_tables_exist()

        # Initialize vector search engine (with automatic fallback)
        self.vector_search = VectorSearchEngine(db_path, silent=self.silent)

        # Keep legacy TF-IDF for backward compatibility
        self.vectorizer = TfidfVectorizer(max_features=1000)
        self.use_vector_search = True  # Flag to enable/disable new search

    def setup_database(self):
        """Create database tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS success_patterns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_name TEXT NOT NULL,
                request_type TEXT,
                user_request TEXT,
                approach TEXT,
                files_involved TEXT,
                solution_steps TEXT,
                key_operations TEXT,
                timestamp DATETIME,
                success_score REAL,
                pattern_quality TEXT DEFAULT 'bronze',
                signal_strength TEXT DEFAULT 'weak',
                tags TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS project_conventions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_name TEXT NOT NULL,
                convention_type TEXT,
                pattern TEXT,
                description TEXT,
                frequency INTEGER DEFAULT 1,
                last_seen DATETIME,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_name TEXT,
                content TEXT,
                request_type TEXT,
                timestamp DATETIME,
                source_file TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tool_usage (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_name TEXT,
                tool TEXT,
                args TEXT,
                success BOOLEAN,
                timestamp DATETIME,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS responses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_name TEXT,
                content TEXT,
                reasoning TEXT,
                timestamp DATETIME,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS documentation (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_name TEXT NOT NULL,
                file_path TEXT NOT NULL,
                doc_type TEXT,
                content TEXT,
                extracted_at DATETIME,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(project_name, file_path)
            )
        ''')

        # New tables for dual-path learning
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS anti_patterns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_name TEXT NOT NULL,
                pattern_type TEXT,
                problem TEXT,
                failed_approach TEXT,
                error_reason TEXT,
                context TEXT,
                alternative_solution TEXT,
                confidence REAL,
                timestamp DATETIME,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS journey_patterns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_name TEXT NOT NULL,
                pattern_id TEXT UNIQUE,
                pattern_type TEXT,
                problem TEXT,
                attempts TEXT,
                final_outcome TEXT,
                key_learning TEXT,
                anti_patterns TEXT,
                success_factors TEXT,
                context TEXT,
                confidence REAL,
                session_id TEXT,
                timestamp DATETIME,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Performance optimizations: Add indexes on frequently queried columns
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_patterns_project
            ON success_patterns(project_name)
        ''')

        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_patterns_timestamp
            ON success_patterns(timestamp)
        ''')

        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_patterns_score
            ON success_patterns(success_score)
        ''')

        # Only create index if column exists (handled by migration)
        cursor.execute("PRAGMA table_info(success_patterns)")
        columns = [col[1] for col in cursor.fetchall()]
        if 'pattern_quality' in columns:
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_patterns_quality
                ON success_patterns(pattern_quality)
            ''')

        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_conventions_project
            ON project_conventions(project_name)
        ''')

        conn.commit()
        conn.close()

        if not self.silent:
            console.print(f"[green]✓ Knowledge base initialized at {self.db_path}[/green]")

    def store_success_pattern(self, pattern: Dict, project_name: str, success_score: float = 1.0):
        """Store a successful pattern"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO success_patterns
            (project_name, request_type, user_request, approach, files_involved,
             solution_steps, key_operations, timestamp, success_score, tags,
             pattern_quality, signal_strength)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            project_name,
            pattern.get('request_type', 'unknown'),
            pattern.get('user_request', ''),
            pattern.get('approach', ''),
            json.dumps(pattern.get('files_involved', [])),
            json.dumps(pattern.get('solution_steps', [])),
            json.dumps(pattern.get('key_operations', [])),
            pattern.get('timestamp', datetime.now().isoformat()),
            success_score,
            json.dumps(pattern.get('tags', [])),
            pattern.get('pattern_quality', 'bronze'),
            pattern.get('signal_strength', 'medium')
        ))

        pattern_id = cursor.lastrowid
        conn.commit()
        conn.close()

        # Add to vector search index if available
        if self.use_vector_search and self.vector_search:
            try:
                # Create searchable text from pattern
                search_text = pattern.get('user_request', '')
                if pattern.get('approach'):
                    search_text += f" {pattern['approach']}"

                # Store metadata for later retrieval
                metadata = {
                    'type': 'pattern',  # Important for unified search
                    'project': project_name,
                    'success_score': success_score,
                    'request_type': pattern.get('request_type', 'unknown'),
                    'timestamp': pattern.get('timestamp', datetime.now().isoformat())
                }

                # Add to vector index
                self.vector_search.add_pattern(
                    text=search_text,
                    pattern_id=f"pattern_{pattern_id}",
                    metadata=metadata
                )

                console.print(f"[green]✓ Stored and indexed pattern for {project_name}[/green]")
            except Exception as e:
                console.print(f"[yellow]Pattern stored but indexing failed: {str(e)}[/yellow]")
        else:
            console.print(f"[green]✓ Stored success pattern for {project_name}[/green]")

    def store_request(self, request_data: Dict):
        """Store a user request"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO user_requests
            (project_name, content, request_type, timestamp, source_file)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            request_data.get('project', 'unknown'),
            request_data.get('content', ''),
            request_data.get('type', 'other'),
            request_data.get('timestamp', datetime.now().isoformat()),
            request_data.get('source', '')
        ))

        conn.commit()
        conn.close()

    def store_tool_usage(self, tool_data: Dict):
        """Store tool usage data"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO tool_usage
            (project_name, tool, args, success, timestamp)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            tool_data.get('project', 'unknown'),
            tool_data.get('tool', ''),
            json.dumps(tool_data.get('args', {})),
            tool_data.get('success', True),
            tool_data.get('timestamp', datetime.now().isoformat())
        ))

        conn.commit()
        conn.close()

    def store_response(self, response_data: Dict):
        """Store assistant response"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO responses
            (project_name, content, reasoning, timestamp)
            VALUES (?, ?, ?, ?)
        ''', (
            response_data.get('project', 'unknown'),
            response_data.get('content', ''),
            response_data.get('reasoning', ''),
            response_data.get('timestamp', datetime.now().isoformat())
        ))

        conn.commit()
        conn.close()

    def find_similar_patterns(self, current_request: str, project_name: str, threshold: float = 0.3) -> List[Dict]:
        """Find similar successful patterns using hybrid vector search"""
        # Try vector search first if available
        if self.use_vector_search and self.vector_search:
            try:
                # Use the vector search engine for better results
                vector_results = self.vector_search.search(
                    query=current_request,
                    limit=10,
                    project=project_name
                )

                # Convert vector search results to expected format
                similar_patterns = []
                for result in vector_results:
                    if result['similarity'] > threshold:
                        # Fetch full pattern data from database
                        conn = sqlite3.connect(self.db_path)
                        cursor = conn.cursor()

                        pattern_id = result.get('pattern_id', '')
                        # Try to extract numeric ID from pattern_id
                        try:
                            numeric_id = int(pattern_id.split('_')[-1]) if '_' in pattern_id else int(pattern_id)
                        except:
                            numeric_id = pattern_id

                        cursor.execute('''
                            SELECT id, user_request, approach, solution_steps, success_score,
                                   files_involved, key_operations, pattern_quality, signal_strength
                            FROM success_patterns
                            WHERE id = ? OR user_request = ?
                        ''', (numeric_id, result.get('text', '')))

                        pattern_data = cursor.fetchone()
                        conn.close()

                        if pattern_data:
                            similar_patterns.append({
                                'id': pattern_data[0],
                                'request': pattern_data[1],
                                'approach': pattern_data[2],
                                'solution_steps': json.loads(pattern_data[3]) if pattern_data[3] else [],
                                'files_involved': json.loads(pattern_data[5]) if pattern_data[5] else [],
                                'key_operations': json.loads(pattern_data[6]) if pattern_data[6] else [],
                                'success_score': pattern_data[4],
                                'pattern_quality': pattern_data[7] if len(pattern_data) > 7 else 'bronze',
                                'signal_strength': pattern_data[8] if len(pattern_data) > 8 else 'medium',
                                'similarity': result['similarity'],
                                'search_mode': result.get('search_mode', 'unknown')
                            })

                if similar_patterns:
                    return sorted(similar_patterns, key=lambda x: x['similarity'], reverse=True)[:5]
            except Exception as e:
                console.print(f"[yellow]Vector search failed, falling back to TF-IDF: {str(e)}[/yellow]")

        # Fallback to legacy TF-IDF search
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT id, user_request, approach, solution_steps, success_score, files_involved, key_operations,
                   pattern_quality, signal_strength
            FROM success_patterns
            WHERE project_name = ?
            ORDER BY success_score DESC
            LIMIT 100
        ''', (project_name,))

        patterns = cursor.fetchall()
        conn.close()

        if not patterns:
            return []

        requests = [current_request] + [p[1] for p in patterns]

        try:
            tfidf_matrix = self.vectorizer.fit_transform(requests)
            similarities = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:]).flatten()
        except:
            similarities = [0] * len(patterns)

        similar_patterns = []
        for i, pattern in enumerate(patterns):
            if similarities[i] > threshold:
                pattern_id, request, approach, steps, score, files, operations = pattern[:7]
                pattern_quality = pattern[7] if len(pattern) > 7 else 'bronze'
                signal_strength = pattern[8] if len(pattern) > 8 else 'medium'

                similar_patterns.append({
                    'id': pattern_id,
                    'request': request,
                    'approach': approach,
                    'solution_steps': json.loads(steps) if steps else [],
                    'files_involved': json.loads(files) if files else [],
                    'key_operations': json.loads(operations) if operations else [],
                    'success_score': score,
                    'pattern_quality': pattern_quality,
                    'signal_strength': signal_strength,
                    'similarity': similarities[i],
                    'search_mode': 'tfidf'
                })

        return sorted(similar_patterns, key=lambda x: x['similarity'], reverse=True)[:5]

    def get_project_conventions(self, project_name: str) -> List[Dict]:
        """Get conventions for a project"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT convention_type, pattern, description, frequency
            FROM project_conventions
            WHERE project_name = ?
            ORDER BY frequency DESC
        ''', (project_name,))

        conventions = []
        for row in cursor.fetchall():
            conventions.append({
                'type': row[0],
                'pattern': row[1],
                'description': row[2],
                'frequency': row[3]
            })

        conn.close()
        return conventions

    def store_convention(self, project_name: str, convention_type: str, pattern: str, description: str = ''):
        """Store or update a project convention"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT id, frequency FROM project_conventions
            WHERE project_name = ? AND convention_type = ? AND pattern = ?
        ''', (project_name, convention_type, pattern))

        existing = cursor.fetchone()

        if existing:
            cursor.execute('''
                UPDATE project_conventions
                SET frequency = frequency + 1, last_seen = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (existing[0],))
        else:
            cursor.execute('''
                INSERT INTO project_conventions
                (project_name, convention_type, pattern, description, last_seen)
                VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
            ''', (project_name, convention_type, pattern, description))

        conn.commit()
        conn.close()

    def get_statistics(self, project_name: Optional[str] = None) -> Dict:
        """Get statistics about the knowledge base"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        stats = {}

        if project_name:
            # Single project stats
            cursor.execute('SELECT COUNT(*) FROM success_patterns WHERE project_name = ?', (project_name,))
            stats['patterns'] = cursor.fetchone()[0]

            cursor.execute('SELECT COUNT(*) FROM project_conventions WHERE project_name = ?', (project_name,))
            stats['conventions'] = cursor.fetchone()[0]

            cursor.execute('SELECT COUNT(*) FROM user_requests WHERE project_name = ?', (project_name,))
            stats['requests'] = cursor.fetchone()[0]

            # Pattern type breakdown for the project
            cursor.execute('''
                SELECT
                    SUM(CASE WHEN success_score >= 0.9 THEN 1 ELSE 0 END) as gold,
                    SUM(CASE WHEN success_score >= 0.7 AND success_score < 0.9 THEN 1 ELSE 0 END) as silver,
                    SUM(CASE WHEN success_score < 0.7 THEN 1 ELSE 0 END) as bronze
                FROM success_patterns
                WHERE project_name = ?
            ''', (project_name,))
            type_counts = cursor.fetchone()
            stats['pattern_types'] = {
                'gold': type_counts[0] or 0,
                'silver': type_counts[1] or 0,
                'bronze': type_counts[2] or 0
            }

            # Anti-patterns and journey patterns
            cursor.execute('SELECT COUNT(*) FROM anti_patterns WHERE project_name = ?', (project_name,))
            stats['anti_patterns'] = cursor.fetchone()[0]

            cursor.execute('SELECT COUNT(*) FROM journey_patterns WHERE project_name = ?', (project_name,))
            stats['journey_patterns'] = cursor.fetchone()[0]
        else:
            # Overall stats with per-project breakdown
            cursor.execute('SELECT COUNT(*) FROM success_patterns')
            stats['total_patterns'] = cursor.fetchone()[0]

            cursor.execute('SELECT COUNT(DISTINCT project_name) FROM success_patterns')
            stats['total_projects'] = cursor.fetchone()[0]

            cursor.execute('SELECT COUNT(*) FROM user_requests')
            stats['total_requests'] = cursor.fetchone()[0]

            # Get per-project breakdown
            cursor.execute('''
                SELECT
                    project_name,
                    COUNT(*) as pattern_count,
                    AVG(success_score) as avg_success_score,
                    MAX(created_at) as last_activity
                FROM success_patterns
                GROUP BY project_name
                ORDER BY pattern_count DESC
            ''')

            projects_breakdown = []
            for row in cursor.fetchall():
                project_stats = {
                    'name': row[0],
                    'patterns': row[1],
                    'avg_success_score': round(row[2], 2) if row[2] else 0,
                    'last_activity': row[3]
                }

                # Get pattern type counts for this project
                cursor.execute('''
                    SELECT
                        SUM(CASE WHEN success_score >= 0.9 THEN 1 ELSE 0 END) as gold,
                        SUM(CASE WHEN success_score >= 0.7 AND success_score < 0.9 THEN 1 ELSE 0 END) as silver,
                        SUM(CASE WHEN success_score < 0.7 THEN 1 ELSE 0 END) as bronze
                    FROM success_patterns
                    WHERE project_name = ?
                ''', (row[0],))
                type_counts = cursor.fetchone()

                project_stats['gold'] = type_counts[0] or 0
                project_stats['silver'] = type_counts[1] or 0
                project_stats['bronze'] = type_counts[2] or 0

                # Get anti-patterns count
                cursor.execute('SELECT COUNT(*) FROM anti_patterns WHERE project_name = ?', (row[0],))
                project_stats['anti_patterns'] = cursor.fetchone()[0]

                # Get journey patterns count
                cursor.execute('SELECT COUNT(*) FROM journey_patterns WHERE project_name = ?', (row[0],))
                project_stats['journey_patterns'] = cursor.fetchone()[0]

                projects_breakdown.append(project_stats)

            stats['projects'] = projects_breakdown

            # Global pattern type totals
            cursor.execute('''
                SELECT
                    SUM(CASE WHEN success_score >= 0.9 THEN 1 ELSE 0 END) as gold,
                    SUM(CASE WHEN success_score >= 0.7 AND success_score < 0.9 THEN 1 ELSE 0 END) as silver,
                    SUM(CASE WHEN success_score < 0.7 THEN 1 ELSE 0 END) as bronze
                FROM success_patterns
            ''')
            type_totals = cursor.fetchone()
            stats['pattern_types_total'] = {
                'gold': type_totals[0] or 0,
                'silver': type_totals[1] or 0,
                'bronze': type_totals[2] or 0
            }

            # Total anti-patterns and journey patterns
            cursor.execute('SELECT COUNT(*) FROM anti_patterns')
            stats['total_anti_patterns'] = cursor.fetchone()[0]

            cursor.execute('SELECT COUNT(*) FROM journey_patterns')
            stats['total_journey_patterns'] = cursor.fetchone()[0]

        conn.close()
        return stats

    def export_patterns(self, project_name: Optional[str] = None) -> Dict:
        """Export patterns for sharing or backup"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        if project_name:
            cursor.execute('''
                SELECT * FROM success_patterns
                WHERE project_name = ?
            ''', (project_name,))
        else:
            cursor.execute('SELECT * FROM success_patterns')

        columns = [description[0] for description in cursor.description]
        patterns = []

        for row in cursor.fetchall():
            pattern_dict = dict(zip(columns, row))

            for field in ['files_involved', 'solution_steps', 'key_operations', 'tags']:
                if field in pattern_dict and pattern_dict[field]:
                    try:
                        pattern_dict[field] = json.loads(pattern_dict[field])
                    except:
                        pass

            patterns.append(pattern_dict)

        conn.close()

        return {
            'version': '1.0',
            'exported_at': datetime.now().isoformat(),
            'project': project_name or 'all',
            'patterns': patterns
        }

    def import_patterns(self, data: Dict):
        """Import patterns from export"""
        patterns = data.get('patterns', [])

        for pattern in patterns:
            for field in ['files_involved', 'solution_steps', 'key_operations', 'tags']:
                if field in pattern and isinstance(pattern[field], list):
                    pattern[field] = json.dumps(pattern[field])

            self.store_success_pattern(pattern, pattern.get('project_name', 'imported'))

        console.print(f"[green]✓ Imported {len(patterns)} patterns[/green]")

    def store_documentation(self, project_name: str, file_path: str, doc_type: str,
                           content: str, extracted_at: str):
        """Store extracted documentation in the knowledge base"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute('''
                INSERT OR REPLACE INTO documentation
                (project_name, file_path, doc_type, content, extracted_at)
                VALUES (?, ?, ?, ?, ?)
            ''', (project_name, file_path, doc_type, content, extracted_at))

            conn.commit()
        finally:
            conn.close()

        # Automatically index documentation into vector search if available
        if self.use_vector_search and self.vector_search:
            try:
                import json
                doc_data = json.loads(content)

                # Create searchable text from lessons, warnings, etc.
                search_text_parts = []

                if 'lessons' in doc_data:
                    search_text_parts.extend(doc_data['lessons'])

                if 'warnings' in doc_data:
                    search_text_parts.extend(doc_data['warnings'])

                if 'best_practices' in doc_data:
                    search_text_parts.extend(doc_data['best_practices'])

                if 'architecture' in doc_data:
                    search_text_parts.append(doc_data['architecture'])

                # Combine all text
                search_text = " ".join(search_text_parts)

                if search_text.strip():
                    # Add to vector search index
                    pattern_id = f"doc_{project_name}_{file_path}".replace("/", "_").replace(" ", "_")[:100]

                    self.vector_search.add_pattern(
                        text=search_text,
                        pattern_id=pattern_id,
                        metadata={
                            'type': 'documentation',
                            'project': project_name,
                            'file_path': file_path,
                            'doc_type': doc_type
                        }
                    )
            except Exception as e:
                # Don't fail if indexing fails, just log it
                console.print(f"[dim]Could not index documentation: {str(e)}[/dim]")

    def search_documentation(self, query: str, project_name: Optional[str] = None,
                           limit: int = 10) -> List[Dict[str, Any]]:
        """Search through stored documentation"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            if project_name:
                cursor.execute('''
                    SELECT project_name, file_path, doc_type, content, extracted_at
                    FROM documentation
                    WHERE project_name = ?
                    ORDER BY extracted_at DESC
                    LIMIT ?
                ''', (project_name, limit))
            else:
                cursor.execute('''
                    SELECT project_name, file_path, doc_type, content, extracted_at
                    FROM documentation
                    ORDER BY extracted_at DESC
                    LIMIT ?
                ''', (limit,))

            results = []
            for row in cursor.fetchall():
                results.append({
                    'project_name': row[0],
                    'file_path': row[1],
                    'doc_type': row[2],
                    'content': row[3],
                    'extracted_at': row[4]
                })

            # Filter by query relevance if provided
            if query and results:
                import json
                scored_results = []
                for result in results:
                    doc_data = json.loads(result['content'])
                    # Simple relevance scoring based on query terms
                    score = 0
                    query_terms = query.lower().split()
                    content_str = json.dumps(doc_data).lower()

                    for term in query_terms:
                        score += content_str.count(term)

                    if score > 0:
                        result['relevance_score'] = score
                        scored_results.append(result)

                # Sort by relevance
                scored_results.sort(key=lambda x: x['relevance_score'], reverse=True)
                return scored_results[:limit]

            return results

        finally:
            conn.close()

    def unified_search(self, query: str, project_name: Optional[str] = None,
                       limit: int = 10) -> List[Dict[str, Any]]:
        """Unified search across all content: patterns, documentation, everything"""
        if self.use_vector_search and self.vector_search:
            # Use vector search for everything
            results = self.vector_search.search(
                query=query,
                limit=limit,
                project=project_name
            )

            # Enrich results with additional metadata
            enriched_results = []
            for result in results:
                metadata = result.get('metadata', {})
                content_type = metadata.get('type', 'unknown')

                enriched_result = {
                    'type': content_type,
                    'content': result.get('text', ''),
                    'similarity': result.get('similarity', 0),
                    'project': metadata.get('project', ''),
                    'search_mode': result.get('search_mode', 'unknown')
                }

                # Add type-specific fields
                if content_type == 'documentation':
                    enriched_result['file_path'] = metadata.get('file_path', '')
                    enriched_result['doc_type'] = metadata.get('doc_type', '')
                elif content_type == 'pattern':
                    enriched_result['pattern_id'] = result.get('pattern_id', '')

                enriched_results.append(enriched_result)

            return enriched_results
        else:
            # Fallback to pattern search only (legacy)
            patterns = self.find_similar_patterns(query, project_name or 'unknown', 0.1)
            return [{
                'type': 'pattern',
                'content': p.get('request', ''),
                'similarity': p.get('similarity', 0),
                'project': project_name or '',
                'search_mode': 'tfidf'
            } for p in patterns[:limit]]

    def get_documentation_for_context(self, project_name: str) -> List[Dict[str, Any]]:
        """Get relevant documentation for context injection"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute('''
                SELECT file_path, doc_type, content
                FROM documentation
                WHERE project_name = ?
                AND doc_type IN ('lessons', 'postmortem', 'architecture', 'guide')
                ORDER BY
                    CASE doc_type
                        WHEN 'lessons' THEN 1
                        WHEN 'postmortem' THEN 2
                        WHEN 'architecture' THEN 3
                        WHEN 'guide' THEN 4
                        ELSE 5
                    END
                LIMIT 10
            ''', (project_name,))

            docs = []
            for row in cursor.fetchall():
                docs.append({
                    'file_path': row[0],
                    'doc_type': row[1],
                    'content': row[2]
                })

            return docs

        finally:
            conn.close()

    def get_project_patterns(self, project_name: Optional[str] = None, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent patterns for a project"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            if project_name:
                cursor.execute('''
                    SELECT project_name, request_type, user_request, approach,
                           files_involved, solution_steps, timestamp
                    FROM success_patterns
                    WHERE project_name = ?
                    ORDER BY timestamp DESC
                    LIMIT ?
                ''', (project_name, limit))
            else:
                cursor.execute('''
                    SELECT project_name, request_type, user_request, approach,
                           files_involved, solution_steps, timestamp
                    FROM success_patterns
                    ORDER BY timestamp DESC
                    LIMIT ?
                ''', (limit,))

            patterns = []
            for row in cursor.fetchall():
                pattern = {
                    'project_name': row[0],
                    'request_type': row[1],
                    'user_request': row[2],
                    'approach': row[3],
                    'files_involved': json.loads(row[4]) if row[4] else [],
                    'solution_steps': json.loads(row[5]) if row[5] else [],
                    'timestamp': row[6],
                    'pattern_quality': row[7] if len(row) > 7 else 'bronze',
                    'signal_strength': row[8] if len(row) > 8 else 'medium'
                }
                patterns.append(pattern)

            return patterns

        finally:
            conn.close()

    def store_anti_pattern(self, pattern_data: Dict):
        """Store an anti-pattern (what doesn't work)"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute('''
                INSERT INTO anti_patterns
                (project_name, pattern_type, problem, failed_approach, error_reason,
                 context, alternative_solution, confidence, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                pattern_data.get('project', 'unknown'),
                pattern_data.get('type', 'anti'),
                pattern_data.get('problem', ''),
                pattern_data.get('failed_approach', ''),
                pattern_data.get('error_reason', ''),
                json.dumps(pattern_data.get('context', {})),
                pattern_data.get('alternative_solution', ''),
                pattern_data.get('confidence', 0.5),
                pattern_data.get('timestamp', datetime.now().isoformat())
            ))
            conn.commit()
        finally:
            conn.close()

    def store_journey_pattern(self, pattern_data: Dict):
        """Store a journey pattern (complete problem-solving path)"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute('''
                INSERT OR REPLACE INTO journey_patterns
                (project_name, pattern_id, pattern_type, problem, attempts,
                 final_outcome, key_learning, anti_patterns, success_factors,
                 context, confidence, session_id, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                pattern_data.get('project', 'unknown'),
                pattern_data.get('pattern_id', ''),
                pattern_data.get('type', 'journey'),
                pattern_data.get('problem', ''),
                pattern_data.get('attempts', ''),
                pattern_data.get('final_outcome', ''),
                pattern_data.get('key_learning', ''),
                pattern_data.get('anti_patterns', ''),
                pattern_data.get('success_factors', ''),
                pattern_data.get('context', ''),
                pattern_data.get('confidence', 0.5),
                pattern_data.get('session_id', ''),
                pattern_data.get('timestamp', datetime.now().isoformat())
            ))
            conn.commit()
        finally:
            conn.close()

    def get_anti_patterns(self, project_name: Optional[str] = None, problem: Optional[str] = None) -> List[Dict]:
        """Retrieve anti-patterns (what to avoid)"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            if project_name and problem:
                cursor.execute('''
                    SELECT * FROM anti_patterns
                    WHERE project_name = ? AND problem LIKE ?
                    ORDER BY confidence DESC
                    LIMIT 10
                ''', (project_name, f'%{problem}%'))
            elif project_name:
                cursor.execute('''
                    SELECT * FROM anti_patterns
                    WHERE project_name = ?
                    ORDER BY confidence DESC
                    LIMIT 10
                ''', (project_name,))
            else:
                cursor.execute('''
                    SELECT * FROM anti_patterns
                    ORDER BY confidence DESC
                    LIMIT 10
                ''')

            anti_patterns = []
            for row in cursor.fetchall():
                anti_patterns.append({
                    'id': row[0],
                    'project': row[1],
                    'type': row[2],
                    'problem': row[3],
                    'failed_approach': row[4],
                    'error_reason': row[5],
                    'context': json.loads(row[6]) if row[6] else {},
                    'alternative': row[7],
                    'confidence': row[8]
                })

            return anti_patterns

        finally:
            conn.close()

    def get_journey_patterns(self, project_name: Optional[str] = None, problem: Optional[str] = None) -> List[Dict]:
        """Retrieve journey patterns (complete problem-solving paths)"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            if project_name and problem:
                cursor.execute('''
                    SELECT * FROM journey_patterns
                    WHERE project_name = ? AND problem LIKE ?
                    ORDER BY confidence DESC
                    LIMIT 10
                ''', (project_name, f'%{problem}%'))
            elif project_name:
                cursor.execute('''
                    SELECT * FROM journey_patterns
                    WHERE project_name = ?
                    ORDER BY confidence DESC
                    LIMIT 10
                ''', (project_name,))
            else:
                cursor.execute('''
                    SELECT * FROM journey_patterns
                    ORDER BY confidence DESC
                    LIMIT 10
                ''')

            journey_patterns = []
            for row in cursor.fetchall():
                journey_patterns.append({
                    'id': row[0],
                    'project': row[1],
                    'pattern_id': row[2],
                    'type': row[3],
                    'problem': row[4],
                    'attempts': json.loads(row[5]) if row[5] else [],
                    'final_outcome': row[6],
                    'key_learning': row[7],
                    'anti_patterns': json.loads(row[8]) if row[8] else [],
                    'success_factors': json.loads(row[9]) if row[9] else [],
                    'context': json.loads(row[10]) if row[10] else {},
                    'confidence': row[11]
                })

            return journey_patterns

        finally:
            conn.close()

    def ensure_all_tables_exist(self):
        """Ensure all required tables exist - for migration and new installs"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Check which tables exist
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        existing_tables = [row[0] for row in cursor.fetchall()]

        # Add new columns to success_patterns if they don't exist
        if 'success_patterns' in existing_tables:
            # Check if pattern_quality column exists
            cursor.execute("PRAGMA table_info(success_patterns)")
            columns = [col[1] for col in cursor.fetchall()]

            if 'pattern_quality' not in columns:
                cursor.execute("ALTER TABLE success_patterns ADD COLUMN pattern_quality TEXT DEFAULT 'bronze'")
                if not self.silent:
                    console.print("[green]✓ Added pattern_quality column[/green]")

            if 'signal_strength' not in columns:
                cursor.execute("ALTER TABLE success_patterns ADD COLUMN signal_strength TEXT DEFAULT 'weak'")
                if not self.silent:
                    console.print("[green]✓ Added signal_strength column[/green]")

        # Create anti_patterns table if it doesn't exist
        if 'anti_patterns' not in existing_tables:
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS anti_patterns (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    project_name TEXT NOT NULL,
                    pattern_type TEXT,
                    problem TEXT,
                    failed_approach TEXT,
                    error_reason TEXT,
                    context TEXT,
                    alternative_solution TEXT,
                    confidence REAL,
                    timestamp DATETIME,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            if not self.silent:
                console.print("[green]✓ Created anti_patterns table[/green]")

        # Create journey_patterns table if it doesn't exist
        if 'journey_patterns' not in existing_tables:
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS journey_patterns (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    project_name TEXT NOT NULL,
                    pattern_id TEXT UNIQUE,
                    pattern_type TEXT,
                    problem TEXT,
                    attempts TEXT,
                    final_outcome TEXT,
                    key_learning TEXT,
                    anti_patterns TEXT,
                    success_factors TEXT,
                    context TEXT,
                    confidence REAL,
                    session_id TEXT,
                    timestamp DATETIME,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            if not self.silent:
                console.print("[green]✓ Created journey_patterns table[/green]")

        conn.commit()
        conn.close()

    def migrate_fragmented_projects(self):
        """Migrate patterns from fragmented project names to consolidated ones"""
        # Import here to avoid circular import
        from .log_processor import LogEntry

        conn = sqlite3.connect(self.db_path)
        try:
            cursor = conn.cursor()

            # Create a dummy LogEntry to use the consolidation logic
            dummy_entry = LogEntry({'cwd': ''}, '')

            # Get all unique project names
            cursor.execute('SELECT DISTINCT project_name FROM success_patterns')
            projects = [row[0] for row in cursor.fetchall()]

            # Track migrations
            migrations = {}

            for project in projects:
                consolidated = dummy_entry._consolidate_project_name(project)
                if consolidated != project:
                    if consolidated not in migrations:
                        migrations[consolidated] = []
                    migrations[consolidated].append(project)

            # Perform migrations
            for target_project, source_projects in migrations.items():
                if not self.silent:
                    print(f"Consolidating {', '.join(source_projects)} → {target_project}")

                # Update success_patterns
                for source in source_projects:
                    cursor.execute('''
                        UPDATE success_patterns
                        SET project_name = ?
                        WHERE project_name = ?
                    ''', (target_project, source))

                # Update anti_patterns
                for source in source_projects:
                    cursor.execute('''
                        UPDATE anti_patterns
                        SET project_name = ?
                        WHERE project_name = ?
                    ''', (target_project, source))

                # Update journey_patterns
                for source in source_projects:
                    cursor.execute('''
                        UPDATE journey_patterns
                        SET project_name = ?
                        WHERE project_name = ?
                    ''', (target_project, source))

            conn.commit()

            if migrations and not self.silent:
                print(f"Successfully consolidated {len(sum(migrations.values(), []))} fragmented projects into {len(migrations)} consolidated projects")

        finally:
            conn.close()