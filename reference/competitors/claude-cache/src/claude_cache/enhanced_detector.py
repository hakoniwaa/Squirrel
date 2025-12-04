"""Enhanced success detection with tech stack awareness and execution monitoring"""

import re
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from .config import DetectionConfig
from .success_detector import SuccessDetector

class EnhancedSuccessDetector(SuccessDetector):
    """Stack-aware success pattern detection"""

    def __init__(self):
        super().__init__()
        self.config = DetectionConfig()

        # Execution success patterns for different build tools
        self.execution_success_patterns = {
            'build_tools': {
                'npm': r'(npm run build|npm run dev).*(?:success|completed|ready|listening)',
                'yarn': r'(yarn build|yarn dev).*(?:success|completed|ready|listening)',
                'cargo': r'cargo.*(?:finished|release)',
                'go': r'go.*(?:build|run).*(?:success|ready)',
                'python': r'python.*(?:completed|success|server.*running)',
                'make': r'make.*(?:success|completed|finished)',
                'webpack': r'webpack.*(?:compiled|success|ready)',
                'vite': r'vite.*(?:ready|dev server running)'
            },
            'test_tools': {
                'jest': r'Tests:.*passed|All tests passed|✓.*test.*passed',
                'pytest': r'(\d+) passed|test.*passed|✓.*passed',
                'cargo_test': r'test result: ok',
                'go_test': r'PASS|ok\s+\S+',
                'mocha': r'\d+\s+passing',
                'vitest': r'Test.*passed|✓.*tests? passed',
                'phpunit': r'OK.*tests',
                'rspec': r'\d+.*examples.*0 failures'
            },
            'linters': {
                'eslint': r'✓.*no.*problems',
                'typescript': r'Found 0 errors',
                'pylint': r'Your code.*rated.*10\.00/10',
                'clippy': r'0 warnings?.*emitted',
                'golint': r'no.*issues',
                'rubocop': r'no.*offenses'
            }
        }

        # Error patterns that indicate failure
        self.execution_error_patterns = {
            'build_errors': [
                r'error|Error|ERROR',
                r'failed|Failed|FAILED',
                r'compilation.*failed',
                r'build.*failed',
                r'syntax.*error',
                r'cannot.*find.*module',
                r'unexpected.*token'
            ],
            'test_errors': [
                r'(\d+)\s+(failed|failing)',
                r'test.*failed',
                r'assertion.*failed',
                r'expected.*but.*got',
                r'✗.*failed',
                r'FAIL.*test'
            ],
            'runtime_errors': [
                r'uncaught.*exception',
                r'segmentation.*fault',
                r'panic:',
                r'fatal.*error',
                r'500.*internal.*server.*error',
                r'connection.*refused'
            ]
        }

        # Add stack-specific success patterns
        self.stack_success_patterns = {
            'frontend': {
                'component_working': r'component\s+(renders?|works?|displays?)',
                'styling_fixed': r'(css|style|styling|layout)\s+(fixed|working|correct)',
                'state_managed': r'state\s+(management|updated|synchronized)',
                'responsive': r'responsive|mobile.*(working|fixed)',
                'performance': r'(render|load|performance).*(optimized|improved|faster)'
            },
            'backend': {
                'api_working': r'(api|endpoint|route).*(working|successful|returns)',
                'auth_implemented': r'(auth|authentication|authorization).*(working|implemented)',
                'validation': r'validation.*(added|working|successful)',
                'error_handled': r'error.*(handled|caught|fixed)',
                'tested': r'(unit|integration|api).*(test|tests).*(pass|passing)'
            },
            'database': {
                'query_optimized': r'query.*(optimized|faster|improved)',
                'migration_successful': r'migration.*(successful|completed|applied)',
                'index_added': r'index.*(added|created|optimized)',
                'schema_updated': r'schema.*(updated|modified|migrated)',
                'performance': r'(database|query|db).*(faster|optimized)'
            }
        }

    def analyze_session_success(self, session_entries: List[Dict]) -> Dict:
        """Enhanced analysis with stack awareness and execution monitoring"""
        # Detect tech stack from session
        tech_stacks = self._detect_session_stacks(session_entries)

        # Get base analysis (user feedback signals)
        base_result = super().analyze_session_success(session_entries)

        # Analyze execution results (build/test/lint success)
        execution_result = self._analyze_execution_success(session_entries)

        # Enhance with stack-specific analysis
        stack_scores = {}
        if tech_stacks:
            stack_scores = self._analyze_stack_specific_success(session_entries, tech_stacks)

        # Calculate combined intelligence score
        enhanced_score = self._calculate_combined_score(
            base_result['score'],
            execution_result['score'],
            stack_scores
        )

        base_result['enhanced_score'] = enhanced_score
        base_result['execution_success'] = execution_result
        base_result['tech_stacks'] = tech_stacks
        base_result['stack_scores'] = stack_scores

        # Determine success using combined signals
        # High confidence if both user and execution signals agree
        user_positive = isinstance(base_result['score'], (int, float)) and base_result['score'] > 0.4
        execution_positive = isinstance(execution_result['score'], (int, float)) and execution_result['score'] > 0.5

        if user_positive and execution_positive:
            # Both signals agree - high confidence
            base_result['success'] = True
            base_result['confidence'] = 'high'
        elif execution_positive and enhanced_score > 0.4:
            # Execution success with reasonable overall score
            base_result['success'] = True
            base_result['confidence'] = 'medium'
        elif user_positive and enhanced_score > 0.3:
            # User positive with decent overall score
            base_result['success'] = True
            base_result['confidence'] = 'medium'
        else:
            base_result['success'] = False
            base_result['confidence'] = 'low'

        # Extract pattern if successful
        if base_result['success'] and not base_result.get('pattern'):
            base_result['pattern'] = self.extract_success_pattern(session_entries)
            if base_result['pattern']:
                # Add enhanced metadata
                base_result['pattern']['tech_stacks'] = tech_stacks
                base_result['pattern']['execution_evidence'] = execution_result['evidence']
                base_result['pattern']['stack_specific_wins'] = self._extract_stack_wins(
                    session_entries, tech_stacks
                )
                base_result['pattern']['confidence'] = base_result['confidence']

        return base_result

    def _detect_session_stacks(self, entries: List[Dict]) -> List[str]:
        """Detect which tech stacks are involved in the session"""
        stacks = set()

        for entry in entries:
            # Check file operations
            if entry.get('type') == 'tool_call':
                args = entry.get('args', {})
                file_path = args.get('file_path', '') or args.get('path', '')

                if file_path:
                    detected = self.config.get_stack_for_file(file_path)
                    stacks.update(detected)

            # Check content for keywords
            content = str(entry.get('content', '')).lower()
            for stack_name, stack_config in self.config.stack_patterns.items():
                if any(keyword in content for keyword in stack_config['keywords']):
                    stacks.add(stack_name)

        return list(stacks)

    def _analyze_stack_specific_success(self, entries: List[Dict], stacks: List[str]) -> Dict[str, float]:
        """Analyze success for each detected stack"""
        stack_scores = {}

        for stack in stacks:
            if stack in self.stack_success_patterns:
                patterns = self.stack_success_patterns[stack]
                score = self._calculate_stack_score(entries, patterns, stack)
                stack_scores[stack] = score

        return stack_scores

    def _calculate_stack_score(self, entries: List[Dict], patterns: Dict[str, str], stack: str) -> float:
        """Calculate success score for a specific stack"""
        total_matches = 0
        pattern_weights = {
            'frontend': {
                'component_working': 0.3,
                'styling_fixed': 0.2,
                'state_managed': 0.2,
                'responsive': 0.15,
                'performance': 0.15
            },
            'backend': {
                'api_working': 0.3,
                'auth_implemented': 0.25,
                'validation': 0.15,
                'error_handled': 0.15,
                'tested': 0.15
            },
            'database': {
                'query_optimized': 0.3,
                'migration_successful': 0.25,
                'index_added': 0.2,
                'schema_updated': 0.15,
                'performance': 0.1
            }
        }

        weights = pattern_weights.get(stack, {})
        score = 0

        for entry in entries:
            content = str(entry.get('content', ''))

            for pattern_name, regex in patterns.items():
                if re.search(regex, content, re.IGNORECASE):
                    weight = weights.get(pattern_name, 0.2)
                    score += weight

        # Check for stack-specific error patterns
        error_penalty = self._check_stack_errors(entries, stack)
        score = max(0, score - error_penalty)

        return min(score, 1.0)  # Cap at 1.0

    def _check_stack_errors(self, entries: List[Dict], stack: str) -> float:
        """Check for stack-specific errors"""
        error_patterns = {
            'frontend': [
                r'console\.(error|warn)',
                r'cannot read property',
                r'undefined is not',
                r'hydration failed',
                r'react error'
            ],
            'backend': [
                r'500\s+error',
                r'internal server error',
                r'unauthorized',
                r'forbidden',
                r'connection refused'
            ],
            'database': [
                r'syntax error',
                r'connection failed',
                r'deadlock',
                r'constraint violation',
                r'timeout'
            ]
        }

        patterns = error_patterns.get(stack, [])
        error_count = 0

        for entry in entries:
            content = str(entry.get('content', '')).lower()
            for pattern in patterns:
                if re.search(pattern, content, re.IGNORECASE):
                    error_count += 1

        # Each error reduces score by 0.1
        return min(error_count * 0.1, 0.5)  # Cap penalty at 0.5

    def _calculate_enhanced_score(self, base_score: float, stack_scores: Dict[str, float]) -> float:
        """Combine base and stack-specific scores"""
        if not stack_scores:
            return float(base_score) if base_score else 0.0

        try:
            # Weight: 60% base score, 40% stack-specific
            # Ensure all values are floats
            base = float(base_score) if base_score else 0.0
            stack_values = [float(v) for v in stack_scores.values() if isinstance(v, (int, float))]
            if not stack_values:
                return base
            stack_avg = sum(stack_values) / len(stack_values)
            return (base * 0.6) + (stack_avg * 0.4)
        except (TypeError, ValueError):
            # Fallback to base score if calculation fails
            return float(base_score) if base_score else 0.0

    def _extract_stack_wins(self, entries: List[Dict], stacks: List[str]) -> Dict[str, List[str]]:
        """Extract specific wins for each stack"""
        wins = {stack: [] for stack in stacks}

        for entry in entries:
            if entry.get('type') == 'assistant_message':
                content = entry.get('content', '')

                for stack in stacks:
                    if stack == 'frontend':
                        if 'component' in content.lower() and 'working' in content.lower():
                            wins[stack].append('Component implementation successful')
                        if 'styled' in content.lower() or 'css' in content.lower():
                            wins[stack].append('Styling completed')

                    elif stack == 'backend':
                        if 'endpoint' in content.lower() or 'api' in content.lower():
                            wins[stack].append('API endpoint implemented')
                        if 'auth' in content.lower():
                            wins[stack].append('Authentication handled')

                    elif stack == 'database':
                        if 'query' in content.lower() and 'optimized' in content.lower():
                            wins[stack].append('Query optimization successful')
                        if 'migration' in content.lower():
                            wins[stack].append('Database migration completed')

        return wins

    def _analyze_execution_success(self, entries: List[Dict]) -> Dict:
        """Analyze execution results from build tools, tests, etc."""
        execution_score = 0.0
        evidence = []
        build_success = False
        test_success = False
        lint_success = False

        for entry in entries:
            content = str(entry.get('content', ''))

            # Check for build tool success
            for tool, pattern in self.execution_success_patterns['build_tools'].items():
                if re.search(pattern, content, re.IGNORECASE):
                    build_success = True
                    execution_score += 0.4
                    evidence.append(f"Build successful ({tool})")
                    break

            # Check for test success
            for tool, pattern in self.execution_success_patterns['test_tools'].items():
                if re.search(pattern, content, re.IGNORECASE):
                    test_success = True
                    execution_score += 0.4
                    evidence.append(f"Tests passed ({tool})")
                    break

            # Check for linter success
            for tool, pattern in self.execution_success_patterns['linters'].items():
                if re.search(pattern, content, re.IGNORECASE):
                    lint_success = True
                    execution_score += 0.2
                    evidence.append(f"Linting passed ({tool})")
                    break

            # Check for error patterns that reduce confidence
            for error_type, patterns in self.execution_error_patterns.items():
                for pattern in patterns:
                    if re.search(pattern, content, re.IGNORECASE):
                        execution_score = max(0, execution_score - 0.3)
                        evidence.append(f"Error detected ({error_type})")

        # Look for error → success transitions
        error_to_success = self._detect_error_resolution(entries)
        if error_to_success:
            execution_score += 0.3
            evidence.append("Error resolved successfully")

        return {
            'score': min(execution_score, 1.0),
            'build_success': build_success,
            'test_success': test_success,
            'lint_success': lint_success,
            'evidence': evidence,
            'error_resolution': error_to_success
        }

    def _detect_error_resolution(self, entries: List[Dict]) -> bool:
        """Detect if errors were resolved during the session"""
        had_error = False
        error_resolved = False

        for i, entry in enumerate(entries):
            content = str(entry.get('content', ''))

            # Check if this entry contains an error
            has_error = any(
                any(re.search(pattern, content, re.IGNORECASE) for pattern in patterns)
                for patterns in self.execution_error_patterns.values()
            )

            if has_error:
                had_error = True
            elif had_error and i > 0:
                # Look for success patterns after we've seen errors
                has_success = any(
                    any(re.search(pattern, content, re.IGNORECASE) for pattern in patterns.values())
                    for patterns in self.execution_success_patterns.values()
                )
                if has_success:
                    error_resolved = True

        return had_error and error_resolved

    def _calculate_combined_score(self, user_score: float, execution_score: float, stack_scores: Dict[str, float]) -> float:
        """Calculate combined intelligence score from all signals"""
        try:
            # Ensure all scores are floats
            user = float(user_score) if user_score else 0.0
            execution = float(execution_score) if execution_score else 0.0

            # Calculate stack average
            stack_values = [float(v) for v in stack_scores.values() if isinstance(v, (int, float))]
            stack_avg = sum(stack_values) / len(stack_values) if stack_values else 0.0

            # Weight the different signals
            # Execution results are most reliable, then user feedback, then stack-specific
            if execution > 0:
                # When we have execution evidence, weight it heavily
                combined = (execution * 0.5) + (user * 0.3) + (stack_avg * 0.2)
            else:
                # When no execution evidence, rely more on user feedback
                combined = (user * 0.6) + (stack_avg * 0.4)

            return min(combined, 1.0)
        except (TypeError, ValueError):
            # Fallback to user score if calculation fails
            return float(user_score) if user_score else 0.0

    def get_stack_specific_patterns(self, project_name: str, stack: str) -> List[Dict]:
        """Get patterns specific to a tech stack"""
        # This would query the knowledge base for stack-specific patterns
        # Implementation would be in the KnowledgeBase class
        pass