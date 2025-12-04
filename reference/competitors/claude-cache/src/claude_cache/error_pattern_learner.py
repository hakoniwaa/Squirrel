"""Learn from errors and failures to prevent repeating mistakes"""

import re
import json
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
import hashlib


@dataclass
class ErrorPattern:
    """Represents an error pattern and its solution"""
    error_signature: str  # Hash of the error for quick lookup
    error_message: str
    error_type: str  # 'syntax', 'runtime', 'logic', 'build', 'test', etc.
    context: Dict  # What was being attempted
    solution: str  # What fixed it
    prevention_tips: List[str] = field(default_factory=list)
    occurrence_count: int = 1
    first_seen: datetime = field(default_factory=datetime.now)
    last_seen: datetime = field(default_factory=datetime.now)
    projects: List[str] = field(default_factory=list)
    technology_stack: List[str] = field(default_factory=list)
    success_rate: float = 0.0  # How often the solution worked


class ErrorPatternLearner:
    """Learn from errors to prevent repeating mistakes"""

    def __init__(self, knowledge_base):
        self.kb = knowledge_base
        self._setup_error_tables()

        # Common error patterns and categories
        self.error_categories = {
            'import_error': [
                r"ModuleNotFoundError|ImportError|Cannot find module|Module not found",
                r"No module named|Failed to import|Unable to import"
            ],
            'type_error': [
                r"TypeError|Type '.*' is not assignable|TS\d{4}:",
                r"Property '.*' does not exist|undefined is not",
                r"Cannot read prop"
            ],
            'syntax_error': [
                r"SyntaxError|Unexpected token|Parsing error",
                r"IndentationError|Invalid syntax"
            ],
            'null_reference': [
                r"NullPointerException|NullReferenceException",
                r"Cannot read property.*of (null|undefined)",
                r"'NoneType' object"
            ],
            'build_error': [
                r"Build failed|Compilation error|webpack.*failed",
                r"error TS|ESLint.*error"
            ],
            'test_failure': [
                r"Test failed|FAIL|AssertionError",
                r"Expected.*but received|Test suite failed"
            ],
            'dependency_error': [
                r"npm ERR!|peer dep|unmet dependency",
                r"version conflict|dependency resolution"
            ],
            'permission_error': [
                r"PermissionError|Permission denied|Access denied",
                r"EACCES|EPERM"
            ],
            'network_error': [
                r"ConnectionError|TimeoutError|ECONNREFUSED",
                r"Failed to fetch|Network request failed"
            ],
            'database_error': [
                r"DatabaseError|QueryException|OperationalError",
                r"duplicate key|constraint violation|table.*not found"
            ]
        }

        # Solution patterns that commonly fix errors
        self.solution_patterns = {
            'install_dependency': r"npm install|pip install|yarn add",
            'fix_import': r"import.*from|require\(|from.*import",
            'type_assertion': r"as \w+|<\w+>|\: \w+",
            'null_check': r"if.*null|undefined|(\?\.|&&|\|\|)",
            'try_catch': r"try.*catch|except|rescue",
            'config_change': r"config|settings|env|dotenv",
            'permission_fix': r"chmod|chown|sudo",
            'restart_service': r"restart|reload|kill.*start"
        }

    def _setup_error_tables(self):
        """Create database tables for error patterns"""
        import sqlite3
        conn = sqlite3.connect(self.kb.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS error_patterns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                error_signature TEXT UNIQUE,
                error_message TEXT,
                error_type TEXT,
                context TEXT,
                solution TEXT,
                prevention_tips TEXT,
                occurrence_count INTEGER DEFAULT 1,
                success_rate REAL DEFAULT 0.0,
                first_seen DATETIME,
                last_seen DATETIME,
                projects TEXT,
                technology_stack TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS error_occurrences (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                error_signature TEXT,
                project_name TEXT,
                timestamp DATETIME,
                was_resolved BOOLEAN,
                time_to_resolution INTEGER,
                solution_applied TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (error_signature) REFERENCES error_patterns(error_signature)
            )
        ''')

        conn.commit()
        conn.close()

    def analyze_error_sequence(self, entries: List[Dict]) -> List[ErrorPattern]:
        """Analyze a sequence of entries to identify error patterns and solutions"""
        patterns = []
        error_contexts = []

        for i, entry in enumerate(entries):
            # Detect errors
            if self._contains_error(entry):
                error_info = self._extract_error_info(entry)
                if error_info:
                    # Look ahead for the solution
                    solution_info = self._find_solution(entries[i:i+10])  # Look at next 10 entries

                    if solution_info:
                        pattern = self._create_error_pattern(
                            error_info,
                            solution_info,
                            entry.get('project_name', 'unknown')
                        )
                        patterns.append(pattern)

        return patterns

    def _contains_error(self, entry: Dict) -> bool:
        """Check if an entry contains an error"""
        content = str(entry.get('content', '')).lower()

        # Check for explicit error indicators
        error_indicators = [
            'error', 'exception', 'failed', 'failure',
            'cannot', 'unable', 'undefined', 'null'
        ]

        return any(indicator in content for indicator in error_indicators)

    def _extract_error_info(self, entry: Dict) -> Optional[Dict]:
        """Extract error information from an entry"""
        content = entry.get('content', '')

        # Identify error type
        error_type = 'unknown'
        for category, patterns in self.error_categories.items():
            for pattern in patterns:
                if re.search(pattern, content, re.IGNORECASE):
                    error_type = category
                    break

        # Extract error message (first line usually)
        lines = content.split('\n')
        error_message = lines[0] if lines else content[:200]

        # Create error signature (hash for deduplication)
        # Remove specific values but keep structure
        normalized = re.sub(r'["\'].*?["\']', '""', error_message)
        normalized = re.sub(r'\d+', 'N', normalized)
        signature = hashlib.md5(normalized.encode()).hexdigest()

        return {
            'signature': signature,
            'message': error_message,
            'type': error_type,
            'full_content': content,
            'timestamp': entry.get('timestamp')
        }

    def _find_solution(self, entries: List[Dict]) -> Optional[Dict]:
        """Find the solution that fixed an error"""
        solution_info = {
            'steps': [],
            'final_fix': None,
            'time_to_resolution': 0
        }

        for entry in entries:
            # Check if this entry indicates success
            if self._indicates_resolution(entry):
                # The previous tool calls are likely the solution
                solution_info['final_fix'] = entry
                return solution_info

            # Track tool calls that might be part of the solution
            if entry.get('type') == 'tool_call':
                solution_info['steps'].append({
                    'tool': entry.get('tool'),
                    'action': entry.get('args', {})
                })

        return None if not solution_info['steps'] else solution_info

    def _indicates_resolution(self, entry: Dict) -> bool:
        """Check if an entry indicates error resolution"""
        content = str(entry.get('content', '')).lower()

        success_indicators = [
            'fixed', 'resolved', 'works', 'success',
            'passed', 'working', 'compiled successfully'
        ]

        return any(indicator in content for indicator in success_indicators)

    def _create_error_pattern(self, error_info: Dict, solution_info: Dict, project: str) -> ErrorPattern:
        """Create an ErrorPattern from error and solution information"""
        # Build solution description
        solution_steps = solution_info.get('steps', [])
        solution_text = self._describe_solution(solution_steps)

        # Generate prevention tips
        prevention_tips = self._generate_prevention_tips(error_info['type'], solution_steps)

        return ErrorPattern(
            error_signature=error_info['signature'],
            error_message=error_info['message'],
            error_type=error_info['type'],
            context={'project': project, 'timestamp': error_info['timestamp']},
            solution=solution_text,
            prevention_tips=prevention_tips,
            projects=[project]
        )

    def _describe_solution(self, steps: List[Dict]) -> str:
        """Create a human-readable description of the solution"""
        if not steps:
            return "No specific solution recorded"

        descriptions = []
        for step in steps:
            tool = step.get('tool', '')
            action = step.get('action', {})

            if tool == 'Edit':
                descriptions.append(f"Modified {action.get('file_path', 'file')}")
            elif tool == 'Bash':
                cmd = action.get('command', '')
                if 'install' in cmd:
                    descriptions.append(f"Installed dependencies: {cmd}")
                else:
                    descriptions.append(f"Ran command: {cmd}")
            elif tool == 'Write':
                descriptions.append(f"Created {action.get('file_path', 'file')}")

        return " → ".join(descriptions)

    def _generate_prevention_tips(self, error_type: str, solution_steps: List[Dict]) -> List[str]:
        """Generate prevention tips based on error type and solution"""
        tips = []

        # Type-specific tips
        if error_type == 'import_error':
            tips.append("Check package.json/requirements.txt for missing dependencies")
            tips.append("Verify import paths match file structure")
        elif error_type == 'type_error':
            tips.append("Use TypeScript or type hints for early detection")
            tips.append("Validate data types at boundaries")
        elif error_type == 'null_reference':
            tips.append("Always check for null/undefined before accessing properties")
            tips.append("Use optional chaining (?.) operator")
        elif error_type == 'build_error':
            tips.append("Run build locally before committing")
            tips.append("Keep dependencies up to date")

        # Solution-based tips
        for step in solution_steps:
            if step.get('tool') == 'Bash' and 'install' in str(step.get('action', {})):
                tips.append("Document all required dependencies in README")

        return tips

    def store_error_pattern(self, pattern: ErrorPattern):
        """Store an error pattern in the database"""
        import sqlite3
        conn = sqlite3.connect(self.kb.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute('''
                INSERT OR REPLACE INTO error_patterns
                (error_signature, error_message, error_type, context, solution,
                 prevention_tips, occurrence_count, success_rate, first_seen,
                 last_seen, projects, technology_stack)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                pattern.error_signature,
                pattern.error_message,
                pattern.error_type,
                json.dumps(pattern.context),
                pattern.solution,
                json.dumps(pattern.prevention_tips),
                pattern.occurrence_count,
                pattern.success_rate,
                pattern.first_seen.isoformat(),
                pattern.last_seen.isoformat(),
                json.dumps(pattern.projects),
                json.dumps(pattern.technology_stack)
            ))
            conn.commit()
        finally:
            conn.close()

    def find_similar_errors(self, error_message: str, project: str = None) -> List[ErrorPattern]:
        """Find similar errors that have been seen before"""
        import sqlite3
        conn = sqlite3.connect(self.kb.db_path)
        cursor = conn.cursor()

        # Create signature for lookup
        normalized = re.sub(r'["\'].*?["\']', '""', error_message)
        normalized = re.sub(r'\d+', 'N', normalized)
        signature = hashlib.md5(normalized.encode()).hexdigest()

        # First try exact match
        cursor.execute('''
            SELECT * FROM error_patterns
            WHERE error_signature = ?
            ORDER BY occurrence_count DESC
        ''', (signature,))

        results = cursor.fetchall()

        if not results:
            # Try fuzzy match on error type
            for category, patterns in self.error_categories.items():
                for pattern in patterns:
                    if re.search(pattern, error_message, re.IGNORECASE):
                        cursor.execute('''
                            SELECT * FROM error_patterns
                            WHERE error_type = ?
                            ORDER BY success_rate DESC, occurrence_count DESC
                            LIMIT 5
                        ''', (category,))
                        results = cursor.fetchall()
                        break

        conn.close()

        # Convert to ErrorPattern objects
        patterns = []
        for row in results:
            patterns.append(self._row_to_pattern(row))

        return patterns

    def _row_to_pattern(self, row) -> ErrorPattern:
        """Convert database row to ErrorPattern"""
        return ErrorPattern(
            error_signature=row[1],
            error_message=row[2],
            error_type=row[3],
            context=json.loads(row[4]) if row[4] else {},
            solution=row[5],
            prevention_tips=json.loads(row[6]) if row[6] else [],
            occurrence_count=row[7],
            success_rate=row[8],
            first_seen=datetime.fromisoformat(row[9]) if row[9] else datetime.now(),
            last_seen=datetime.fromisoformat(row[10]) if row[10] else datetime.now(),
            projects=json.loads(row[11]) if row[11] else [],
            technology_stack=json.loads(row[12]) if row[12] else []
        )

    def update_pattern_success(self, signature: str, was_successful: bool):
        """Update the success rate of an error pattern solution"""
        import sqlite3
        conn = sqlite3.connect(self.kb.db_path)
        cursor = conn.cursor()

        # Get current stats
        cursor.execute('''
            SELECT occurrence_count, success_rate FROM error_patterns
            WHERE error_signature = ?
        ''', (signature,))

        row = cursor.fetchone()
        if row:
            count, rate = row
            # Update rolling average
            new_rate = ((rate * count) + (1.0 if was_successful else 0.0)) / (count + 1)

            cursor.execute('''
                UPDATE error_patterns
                SET occurrence_count = occurrence_count + 1,
                    success_rate = ?,
                    last_seen = ?
                WHERE error_signature = ?
            ''', (new_rate, datetime.now().isoformat(), signature))

            conn.commit()
        conn.close()

    def get_prevention_guide(self, project: str) -> Dict:
        """Get a prevention guide for common errors in a project"""
        import sqlite3
        conn = sqlite3.connect(self.kb.db_path)
        cursor = conn.cursor()

        # Get top errors for this project
        cursor.execute('''
            SELECT error_type, COUNT(*) as count, AVG(success_rate) as avg_success
            FROM error_patterns
            WHERE projects LIKE ?
            GROUP BY error_type
            ORDER BY count DESC
            LIMIT 10
        ''', (f'%{project}%',))

        guide = {
            'project': project,
            'common_errors': [],
            'prevention_tips': set()
        }

        for row in cursor.fetchall():
            error_type, count, avg_success = row

            # Get prevention tips for this error type
            cursor.execute('''
                SELECT prevention_tips FROM error_patterns
                WHERE error_type = ? AND projects LIKE ?
                LIMIT 5
            ''', (error_type, f'%{project}%'))

            tips = []
            for tip_row in cursor.fetchall():
                if tip_row[0]:
                    tips.extend(json.loads(tip_row[0]))

            guide['common_errors'].append({
                'type': error_type,
                'frequency': count,
                'success_rate': avg_success,
                'prevention': list(set(tips))[:3]  # Top 3 unique tips
            })

            guide['prevention_tips'].update(tips)

        conn.close()

        guide['prevention_tips'] = list(guide['prevention_tips'])[:10]
        return guide