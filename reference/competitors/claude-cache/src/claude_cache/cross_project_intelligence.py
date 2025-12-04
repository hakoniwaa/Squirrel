"""Share and transfer knowledge across projects intelligently"""

import json
import sqlite3
from typing import Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
import re


@dataclass
class GlobalPattern:
    """A pattern that works across multiple projects"""
    pattern_id: str
    pattern_type: str  # 'auth', 'api', 'database', 'testing', 'deployment', etc.
    technology_stack: List[str]  # ['react', 'node', 'typescript', etc.]
    description: str
    solution: Dict
    projects_used: Set[str] = field(default_factory=set)
    success_rate: float = 0.0
    transferability_score: float = 0.0  # How well it transfers to new projects
    context_requirements: List[str] = field(default_factory=list)  # What needs to be present
    incompatibilities: List[str] = field(default_factory=list)  # Known conflicts


@dataclass
class ProjectProfile:
    """Profile of a project's technology and patterns"""
    project_name: str
    languages: Set[str]
    frameworks: Set[str]
    libraries: Set[str]
    pattern_types: Set[str]  # Types of patterns used
    common_tasks: List[str]
    last_updated: datetime


class CrossProjectIntelligence:
    """Share patterns and knowledge across projects intelligently"""

    def __init__(self, knowledge_base):
        self.kb = knowledge_base
        self._setup_global_tables()

        # Pattern categories that commonly transfer
        self.transferable_categories = {
            'authentication': ['jwt', 'oauth', 'session', 'login', 'signup'],
            'api_patterns': ['rest', 'graphql', 'crud', 'endpoint', 'route'],
            'database': ['query', 'migration', 'schema', 'model', 'orm'],
            'testing': ['unit test', 'integration test', 'mock', 'fixture'],
            'error_handling': ['try catch', 'error boundary', 'exception'],
            'validation': ['input validation', 'form validation', 'schema validation'],
            'deployment': ['docker', 'ci/cd', 'build', 'deploy'],
            'state_management': ['redux', 'context', 'store', 'state'],
            'styling': ['css', 'styled-components', 'tailwind', 'sass'],
            'security': ['sanitize', 'escape', 'cors', 'helmet', 'rate limit']
        }

        # Technology compatibility matrix
        self.compatibility_matrix = {
            'react': ['javascript', 'typescript', 'jsx', 'next.js', 'redux'],
            'vue': ['javascript', 'typescript', 'vuex', 'nuxt'],
            'angular': ['typescript', 'rxjs', 'ngrx'],
            'express': ['node', 'javascript', 'typescript'],
            'django': ['python', 'orm', 'rest_framework'],
            'flask': ['python', 'sqlalchemy'],
            'rails': ['ruby', 'activerecord'],
            'spring': ['java', 'kotlin', 'hibernate']
        }

    def _setup_global_tables(self):
        """Create database tables for global patterns"""
        conn = sqlite3.connect(self.kb.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS global_patterns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pattern_id TEXT UNIQUE,
                pattern_type TEXT,
                technology_stack TEXT,
                description TEXT,
                solution TEXT,
                projects_used TEXT,
                success_rate REAL,
                transferability_score REAL,
                context_requirements TEXT,
                incompatibilities TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS project_profiles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_name TEXT UNIQUE,
                languages TEXT,
                frameworks TEXT,
                libraries TEXT,
                pattern_types TEXT,
                common_tasks TEXT,
                last_updated DATETIME,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS pattern_transfers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pattern_id TEXT,
                from_project TEXT,
                to_project TEXT,
                was_successful BOOLEAN,
                adaptation_needed TEXT,
                transfer_date DATETIME,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        conn.commit()
        conn.close()

    def classify_pattern_scope(self, pattern: Dict, project_context: Dict) -> Tuple[str, float]:
        """Classify if a pattern is project-specific or universal"""
        universality_score = 0.0
        classification = "unknown"

        # Analyze pattern content for specificity indicators
        approach = pattern.get('approach', '').lower()
        files_involved = pattern.get('files_involved', [])
        tags = pattern.get('tags', [])

        # Universal pattern indicators
        universal_indicators = {
            'authentication': ['auth', 'login', 'jwt', 'oauth', 'session'],
            'database': ['query', 'sql', 'orm', 'migration', 'schema'],
            'api': ['rest', 'api', 'endpoint', 'http', 'request'],
            'testing': ['test', 'spec', 'unit', 'integration', 'e2e'],
            'error_handling': ['error', 'exception', 'try', 'catch', 'handle'],
            'security': ['security', 'validation', 'sanitize', 'encrypt'],
            'performance': ['cache', 'optimize', 'performance', 'speed'],
            'deployment': ['deploy', 'build', 'ci', 'cd', 'docker']
        }

        # Project-specific indicators
        project_specific_indicators = [
            'this project', 'our codebase', 'specific to',
            'custom implementation', 'project requirement',
            'team convention', 'local setup'
        ]

        # Check for universal patterns
        for category, keywords in universal_indicators.items():
            if any(keyword in approach for keyword in keywords):
                universality_score += 0.3
                if any(keyword in str(tags) for keyword in keywords):
                    universality_score += 0.2

        # Check for project-specific indicators
        for indicator in project_specific_indicators:
            if indicator in approach:
                universality_score -= 0.4

        # Analyze file paths for project specificity
        if files_involved:
            generic_paths = ['src/', 'lib/', 'components/', 'utils/', 'helpers/']
            specific_paths = ['config/', 'settings/', '.env', 'local/', 'custom/']

            for file_path in files_involved:
                if any(generic in file_path for generic in generic_paths):
                    universality_score += 0.1
                if any(specific in file_path for specific in specific_paths):
                    universality_score -= 0.2

        # Determine classification
        if universality_score > 0.6:
            classification = "universal"
        elif universality_score > 0.3:
            classification = "transferable"
        elif universality_score > 0.0:
            classification = "context_dependent"
        else:
            classification = "project_specific"

        return classification, max(0.0, min(1.0, universality_score))

    def get_contextual_patterns(self, project_name: str, current_context: Dict, limit: int = 5) -> List[Dict]:
        """Get patterns most relevant to current project and context"""
        project_profile = self._get_project_profile(project_name)

        # Get project-specific patterns first
        project_patterns = self._get_patterns_for_project(project_name)

        # Get universal patterns that match project stack
        universal_patterns = self._get_universal_patterns_for_stack(
            project_profile.languages if project_profile else set(),
            project_profile.frameworks if project_profile else set()
        )

        # Combine and rank by relevance to current context
        all_patterns = project_patterns + universal_patterns
        ranked_patterns = self._rank_patterns_by_context(all_patterns, current_context)

        return ranked_patterns[:limit]

    def _rank_patterns_by_context(self, patterns: List[Dict], context: Dict) -> List[Dict]:
        """Rank patterns by relevance to current context"""
        current_file = context.get('current_file', '')
        current_task = context.get('current_task', '').lower()
        recent_patterns = context.get('recent_successful_patterns', [])

        scored_patterns = []

        for pattern in patterns:
            score = 0.0

            # Match file type/extension
            if current_file:
                pattern_files = pattern.get('files_involved', [])
                current_ext = current_file.split('.')[-1] if '.' in current_file else ''
                for file_path in pattern_files:
                    if current_ext and file_path.endswith(f'.{current_ext}'):
                        score += 0.3

            # Match task/intent similarity
            if current_task:
                approach = pattern.get('approach', '').lower()
                common_words = set(current_task.split()) & set(approach.split())
                score += len(common_words) * 0.1

            # Boost recently successful similar patterns
            pattern_tags = set(pattern.get('tags', []))
            for recent in recent_patterns:
                recent_tags = set(recent.get('tags', []))
                tag_overlap = len(pattern_tags & recent_tags)
                if tag_overlap > 0:
                    score += tag_overlap * 0.2

            # Consider pattern success rate and confidence
            confidence = pattern.get('confidence', 'medium')
            confidence_boost = {'high': 0.3, 'medium': 0.1, 'low': 0.0}
            score += confidence_boost.get(confidence, 0.0)

            scored_patterns.append((pattern, score))

        # Sort by score descending
        scored_patterns.sort(key=lambda x: x[1], reverse=True)
        return [pattern for pattern, score in scored_patterns]

    def analyze_project(self, project_name: str, entries: List[Dict]) -> ProjectProfile:
        """Analyze a project to build its profile"""
        languages = set()
        frameworks = set()
        libraries = set()
        pattern_types = set()
        common_tasks = []

        for entry in entries:
            content = str(entry.get('content', '')).lower()

            # Detect languages
            if 'import' in content or 'from' in content:
                if 'react' in content:
                    frameworks.add('react')
                    languages.add('javascript')
                if 'typescript' in content or '.ts' in content:
                    languages.add('typescript')
                if 'python' in content or '.py' in content:
                    languages.add('python')

            # Detect frameworks
            for fw in ['express', 'django', 'flask', 'rails', 'spring', 'next', 'nuxt', 'angular', 'vue']:
                if fw in content:
                    frameworks.add(fw)

            # Detect pattern types
            for category, keywords in self.transferable_categories.items():
                if any(kw in content for kw in keywords):
                    pattern_types.add(category)

            # Track common tasks
            if entry.get('type') == 'user_message':
                common_tasks.append(entry.get('content', '')[:100])

        profile = ProjectProfile(
            project_name=project_name,
            languages=languages,
            frameworks=frameworks,
            libraries=libraries,
            pattern_types=pattern_types,
            common_tasks=common_tasks[-10:],  # Keep last 10 tasks
            last_updated=datetime.now()
        )

        self._store_project_profile(profile)
        return profile

    def _get_project_profile(self, project_name: str) -> Optional[ProjectProfile]:
        """Get stored project profile"""
        conn = sqlite3.connect(self.kb.db_path)
        cursor = conn.cursor()

        cursor.execute(
            'SELECT * FROM project_profiles WHERE project_name = ?',
            (project_name,)
        )
        result = cursor.fetchone()
        conn.close()

        if result:
            return ProjectProfile(
                project_name=result[1],
                languages=set(json.loads(result[2])) if result[2] else set(),
                frameworks=set(json.loads(result[3])) if result[3] else set(),
                libraries=set(json.loads(result[4])) if result[4] else set(),
                pattern_types=set(json.loads(result[5])) if result[5] else set(),
                common_tasks=json.loads(result[6]) if result[6] else [],
                last_updated=datetime.fromisoformat(result[7]) if result[7] else datetime.now()
            )
        return None

    def _get_patterns_for_project(self, project_name: str) -> List[Dict]:
        """Get patterns specific to a project"""
        conn = sqlite3.connect(self.kb.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT * FROM success_patterns
            WHERE project_name = ?
            ORDER BY created_at DESC
            LIMIT 20
        ''', (project_name,))

        patterns = []
        for row in cursor.fetchall():
            pattern = {
                'id': row[0],
                'project_name': row[1],
                'approach': row[3],
                'files_involved': json.loads(row[4]) if row[4] else [],
                'tags': json.loads(row[6]) if row[6] else [],
                'confidence': 'medium',  # Default confidence
                'scope': 'project_specific'
            }
            patterns.append(pattern)

        conn.close()
        return patterns

    def _get_universal_patterns_for_stack(self, languages: set, frameworks: set) -> List[Dict]:
        """Get universal patterns that match the tech stack"""
        conn = sqlite3.connect(self.kb.db_path)
        cursor = conn.cursor()

        # Look for patterns from global_patterns table
        cursor.execute('''
            SELECT * FROM global_patterns
            WHERE transferability_score > 0.6
            ORDER BY success_rate DESC
            LIMIT 15
        ''')

        patterns = []
        for row in cursor.fetchall():
            tech_stack = json.loads(row[2]) if row[2] else []
            # Check if this pattern's tech stack overlaps with project's
            if any(tech in tech_stack for tech in languages | frameworks):
                pattern = {
                    'id': row[0],
                    'pattern_type': row[1],
                    'tech_stack': tech_stack,
                    'description': row[3],
                    'approach': row[3],  # Use description as approach for now
                    'success_rate': row[5],
                    'transferability_score': row[6],
                    'confidence': 'high' if row[5] > 0.8 else 'medium',
                    'scope': 'universal'
                }
                patterns.append(pattern)

        conn.close()
        return patterns

    def identify_transferable_patterns(self, pattern: Dict, source_project: str) -> GlobalPattern:
        """Identify if a pattern can be used across projects"""
        pattern_type = self._categorize_pattern(pattern)
        tech_stack = self._extract_technology_stack(pattern)

        # Check how many projects could use this
        compatible_projects = self._find_compatible_projects(tech_stack)

        transferability = len(compatible_projects) / max(1, self._count_total_projects())

        global_pattern = GlobalPattern(
            pattern_id=f"global_{pattern.get('id', '')}",
            pattern_type=pattern_type,
            technology_stack=tech_stack,
            description=pattern.get('user_request', ''),
            solution=pattern,
            projects_used={source_project},
            success_rate=pattern.get('success_score', 0.0),
            transferability_score=transferability,
            context_requirements=self._extract_requirements(pattern),
            incompatibilities=self._identify_incompatibilities(tech_stack)
        )

        if transferability > 0.3:  # If >30% of projects could use it
            self._store_global_pattern(global_pattern)

        return global_pattern

    def _categorize_pattern(self, pattern: Dict) -> str:
        """Categorize a pattern into a type"""
        request = pattern.get('user_request', '').lower()
        approach = pattern.get('approach', '').lower()

        for category, keywords in self.transferable_categories.items():
            if any(kw in request or kw in approach for kw in keywords):
                return category

        return 'general'

    def _extract_technology_stack(self, pattern: Dict) -> List[str]:
        """Extract technology stack from a pattern"""
        stack = []
        files = pattern.get('files_involved', [])

        for file in files:
            if '.ts' in file or '.tsx' in file:
                stack.append('typescript')
            elif '.js' in file or '.jsx' in file:
                stack.append('javascript')
            elif '.py' in file:
                stack.append('python')
            elif '.rb' in file:
                stack.append('ruby')
            elif '.java' in file:
                stack.append('java')

            # Framework detection from file paths
            if 'react' in file.lower() or 'component' in file.lower():
                stack.append('react')
            elif 'django' in file.lower():
                stack.append('django')
            elif 'express' in file.lower():
                stack.append('express')

        return list(set(stack))

    def _extract_requirements(self, pattern: Dict) -> List[str]:
        """Extract what needs to be present for this pattern to work"""
        requirements = []

        # Check for specific dependencies
        operations = pattern.get('key_operations', [])
        for op in operations:
            if op.get('tool') == 'Bash':
                cmd = op.get('command', '')
                if 'npm install' in cmd:
                    # Extract package names
                    packages = re.findall(r'npm install ([\w-]+)', cmd)
                    requirements.extend([f"npm:{p}" for p in packages])
                elif 'pip install' in cmd:
                    packages = re.findall(r'pip install ([\w-]+)', cmd)
                    requirements.extend([f"pip:{p}" for p in packages])

        # Check for file structure requirements
        files = pattern.get('files_involved', [])
        for file in files:
            if 'config' in file.lower():
                requirements.append(f"config_file:{file}")

        return requirements

    def _identify_incompatibilities(self, tech_stack: List[str]) -> List[str]:
        """Identify known incompatibilities"""
        incompatibilities = []

        # Check for conflicting frameworks
        if 'react' in tech_stack and 'angular' in tech_stack:
            incompatibilities.append('Mixed frontend frameworks')
        if 'django' in tech_stack and 'express' in tech_stack:
            incompatibilities.append('Mixed backend frameworks')

        return incompatibilities

    def find_relevant_global_patterns(self, project: str, request: str) -> List[GlobalPattern]:
        """Find global patterns relevant to a project and request"""
        # Get project profile
        profile = self._get_project_profile(project)
        if not profile:
            return []

        # Get all global patterns
        conn = sqlite3.connect(self.kb.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT * FROM global_patterns
            WHERE transferability_score > 0.3
            ORDER BY success_rate DESC, transferability_score DESC
        ''')

        patterns = []
        for row in cursor.fetchall():
            global_pattern = self._row_to_global_pattern(row)

            # Check compatibility
            if self._is_compatible(global_pattern, profile):
                # Check relevance to request
                if self._is_relevant_to_request(global_pattern, request):
                    patterns.append(global_pattern)

        conn.close()
        return patterns[:5]  # Return top 5 relevant patterns

    def _is_compatible(self, pattern: GlobalPattern, profile: ProjectProfile) -> bool:
        """Check if a global pattern is compatible with a project"""
        # Check technology stack compatibility
        pattern_tech = set(pattern.technology_stack)
        project_tech = profile.languages.union(profile.frameworks)

        # Need at least one common technology
        if not pattern_tech.intersection(project_tech):
            return False

        # Check for incompatibilities
        for incomp in pattern.incompatibilities:
            if incomp in str(project_tech):
                return False

        return True

    def _is_relevant_to_request(self, pattern: GlobalPattern, request: str) -> bool:
        """Check if a pattern is relevant to a user request"""
        request_lower = request.lower()

        # Check pattern type relevance
        for category, keywords in self.transferable_categories.items():
            if pattern.pattern_type == category:
                if any(kw in request_lower for kw in keywords):
                    return True

        # Check description similarity
        pattern_desc = pattern.description.lower()
        # Simple word overlap
        request_words = set(request_lower.split())
        pattern_words = set(pattern_desc.split())
        overlap = len(request_words.intersection(pattern_words))

        return overlap > 2  # At least 3 common words

    def transfer_pattern(self, pattern: GlobalPattern, to_project: str, adaptation_hints: Dict = None) -> Dict:
        """Transfer a global pattern to a new project with adaptations"""
        # Get target project profile
        target_profile = self._get_project_profile(to_project)
        if not target_profile:
            return {'success': False, 'reason': 'Unknown target project'}

        # Adapt the pattern for the target project
        adapted_solution = self._adapt_solution(pattern.solution, target_profile, adaptation_hints)

        # Record the transfer
        self._record_transfer(pattern.pattern_id, pattern.projects_used, to_project, adaptation_hints)

        return {
            'success': True,
            'original_pattern': pattern,
            'adapted_solution': adapted_solution,
            'adaptations_made': adaptation_hints or {},
            'confidence': self._calculate_transfer_confidence(pattern, target_profile)
        }

    def _adapt_solution(self, solution: Dict, target_profile: ProjectProfile, hints: Dict = None) -> Dict:
        """Adapt a solution for a different project context"""
        adapted = solution.copy()

        # Adapt file paths if needed
        if 'files_involved' in adapted:
            adapted['files_involved'] = self._adapt_file_paths(
                adapted['files_involved'],
                target_profile
            )

        # Adapt technology-specific elements
        if hints:
            if 'language_mapping' in hints:
                # e.g., {'javascript': 'typescript'}
                adapted['solution_steps'] = self._translate_language_specifics(
                    adapted.get('solution_steps', []),
                    hints['language_mapping']
                )

        return adapted

    def _adapt_file_paths(self, files: List[str], profile: ProjectProfile) -> List[str]:
        """Adapt file paths to match project structure"""
        adapted = []
        for file in files:
            # Simple heuristic: preserve filename but adjust extension
            base_name = Path(file).stem

            if 'typescript' in profile.languages:
                if file.endswith('.js'):
                    adapted.append(file.replace('.js', '.ts'))
                elif file.endswith('.jsx'):
                    adapted.append(file.replace('.jsx', '.tsx'))
                else:
                    adapted.append(file)
            else:
                adapted.append(file)

        return adapted

    def _translate_language_specifics(self, steps: List[Dict], mapping: Dict) -> List[Dict]:
        """Translate language-specific elements in solution steps"""
        # This would be more sophisticated in practice
        translated = []
        for step in steps:
            if isinstance(step, dict):
                step_copy = step.copy()
                # Simple keyword replacement for demo
                if 'action' in step_copy:
                    for old_lang, new_lang in mapping.items():
                        step_copy['action'] = step_copy['action'].replace(old_lang, new_lang)
                translated.append(step_copy)
            else:
                translated.append(step)
        return translated

    def _calculate_transfer_confidence(self, pattern: GlobalPattern, profile: ProjectProfile) -> float:
        """Calculate confidence in pattern transfer success"""
        confidence = pattern.transferability_score

        # Boost if same technology stack
        tech_overlap = len(set(pattern.technology_stack).intersection(
            profile.languages.union(profile.frameworks)
        ))
        confidence += tech_overlap * 0.1

        # Reduce if pattern hasn't been used much
        if len(pattern.projects_used) < 3:
            confidence *= 0.8

        return min(confidence, 1.0)

    def _store_global_pattern(self, pattern: GlobalPattern):
        """Store a global pattern in the database"""
        conn = sqlite3.connect(self.kb.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            INSERT OR REPLACE INTO global_patterns
            (pattern_id, pattern_type, technology_stack, description, solution,
             projects_used, success_rate, transferability_score,
             context_requirements, incompatibilities)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            pattern.pattern_id,
            pattern.pattern_type,
            json.dumps(list(pattern.technology_stack)),
            pattern.description,
            json.dumps(pattern.solution),
            json.dumps(list(pattern.projects_used)),
            pattern.success_rate,
            pattern.transferability_score,
            json.dumps(pattern.context_requirements),
            json.dumps(pattern.incompatibilities)
        ))

        conn.commit()
        conn.close()

    def _store_project_profile(self, profile: ProjectProfile):
        """Store a project profile in the database"""
        conn = sqlite3.connect(self.kb.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            INSERT OR REPLACE INTO project_profiles
            (project_name, languages, frameworks, libraries, pattern_types,
             common_tasks, last_updated)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            profile.project_name,
            json.dumps(list(profile.languages)),
            json.dumps(list(profile.frameworks)),
            json.dumps(list(profile.libraries)),
            json.dumps(list(profile.pattern_types)),
            json.dumps(profile.common_tasks),
            profile.last_updated.isoformat()
        ))

        conn.commit()
        conn.close()

    def _record_transfer(self, pattern_id: str, from_projects: Set[str], to_project: str, adaptation: Dict = None):
        """Record a pattern transfer"""
        conn = sqlite3.connect(self.kb.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO pattern_transfers
            (pattern_id, from_project, to_project, was_successful, adaptation_needed, transfer_date)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            pattern_id,
            json.dumps(list(from_projects)),
            to_project,
            True,  # Will be updated later based on outcome
            json.dumps(adaptation) if adaptation else None,
            datetime.now().isoformat()
        ))

        conn.commit()
        conn.close()

    def _get_project_profile(self, project_name: str) -> Optional[ProjectProfile]:
        """Retrieve a project profile"""
        conn = sqlite3.connect(self.kb.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT * FROM project_profiles
            WHERE project_name = ?
        ''', (project_name,))

        row = cursor.fetchone()
        conn.close()

        if not row:
            return None

        return ProjectProfile(
            project_name=row[1],
            languages=set(json.loads(row[2])) if row[2] else set(),
            frameworks=set(json.loads(row[3])) if row[3] else set(),
            libraries=set(json.loads(row[4])) if row[4] else set(),
            pattern_types=set(json.loads(row[5])) if row[5] else set(),
            common_tasks=json.loads(row[6]) if row[6] else [],
            last_updated=datetime.fromisoformat(row[7]) if row[7] else datetime.now()
        )

    def _find_compatible_projects(self, tech_stack: List[str]) -> List[str]:
        """Find projects compatible with a technology stack"""
        conn = sqlite3.connect(self.kb.db_path)
        cursor = conn.cursor()

        cursor.execute('SELECT project_name, languages, frameworks FROM project_profiles')

        compatible = []
        for row in cursor.fetchall():
            project_tech = set()
            if row[1]:
                project_tech.update(json.loads(row[1]))
            if row[2]:
                project_tech.update(json.loads(row[2]))

            if project_tech.intersection(set(tech_stack)):
                compatible.append(row[0])

        conn.close()
        return compatible

    def _count_total_projects(self) -> int:
        """Count total number of projects"""
        conn = sqlite3.connect(self.kb.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(DISTINCT project_name) FROM project_profiles')
        count = cursor.fetchone()[0]
        conn.close()
        return count

    def _row_to_global_pattern(self, row) -> GlobalPattern:
        """Convert database row to GlobalPattern"""
        return GlobalPattern(
            pattern_id=row[1],
            pattern_type=row[2],
            technology_stack=json.loads(row[3]) if row[3] else [],
            description=row[4],
            solution=json.loads(row[5]) if row[5] else {},
            projects_used=set(json.loads(row[6])) if row[6] else set(),
            success_rate=row[7],
            transferability_score=row[8],
            context_requirements=json.loads(row[9]) if row[9] else [],
            incompatibilities=json.loads(row[10]) if row[10] else []
        )

    def generate_cross_project_insights(self) -> Dict:
        """Generate insights about patterns across all projects"""
        conn = sqlite3.connect(self.kb.db_path)
        cursor = conn.cursor()

        insights = {
            'most_transferable': [],
            'most_successful': [],
            'common_stacks': [],
            'pattern_distribution': {}
        }

        # Most transferable patterns
        cursor.execute('''
            SELECT pattern_type, AVG(transferability_score) as avg_transfer, COUNT(*) as count
            FROM global_patterns
            GROUP BY pattern_type
            ORDER BY avg_transfer DESC
            LIMIT 5
        ''')

        for row in cursor.fetchall():
            insights['most_transferable'].append({
                'type': row[0],
                'transferability': f"{row[1]:.0%}",
                'count': row[2]
            })

        # Most successful patterns
        cursor.execute('''
            SELECT pattern_type, AVG(success_rate) as avg_success, COUNT(*) as count
            FROM global_patterns
            WHERE success_rate > 0
            GROUP BY pattern_type
            ORDER BY avg_success DESC
            LIMIT 5
        ''')

        for row in cursor.fetchall():
            insights['most_successful'].append({
                'type': row[0],
                'success_rate': f"{row[1]:.0%}",
                'count': row[2]
            })

        conn.close()
        return insights