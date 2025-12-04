"""Track and prioritize patterns based on their efficiency and effectiveness"""

import json
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
import statistics


@dataclass
class EfficiencyMetrics:
    """Metrics for pattern efficiency"""
    pattern_id: str
    time_to_solution: timedelta  # How long it took to solve
    lines_changed: int  # How many lines were modified
    files_touched: int  # Number of files modified
    commands_executed: int  # Number of commands run
    iterations_needed: int  # How many attempts before success
    user_interactions: int  # How many times user provided feedback
    error_rate: float  # Percentage of errors during execution
    recency_score: float  # How recent this pattern is (0-1)
    frequency_score: float  # How often it's used (0-1)
    success_rate: float  # Overall success rate (0-1)


@dataclass
class RankedPattern:
    """A pattern with its efficiency ranking"""
    pattern: Dict
    metrics: EfficiencyMetrics
    efficiency_score: float  # Composite score (0-100)
    rank: int
    reason: str  # Why this pattern ranks high/low


class DifferentialLearner:
    """Learn which patterns are most efficient and prioritize them"""

    def __init__(self, knowledge_base):
        self.kb = knowledge_base
        self._setup_metrics_tables()

        # Weights for calculating efficiency scores
        self.efficiency_weights = {
            'time_weight': 0.3,  # Faster is better
            'simplicity_weight': 0.2,  # Fewer changes is better
            'reliability_weight': 0.25,  # Higher success rate is better
            'recency_weight': 0.15,  # Recent patterns preferred
            'frequency_weight': 0.1  # Frequently used patterns preferred
        }

        # Thresholds for classification
        self.thresholds = {
            'fast_solution': timedelta(minutes=5),
            'moderate_solution': timedelta(minutes=15),
            'complex_solution': timedelta(minutes=30),
            'simple_change': 10,  # lines
            'moderate_change': 50,  # lines
            'major_change': 100  # lines
        }

    def _setup_metrics_tables(self):
        """Create database tables for efficiency metrics"""
        import sqlite3
        conn = sqlite3.connect(self.kb.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS pattern_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pattern_id TEXT UNIQUE,
                time_to_solution INTEGER,  -- seconds
                lines_changed INTEGER,
                files_touched INTEGER,
                commands_executed INTEGER,
                iterations_needed INTEGER,
                user_interactions INTEGER,
                error_rate REAL,
                success_count INTEGER DEFAULT 0,
                failure_count INTEGER DEFAULT 0,
                last_used DATETIME,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS session_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT,
                project_name TEXT,
                start_time DATETIME,
                end_time DATETIME,
                total_duration INTEGER,  -- seconds
                pattern_used TEXT,
                was_successful BOOLEAN,
                user_satisfaction_score REAL,
                complexity_score REAL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS pattern_comparisons (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pattern_a TEXT,
                pattern_b TEXT,
                task_type TEXT,
                winner TEXT,  -- Which pattern was more efficient
                comparison_metric TEXT,  -- What was compared
                difference_value REAL,  -- How much better
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        conn.commit()
        conn.close()

    def track_session_metrics(self, session_data: Dict) -> EfficiencyMetrics:
        """Track metrics for a coding session"""
        start_time = datetime.fromisoformat(session_data.get('start_time'))
        end_time = datetime.fromisoformat(session_data.get('end_time'))
        duration = end_time - start_time

        # Count various metrics
        lines_changed = self._count_lines_changed(session_data.get('entries', []))
        files_touched = self._count_files_touched(session_data.get('entries', []))
        commands_executed = self._count_commands(session_data.get('entries', []))
        iterations = self._count_iterations(session_data.get('entries', []))
        user_interactions = self._count_user_interactions(session_data.get('entries', []))
        error_rate = self._calculate_error_rate(session_data.get('entries', []))

        metrics = EfficiencyMetrics(
            pattern_id=session_data.get('pattern_id', 'unknown'),
            time_to_solution=duration,
            lines_changed=lines_changed,
            files_touched=files_touched,
            commands_executed=commands_executed,
            iterations_needed=iterations,
            user_interactions=user_interactions,
            error_rate=error_rate,
            recency_score=1.0,  # New patterns start with high recency
            frequency_score=0.0,  # Will be updated based on usage
            success_rate=1.0 if session_data.get('successful') else 0.0
        )

        self._store_metrics(metrics)
        return metrics

    def _count_lines_changed(self, entries: List[Dict]) -> int:
        """Count total lines changed in a session"""
        lines = 0
        for entry in entries:
            if entry.get('type') == 'tool_call':
                tool = entry.get('tool')
                if tool in ['Edit', 'Write', 'MultiEdit']:
                    # Estimate lines based on content
                    content = str(entry.get('args', {}).get('new_string', ''))
                    lines += len(content.split('\n'))
        return lines

    def _count_files_touched(self, entries: List[Dict]) -> int:
        """Count unique files modified"""
        files = set()
        for entry in entries:
            if entry.get('type') == 'tool_call':
                args = entry.get('args', {})
                if 'file_path' in args:
                    files.add(args['file_path'])
        return len(files)

    def _count_commands(self, entries: List[Dict]) -> int:
        """Count bash commands executed"""
        count = 0
        for entry in entries:
            if entry.get('type') == 'tool_call' and entry.get('tool') == 'Bash':
                count += 1
        return count

    def _count_iterations(self, entries: List[Dict]) -> int:
        """Count how many attempts were needed (error-fix cycles)"""
        iterations = 1
        for i, entry in enumerate(entries):
            if i > 0:
                # Check for error followed by fix attempt
                if 'error' in str(entry.get('content', '')).lower():
                    # Look for subsequent fix attempt
                    if i + 1 < len(entries):
                        next_entry = entries[i + 1]
                        if next_entry.get('type') == 'tool_call':
                            iterations += 1
        return iterations

    def _count_user_interactions(self, entries: List[Dict]) -> int:
        """Count user messages during session"""
        return sum(1 for e in entries if e.get('type') == 'user_message')

    def _calculate_error_rate(self, entries: List[Dict]) -> float:
        """Calculate percentage of actions that resulted in errors"""
        total_actions = 0
        error_actions = 0

        for entry in entries:
            if entry.get('type') == 'tool_call':
                total_actions += 1
                if not entry.get('success', True):
                    error_actions += 1

        return error_actions / total_actions if total_actions > 0 else 0.0

    def rank_patterns(self, patterns: List[Dict], context: Optional[Dict] = None) -> List[RankedPattern]:
        """Rank patterns by their efficiency scores"""
        ranked = []

        for pattern in patterns:
            metrics = self._get_pattern_metrics(pattern.get('id'))
            if metrics:
                score = self._calculate_efficiency_score(metrics, context)
                ranked.append(RankedPattern(
                    pattern=pattern,
                    metrics=metrics,
                    efficiency_score=score,
                    rank=0,  # Will be set after sorting
                    reason=self._explain_ranking(metrics, score)
                ))

        # Sort by efficiency score (highest first)
        ranked.sort(key=lambda x: x.efficiency_score, reverse=True)

        # Assign ranks
        for i, item in enumerate(ranked):
            item.rank = i + 1

        return ranked

    def _calculate_efficiency_score(self, metrics: EfficiencyMetrics, context: Optional[Dict] = None) -> float:
        """Calculate composite efficiency score (0-100)"""
        scores = {}

        # Time score (faster is better)
        if metrics.time_to_solution < self.thresholds['fast_solution']:
            scores['time'] = 100
        elif metrics.time_to_solution < self.thresholds['moderate_solution']:
            scores['time'] = 70
        elif metrics.time_to_solution < self.thresholds['complex_solution']:
            scores['time'] = 40
        else:
            scores['time'] = 20

        # Simplicity score (fewer changes is better)
        if metrics.lines_changed < self.thresholds['simple_change']:
            scores['simplicity'] = 100
        elif metrics.lines_changed < self.thresholds['moderate_change']:
            scores['simplicity'] = 70
        elif metrics.lines_changed < self.thresholds['major_change']:
            scores['simplicity'] = 40
        else:
            scores['simplicity'] = 20

        # Reliability score (based on success rate and error rate)
        scores['reliability'] = (metrics.success_rate * 100) * (1 - metrics.error_rate)

        # Recency score
        scores['recency'] = metrics.recency_score * 100

        # Frequency score
        scores['frequency'] = metrics.frequency_score * 100

        # Apply weights
        weighted_score = (
            scores['time'] * self.efficiency_weights['time_weight'] +
            scores['simplicity'] * self.efficiency_weights['simplicity_weight'] +
            scores['reliability'] * self.efficiency_weights['reliability_weight'] +
            scores['recency'] * self.efficiency_weights['recency_weight'] +
            scores['frequency'] * self.efficiency_weights['frequency_weight']
        )

        # Apply context modifiers if provided
        if context:
            if context.get('prefer_fast'):
                weighted_score *= 1.2 if scores['time'] > 70 else 0.8
            if context.get('prefer_simple'):
                weighted_score *= 1.2 if scores['simplicity'] > 70 else 0.8

        return min(weighted_score, 100)  # Cap at 100

    def _explain_ranking(self, metrics: EfficiencyMetrics, score: float) -> str:
        """Generate human-readable explanation for ranking"""
        explanations = []

        # Time-based explanation
        if metrics.time_to_solution < self.thresholds['fast_solution']:
            explanations.append(f"Very fast solution ({metrics.time_to_solution.seconds}s)")
        elif metrics.time_to_solution > self.thresholds['complex_solution']:
            explanations.append(f"Time-consuming solution ({metrics.time_to_solution.seconds}s)")

        # Complexity explanation
        if metrics.lines_changed < self.thresholds['simple_change']:
            explanations.append(f"Simple change ({metrics.lines_changed} lines)")
        elif metrics.lines_changed > self.thresholds['major_change']:
            explanations.append(f"Major refactoring ({metrics.lines_changed} lines)")

        # Reliability explanation
        if metrics.success_rate > 0.9:
            explanations.append(f"Highly reliable ({metrics.success_rate:.0%} success)")
        elif metrics.success_rate < 0.5:
            explanations.append(f"Unreliable ({metrics.success_rate:.0%} success)")

        # Recency explanation
        if metrics.recency_score > 0.8:
            explanations.append("Recently successful")
        elif metrics.recency_score < 0.3:
            explanations.append("Older pattern")

        return " | ".join(explanations) if explanations else f"Efficiency score: {score:.1f}"

    def _store_metrics(self, metrics: EfficiencyMetrics):
        """Store metrics in database"""
        import sqlite3
        conn = sqlite3.connect(self.kb.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            INSERT OR REPLACE INTO pattern_metrics
            (pattern_id, time_to_solution, lines_changed, files_touched,
             commands_executed, iterations_needed, user_interactions,
             error_rate, last_used)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            metrics.pattern_id,
            int(metrics.time_to_solution.total_seconds()),
            metrics.lines_changed,
            metrics.files_touched,
            metrics.commands_executed,
            metrics.iterations_needed,
            metrics.user_interactions,
            metrics.error_rate,
            datetime.now().isoformat()
        ))

        conn.commit()
        conn.close()

    def _get_pattern_metrics(self, pattern_id: str) -> Optional[EfficiencyMetrics]:
        """Retrieve metrics for a pattern"""
        import sqlite3
        conn = sqlite3.connect(self.kb.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT * FROM pattern_metrics
            WHERE pattern_id = ?
        ''', (pattern_id,))

        row = cursor.fetchone()
        conn.close()

        if not row:
            return None

        # Calculate recency score (decay over time)
        last_used = datetime.fromisoformat(row[11]) if row[11] else datetime.now()
        days_ago = (datetime.now() - last_used).days
        recency_score = max(0, 1 - (days_ago / 30))  # Decay over 30 days

        # Calculate frequency score
        cursor = conn.cursor()
        cursor.execute('''
            SELECT COUNT(*) FROM session_metrics
            WHERE pattern_used = ?
            AND datetime(created_at) > datetime('now', '-30 days')
        ''', (pattern_id,))
        frequency = cursor.fetchone()[0]
        conn.close()
        frequency_score = min(1.0, frequency / 10)  # Cap at 10 uses

        return EfficiencyMetrics(
            pattern_id=row[1],
            time_to_solution=timedelta(seconds=row[2]),
            lines_changed=row[3],
            files_touched=row[4],
            commands_executed=row[5],
            iterations_needed=row[6],
            user_interactions=row[7],
            error_rate=row[8],
            recency_score=recency_score,
            frequency_score=frequency_score,
            success_rate=(row[9] / (row[9] + row[10])) if (row[9] + row[10]) > 0 else 0
        )

    def compare_patterns(self, pattern_a: Dict, pattern_b: Dict, task_type: str) -> Dict:
        """Compare two patterns for the same task type"""
        metrics_a = self._get_pattern_metrics(pattern_a.get('id'))
        metrics_b = self._get_pattern_metrics(pattern_b.get('id'))

        if not metrics_a or not metrics_b:
            return {'comparison': 'insufficient_data'}

        comparison = {
            'pattern_a': pattern_a,
            'pattern_b': pattern_b,
            'task_type': task_type,
            'winner': None,
            'advantages': [],
            'metrics_comparison': {}
        }

        # Compare key metrics
        if metrics_a.time_to_solution < metrics_b.time_to_solution:
            time_diff = (metrics_b.time_to_solution - metrics_a.time_to_solution).seconds
            comparison['advantages'].append(f"Pattern A is {time_diff}s faster")
            comparison['metrics_comparison']['time'] = 'a'
        else:
            time_diff = (metrics_a.time_to_solution - metrics_b.time_to_solution).seconds
            comparison['advantages'].append(f"Pattern B is {time_diff}s faster")
            comparison['metrics_comparison']['time'] = 'b'

        if metrics_a.lines_changed < metrics_b.lines_changed:
            comparison['advantages'].append(f"Pattern A is simpler ({metrics_a.lines_changed} vs {metrics_b.lines_changed} lines)")
            comparison['metrics_comparison']['simplicity'] = 'a'
        else:
            comparison['advantages'].append(f"Pattern B is simpler ({metrics_b.lines_changed} vs {metrics_a.lines_changed} lines)")
            comparison['metrics_comparison']['simplicity'] = 'b'

        if metrics_a.success_rate > metrics_b.success_rate:
            comparison['advantages'].append(f"Pattern A more reliable ({metrics_a.success_rate:.0%} vs {metrics_b.success_rate:.0%})")
            comparison['metrics_comparison']['reliability'] = 'a'
        else:
            comparison['advantages'].append(f"Pattern B more reliable ({metrics_b.success_rate:.0%} vs {metrics_a.success_rate:.0%})")
            comparison['metrics_comparison']['reliability'] = 'b'

        # Determine overall winner
        score_a = self._calculate_efficiency_score(metrics_a)
        score_b = self._calculate_efficiency_score(metrics_b)

        if score_a > score_b:
            comparison['winner'] = 'pattern_a'
            comparison['winner_score'] = score_a
            comparison['advantage_margin'] = score_a - score_b
        else:
            comparison['winner'] = 'pattern_b'
            comparison['winner_score'] = score_b
            comparison['advantage_margin'] = score_b - score_a

        # Store comparison for learning
        self._store_comparison(comparison)

        return comparison

    def _store_comparison(self, comparison: Dict):
        """Store pattern comparison results"""
        import sqlite3
        conn = sqlite3.connect(self.kb.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO pattern_comparisons
            (pattern_a, pattern_b, task_type, winner, comparison_metric, difference_value)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            comparison['pattern_a'].get('id'),
            comparison['pattern_b'].get('id'),
            comparison['task_type'],
            comparison['winner'],
            json.dumps(comparison['metrics_comparison']),
            comparison['advantage_margin']
        ))

        conn.commit()
        conn.close()

    def get_efficiency_report(self, project: str = None) -> Dict:
        """Generate efficiency report for patterns"""
        import sqlite3
        conn = sqlite3.connect(self.kb.db_path)
        cursor = conn.cursor()

        report = {
            'project': project or 'all',
            'summary': {},
            'top_efficient': [],
            'least_efficient': [],
            'improvements': []
        }

        # Get average metrics
        cursor.execute('''
            SELECT
                AVG(time_to_solution),
                AVG(lines_changed),
                AVG(error_rate),
                COUNT(DISTINCT pattern_id)
            FROM pattern_metrics
        ''')

        avg_time, avg_lines, avg_error, pattern_count = cursor.fetchone()

        report['summary'] = {
            'total_patterns': pattern_count,
            'avg_time_to_solution': f"{avg_time:.0f}s" if avg_time else "N/A",
            'avg_lines_changed': int(avg_lines) if avg_lines else 0,
            'avg_error_rate': f"{avg_error:.1%}" if avg_error else "0%"
        }

        # Get top efficient patterns
        cursor.execute('''
            SELECT pattern_id, time_to_solution, success_count
            FROM pattern_metrics
            WHERE success_count > 0
            ORDER BY time_to_solution ASC, success_count DESC
            LIMIT 5
        ''')

        for row in cursor.fetchall():
            report['top_efficient'].append({
                'pattern_id': row[0],
                'time': f"{row[1]}s",
                'uses': row[2]
            })

        conn.close()
        return report