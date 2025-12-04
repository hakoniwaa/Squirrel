"""Detect successful patterns in Claude Code sessions"""

import re
from typing import List, Dict, Any, Optional
from datetime import datetime
from rich.console import Console
from .intent_detector import IntentDetector
from .execution_monitor import ExecutionMonitor

# Try to import enhanced modules with graceful fallback
try:
    from .semantic_matcher import SemanticMatcher
    HAS_SEMANTIC_MATCHER = True
except ImportError:
    HAS_SEMANTIC_MATCHER = False
    SemanticMatcher = None

try:
    from .meta_pattern_scorer import MetaPatternScorer
    HAS_META_SCORER = True
except ImportError:
    HAS_META_SCORER = False
    MetaPatternScorer = None

console = Console()


class SuccessDetector:
    """Analyze sessions to identify successful patterns"""

    def __init__(self):
        # Simplified: Focus on top 20 most reliable indicators
        self.success_indicators = {
            'test_keywords': ['passed', 'success', '✓', 'ok'],
            'failure_keywords': ['failed', 'error', 'broken', 'exception'],
            'completion_keywords': ['done', 'completed', 'finished', 'works', 'fixed'],
            'user_satisfaction': ['thanks', 'perfect', 'great', 'that worked', 'exactly'],
            'implicit_success': ['now let', 'next', 'also', 'moving on'],
            'workflow_progression': ['continue', 'proceed', 'go ahead'],
            'domain_specific_success': {
                'frontend': ['renders', 'ui works', 'component works'],
                'backend': ['api works', 'endpoint works', 'server running'],
                'database': ['query works', 'migration successful'],
                'devops': ['deployed', 'build passing'],
                'testing': ['tests pass', 'coverage']
            }
        }

        # Initialize semantic intent detector
        self.intent_detector = IntentDetector()

        # Initialize execution monitor
        self.execution_monitor = ExecutionMonitor()

        # Initialize semantic matcher (with fallback)
        if HAS_SEMANTIC_MATCHER:
            self.semantic_matcher = SemanticMatcher()
        else:
            self.semantic_matcher = None

        # Initialize meta-pattern scorer (with fallback)
        if HAS_META_SCORER:
            self.meta_scorer = MetaPatternScorer()
        else:
            self.meta_scorer = None

    def analyze_session_success(self, session_entries: List[Dict]) -> Dict:
        """Determine if a session was successful and extract patterns"""
        if not session_entries:
            return {'success': False, 'score': 0, 'pattern': None}

        # Analyze execution signals
        execution_success = self.analyze_execution_signals(session_entries)

        indicators = {
            'tests_passed': self.check_test_success(session_entries),
            'no_errors': self.check_for_errors(session_entries),
            'files_modified': self.count_successful_edits(session_entries),
            'user_satisfied': self.detect_user_satisfaction(session_entries),
            'task_completed': self.check_task_completion(session_entries),
            'execution_success': execution_success,
            'completion_flow': self.detect_task_completion_flow(session_entries)
        }

        score = self.calculate_success_score(indicators)

        # Enhanced analysis using meta-pattern scoring (if available)
        if self.meta_scorer:
            session_context = self._extract_session_context(session_entries)
            meta_analysis = self.meta_scorer.evaluate_session_patterns(session_entries, session_context)

            # Integrate traditional scoring with meta-pattern analysis
            combined_score = (score * 0.6) + (meta_analysis.get('meta_score', 0.0) * 0.4)

            # Determine success based on either traditional or meta-pattern thresholds
            is_successful = (
                score > 0.3 or  # Traditional threshold
                meta_analysis.get('meta_score', 0.0) > 0.4 or  # Meta-pattern threshold
                meta_analysis.get('confidence', 'low') == 'high'  # High confidence override
            )
        else:
            # Fallback to traditional scoring only
            meta_analysis = {'meta_score': 0.0, 'confidence': 'low', 'pattern_types_detected': []}
            combined_score = score
            is_successful = score > 0.3

        if is_successful:
            pattern = self.extract_success_pattern(session_entries)

            # Enhance pattern with meta-analysis insights
            if pattern and meta_analysis:
                pattern['meta_analysis'] = meta_analysis
                pattern['combined_score'] = combined_score
                pattern['pattern_types_detected'] = meta_analysis.get('pattern_types_detected', [])
                pattern['quality_indicators'] = meta_analysis.get('quality_indicators', {})
                pattern['recommendations'] = meta_analysis.get('recommendations', [])

            return {
                'success': True,
                'score': combined_score,
                'pattern': pattern,
                'indicators': indicators,
                'meta_analysis': meta_analysis,
                'confidence': meta_analysis.get('confidence', 'medium')
            }

        return {
            'success': False,
            'score': combined_score,
            'pattern': None,
            'indicators': indicators,
            'meta_analysis': meta_analysis
        }

    def check_test_success(self, entries: List[Dict]) -> bool:
        """Check if tests passed in the session using execution monitoring"""
        # Check execution signals from bash commands
        for entry in entries:
            if entry.get('type') == 'tool_call' and entry.get('tool') == 'Bash':
                command = entry.get('args', {}).get('command', '')
                output = entry.get('output', '')

                if output:
                    signals = self.execution_monitor.analyze_output(output, command)
                    for signal in signals:
                        if signal.signal_type == 'test_pass' and signal.confidence > 0.7:
                            return True

        # Fallback to keyword detection
        for entry in entries:
            content = str(entry.get('content', '')).lower()

            if any(keyword in content for keyword in self.success_indicators['test_keywords']):
                if 'test' in content or 'spec' in content:
                    return True

        return False

    def check_for_errors(self, entries: List[Dict]) -> bool:
        """Check if there were no errors in the session"""
        error_count = 0
        success_count = 0

        for entry in entries:
            content = str(entry.get('content', '')).lower()

            for keyword in self.success_indicators['failure_keywords']:
                if keyword in content:
                    error_count += 1

            for keyword in self.success_indicators['test_keywords']:
                if keyword in content:
                    success_count += 1

        return success_count > error_count

    def count_successful_edits(self, entries: List[Dict]) -> int:
        """Count number of successful file modifications"""
        successful_edits = 0

        for entry in entries:
            if entry.get('type') == 'tool_call':
                tool = entry.get('tool', '')
                success = entry.get('success', True)

                if tool in ['Edit', 'Write', 'MultiEdit'] and success:
                    successful_edits += 1

        return successful_edits

    def detect_user_satisfaction(self, entries: List[Dict]) -> bool:
        """Detect if the user was satisfied with the result using semantic analysis"""
        # Analyze the conversation flow for semantic intent
        conversation = []
        for entry in entries:
            if entry.get('type') in ['user_message', 'assistant_message']:
                conversation.append({
                    'role': 'user' if entry.get('type') == 'user_message' else 'assistant',
                    'content': entry.get('content', '')
                })

        # Use semantic analysis - both intent detection and semantic matching
        if conversation:
            # Original intent analysis
            analysis = self.intent_detector.analyze_conversation_flow(conversation)
            if analysis.get('overall_intent') == 'positive' and analysis.get('confidence', 0) > 0.6:
                return True

            # Enhanced semantic analysis (if available)
            if self.semantic_matcher:
                semantic_analysis = self.semantic_matcher.analyze_conversation_success_signals(conversation)
                if semantic_analysis.get('success_probability', 0) > 0.5:
                    return True

        # Enhanced keyword matching with multiple signal types
        satisfaction_score = 0

        for entry in reversed(entries):
            if entry.get('type') == 'user_message':
                content = str(entry.get('content', '')).lower()

                # Direct satisfaction indicators
                for keyword in self.success_indicators['user_satisfaction']:
                    if keyword in content:
                        satisfaction_score += 0.3

                # Implicit success indicators (user moving on)
                for keyword in self.success_indicators['implicit_success']:
                    if keyword in content:
                        satisfaction_score += 0.2

                # Workflow progression indicators
                for keyword in self.success_indicators['workflow_progression']:
                    if keyword in content:
                        satisfaction_score += 0.2

                # Domain-specific success detection
                for domain, keywords in self.success_indicators['domain_specific_success'].items():
                    for keyword in keywords:
                        if keyword in content:
                            satisfaction_score += 0.25

                # Check for technical stack clues to weight domain signals
                context = self._detect_session_context(entries)
                if context and any(domain in context for domain in ['frontend', 'backend', 'database', 'devops', 'testing']):
                    # Boost score if we have domain context
                    satisfaction_score *= 1.1

        return satisfaction_score >= 0.3

    def detect_task_completion_flow(self, entries: List[Dict]) -> float:
        """Detect natural task completion flow patterns"""
        score = 0.0

        # Look for AI completion confirmation followed by user moving on
        for i, entry in enumerate(entries[:-1]):
            if entry.get('type') == 'assistant_message':
                content = str(entry.get('content', '')).lower()

                # AI completion indicators
                ai_completion_phrases = [
                    'completed', 'finished', 'done', 'should be working',
                    'should now work', 'is now set up', 'is ready',
                    'has been updated', 'has been created', 'has been fixed',
                    'all set', 'you can now', 'try running', 'should work now',
                    'successfully', 'implementation is complete'
                ]

                if any(phrase in content for phrase in ai_completion_phrases):
                    # Check if user moves to next task or confirms
                    next_entry = entries[i + 1] if i + 1 < len(entries) else None
                    if next_entry and next_entry.get('type') == 'user_message':
                        next_content = str(next_entry.get('content', '')).lower()

                        # User moves to new task without complaints
                        new_task_indicators = [
                            'now let', 'next', 'also', 'can you', 'please',
                            'let\'s', 'okay', 'great', 'perfect', 'thanks'
                        ]

                        # User doesn't counter with problems
                        problem_indicators = [
                            'error', 'doesn\'t work', 'not working', 'issue',
                            'problem', 'broken', 'failed', 'wrong'
                        ]

                        if (any(phrase in next_content for phrase in new_task_indicators) and
                            not any(phrase in next_content for phrase in problem_indicators)):
                            score += 0.5

                        # Direct confirmation
                        if any(phrase in next_content for phrase in ['perfect', 'great', 'thanks', 'that worked']):
                            score += 0.3

        return min(score, 1.0)

    def check_task_completion(self, entries: List[Dict]) -> bool:
        """Check if the task was marked as completed"""
        for entry in entries:
            content = str(entry.get('content', '')).lower()

            for keyword in self.success_indicators['completion_keywords']:
                if keyword in content:
                    return True

        return False

    def calculate_success_score(self, indicators: Dict[str, Any]) -> float:
        """Calculate overall success score"""
        weights = {
            'tests_passed': 0.2,
            'no_errors': 0.15,
            'files_modified': 0.1,
            'user_satisfied': 0.15,
            'task_completed': 0.1,
            'execution_success': 0.1,
            'completion_flow': 0.2  # High weight for natural conversation flow
        }

        score = 0
        for key, value in indicators.items():
            if key in weights:
                if isinstance(value, bool):
                    score += weights[key] if value else 0
                elif isinstance(value, int):
                    score += weights[key] * min(value / 5, 1)
                elif isinstance(value, float):
                    score += weights[key] * value

        return score

    def extract_success_pattern(self, entries: List[Dict]) -> Dict:
        """Extract the successful pattern from a session"""
        pattern = {
            'user_request': self.get_initial_request(entries),
            'approach': self.extract_approach(entries),
            'files_involved': self.get_files_touched(entries),
            'solution_steps': self.extract_solution_steps(entries),
            'key_operations': self.extract_key_operations(entries),
            'timestamp': datetime.now().isoformat()
        }

        return pattern

    def get_initial_request(self, entries: List[Dict]) -> str:
        """Get the initial user request from the session"""
        for entry in entries:
            if entry.get('type') == 'user_message':
                return entry.get('content', '')

        return ''

    def extract_approach(self, entries: List[Dict]) -> str:
        """Extract the general approach taken"""
        tool_sequence = []

        for entry in entries:
            if entry.get('type') == 'tool_call':
                tool = entry.get('tool', '')
                if tool:
                    tool_sequence.append(tool)

        approach_patterns = {
            'exploration_first': ['Grep', 'Read', 'Read'],
            'direct_edit': ['Edit', 'Edit'],
            'test_driven': ['Read', 'Edit', 'Bash'],
            'research_based': ['WebSearch', 'Read', 'Edit']
        }

        for approach, pattern in approach_patterns.items():
            if self._matches_pattern(tool_sequence, pattern):
                return approach

        return 'mixed_approach'

    def _matches_pattern(self, sequence: List[str], pattern: List[str]) -> bool:
        """Check if a tool sequence matches a pattern"""
        if len(sequence) < len(pattern):
            return False

        for i in range(len(sequence) - len(pattern) + 1):
            if sequence[i:i + len(pattern)] == pattern:
                return True

        return False

    def get_files_touched(self, entries: List[Dict]) -> List[str]:
        """Get list of files that were touched in the session"""
        files = set()

        for entry in entries:
            if entry.get('type') == 'tool_call':
                args = entry.get('args', {})

                if 'file_path' in args:
                    files.add(args['file_path'])
                elif 'path' in args:
                    files.add(args['path'])

        return list(files)

    def extract_solution_steps(self, entries: List[Dict]) -> List[Dict]:
        """Extract the key solution steps"""
        steps = []
        step_number = 1

        for entry in entries:
            if entry.get('type') == 'assistant_message':
                content = entry.get('content', '')

                if self._is_significant_step(content):
                    steps.append({
                        'number': step_number,
                        'action': self._summarize_step(content),
                        'timestamp': entry.get('timestamp')
                    })
                    step_number += 1

        return steps

    def _is_significant_step(self, content: str) -> bool:
        """Determine if a message represents a significant step"""
        significant_indicators = [
            'implementing', 'creating', 'adding', 'fixing',
            'updating', 'modifying', 'refactoring', 'testing'
        ]

        content_lower = content.lower()
        return any(indicator in content_lower for indicator in significant_indicators)

    def _summarize_step(self, content: str) -> str:
        """Create a brief summary of a step"""
        lines = content.split('\n')
        first_line = lines[0] if lines else content

        if len(first_line) > 100:
            return first_line[:97] + '...'

        return first_line

    def _detect_session_context(self, entries: List[Dict]) -> List[str]:
        """Detect the technical context/domain of the session"""
        context = set()

        for entry in entries:
            content = str(entry.get('content', '')).lower()

            # Check for frontend indicators
            if any(term in content for term in ['react', 'component', 'jsx', 'vue', 'angular', 'css', 'html', 'dom']):
                context.add('frontend')

            # Check for backend indicators
            if any(term in content for term in ['api', 'endpoint', 'server', 'express', 'django', 'flask', 'node']):
                context.add('backend')

            # Check for database indicators
            if any(term in content for term in ['database', 'sql', 'query', 'postgres', 'mysql', 'mongodb']):
                context.add('database')

            # Check for devops indicators
            if any(term in content for term in ['deploy', 'docker', 'ci', 'build', 'pipeline', 'aws', 'cloud']):
                context.add('devops')

            # Check for testing indicators
            if any(term in content for term in ['test', 'jest', 'pytest', 'spec', 'unit test', 'integration']):
                context.add('testing')

            # Check file extensions in tool calls
            if entry.get('type') == 'tool_call':
                args = entry.get('args', {})
                file_path = args.get('file_path', '') or args.get('path', '')
                if file_path:
                    if any(ext in file_path for ext in ['.js', '.jsx', '.ts', '.tsx', '.vue', '.html', '.css']):
                        context.add('frontend')
                    if any(ext in file_path for ext in ['.py', '.java', '.rb', '.go', '.php']):
                        context.add('backend')
                    if any(ext in file_path for ext in ['.sql', '.db']):
                        context.add('database')

        return list(context)

    def _extract_session_context(self, entries: List[Dict]) -> Dict:
        """Extract comprehensive session context for meta-pattern analysis"""
        context = {
            'project_name': 'unknown',
            'tech_domains': self._detect_session_context(entries),
            'tools_used': set(),
            'file_types': set(),
            'session_length': len(entries),
            'complexity_indicators': {},
            'timestamp': datetime.now().isoformat()
        }

        # Extract tools and file types
        for entry in entries:
            if entry.get('type') == 'tool_call':
                tool = entry.get('tool', '')
                if tool:
                    context['tools_used'].add(tool)

                args = entry.get('args', {})
                file_path = args.get('file_path', '') or args.get('path', '')
                if file_path and '.' in file_path:
                    ext = file_path.split('.')[-1]
                    context['file_types'].add(ext)

            # Extract project name if available
            if 'project' in entry:
                context['project_name'] = entry.get('project', 'unknown')

        # Convert sets to lists for JSON serialization
        context['tools_used'] = list(context['tools_used'])
        context['file_types'] = list(context['file_types'])

        # Calculate complexity indicators
        context['complexity_indicators'] = {
            'tool_diversity': len(context['tools_used']),
            'file_type_diversity': len(context['file_types']),
            'domain_diversity': len(context['tech_domains']),
            'session_complexity': 'low' if len(entries) < 10 else 'medium' if len(entries) < 30 else 'high'
        }

        return context

    def extract_key_operations(self, entries: List[Dict]) -> List[Dict]:
        """Extract key operations performed"""
        operations = []

        for entry in entries:
            if entry.get('type') == 'tool_call':
                tool = entry.get('tool', '')
                args = entry.get('args', {})

                operation = {
                    'tool': tool,
                    'success': entry.get('success', True)
                }

                if tool in ['Edit', 'Write']:
                    operation['file'] = args.get('file_path', '')
                elif tool == 'Bash':
                    operation['command'] = args.get('command', '')[:50]

                operations.append(operation)

        return operations

    def analyze_execution_signals(self, entries: List[Dict]) -> float:
        """Analyze execution signals from command outputs"""
        all_signals = []

        for entry in entries:
            if entry.get('type') == 'tool_call' and entry.get('tool') == 'Bash':
                command = entry.get('args', {}).get('command', '')
                output = entry.get('output', '')

                if output:
                    signals = self.execution_monitor.analyze_output(output, command)
                    all_signals.extend(signals)

        if not all_signals:
            return 0.0

        # Calculate overall success from signals
        success, confidence = self.execution_monitor.calculate_overall_success(all_signals)
        return confidence if success else 0.0

    def analyze_error_resolution_journey(self, entries: List[Dict]) -> Dict:
        """Analyze error→success resolution patterns with enhanced tracking"""
        resolution_analysis = {
            'error_phases': [],
            'resolution_strategies': [],
            'debugging_patterns': [],
            'success_breakthrough': None,
            'total_resolution_time': 0,
            'resolution_quality': 'unknown',
            'learning_moments': [],
            'preventable_errors': []
        }

        error_phases = []
        current_phase = None

        for i, entry in enumerate(entries):
            content = str(entry.get('content', '')).lower()

            # Detect error states
            error_indicators = [
                'error', 'exception', 'failed', 'crash', 'broken',
                'not working', 'issue', 'problem', 'bug', 'traceback'
            ]

            # Detect resolution attempts
            resolution_indicators = [
                'try', 'let me', 'maybe', 'what if', 'how about',
                'alternative', 'instead', 'another approach'
            ]

            # Detect success signals
            success_indicators = [
                'works', 'working', 'fixed', 'resolved', 'solved',
                'success', 'perfect', 'great', 'that did it'
            ]

            # Detect debugging patterns
            debugging_indicators = [
                'debug', 'check', 'verify', 'test', 'print',
                'log', 'inspect', 'examine', 'investigate'
            ]

            # Track error phases
            if any(indicator in content for indicator in error_indicators):
                if not current_phase or current_phase['type'] != 'error':
                    # Start new error phase
                    current_phase = {
                        'type': 'error',
                        'start_index': i,
                        'errors': [],
                        'attempted_solutions': [],
                        'debugging_actions': []
                    }
                    error_phases.append(current_phase)

                # Extract specific error details
                current_phase['errors'].append({
                    'content': content[:200],
                    'timestamp': entry.get('timestamp', ''),
                    'context': self._extract_error_context(entry)
                })

            # Track resolution attempts
            elif any(indicator in content for indicator in resolution_indicators):
                if current_phase and current_phase['type'] == 'error':
                    current_phase['attempted_solutions'].append({
                        'approach': content[:150],
                        'timestamp': entry.get('timestamp', ''),
                        'tools_used': self._extract_tools_from_entry(entry)
                    })

            # Track debugging actions
            elif any(indicator in content for indicator in debugging_indicators):
                if current_phase and current_phase['type'] == 'error':
                    current_phase['debugging_actions'].append({
                        'action': content[:100],
                        'timestamp': entry.get('timestamp', ''),
                        'type': self._classify_debugging_action(content)
                    })

            # Track success resolution
            elif any(indicator in content for indicator in success_indicators):
                if current_phase and current_phase['type'] == 'error':
                    # Mark resolution
                    current_phase['end_index'] = i
                    current_phase['resolution'] = {
                        'success_signal': content[:100],
                        'timestamp': entry.get('timestamp', ''),
                        'final_approach': current_phase['attempted_solutions'][-1] if current_phase['attempted_solutions'] else None
                    }
                    current_phase = None  # End current error phase

        # Analyze completed error phases
        for phase in error_phases:
            if 'resolution' in phase:
                resolution_analysis['error_phases'].append(phase)

                # Extract resolution strategies
                strategies = self._extract_resolution_strategies(phase)
                resolution_analysis['resolution_strategies'].extend(strategies)

                # Extract debugging patterns
                debugging_patterns = self._extract_debugging_patterns(phase)
                resolution_analysis['debugging_patterns'].extend(debugging_patterns)

                # Identify learning moments
                learning = self._identify_learning_moments(phase)
                if learning:
                    resolution_analysis['learning_moments'].append(learning)

        # Analyze overall resolution quality
        resolution_analysis['resolution_quality'] = self._assess_resolution_quality(resolution_analysis)

        # Identify success breakthrough moment
        if resolution_analysis['error_phases']:
            last_resolution = resolution_analysis['error_phases'][-1].get('resolution')
            if last_resolution:
                resolution_analysis['success_breakthrough'] = {
                    'final_approach': last_resolution.get('final_approach'),
                    'key_insight': self._extract_key_insight(last_resolution),
                    'breakthrough_type': self._classify_breakthrough(last_resolution)
                }

        return resolution_analysis

    def _extract_error_context(self, entry: Dict) -> Dict:
        """Extract context around an error"""
        return {
            'tool': entry.get('tool', ''),
            'file_involved': entry.get('args', {}).get('file_path', ''),
            'command': entry.get('args', {}).get('command', ''),
            'entry_type': entry.get('type', '')
        }

    def _extract_tools_from_entry(self, entry: Dict) -> List[str]:
        """Extract tools mentioned or used in an entry"""
        tools = []
        if entry.get('tool'):
            tools.append(entry.get('tool'))

        content = str(entry.get('content', '')).lower()
        tool_keywords = ['bash', 'edit', 'read', 'write', 'grep', 'search']
        for tool in tool_keywords:
            if tool in content:
                tools.append(tool)

        return list(set(tools))

    def _classify_debugging_action(self, content: str) -> str:
        """Classify the type of debugging action"""
        if any(word in content for word in ['print', 'log', 'console']):
            return 'logging'
        elif any(word in content for word in ['test', 'verify', 'check']):
            return 'verification'
        elif any(word in content for word in ['inspect', 'examine', 'look']):
            return 'inspection'
        elif any(word in content for word in ['trace', 'step', 'debug']):
            return 'tracing'
        else:
            return 'general'

    def _extract_resolution_strategies(self, phase: Dict) -> List[Dict]:
        """Extract resolution strategies from an error phase"""
        strategies = []

        for solution in phase.get('attempted_solutions', []):
            approach = solution.get('approach', '').lower()

            strategy_type = 'unknown'
            if 'alternative' in approach or 'different' in approach:
                strategy_type = 'alternative_approach'
            elif 'simple' in approach or 'basic' in approach:
                strategy_type = 'simplification'
            elif 'check' in approach or 'verify' in approach:
                strategy_type = 'verification'
            elif 'restart' in approach or 'reset' in approach:
                strategy_type = 'reset'

            strategies.append({
                'type': strategy_type,
                'description': approach[:100],
                'tools_used': solution.get('tools_used', [])
            })

        return strategies

    def _extract_debugging_patterns(self, phase: Dict) -> List[Dict]:
        """Extract debugging patterns from an error phase"""
        patterns = []

        debugging_actions = phase.get('debugging_actions', [])
        if debugging_actions:
            # Group by type
            by_type = {}
            for action in debugging_actions:
                action_type = action.get('type', 'general')
                if action_type not in by_type:
                    by_type[action_type] = []
                by_type[action_type].append(action)

            # Create patterns
            for action_type, actions in by_type.items():
                patterns.append({
                    'pattern_type': action_type,
                    'frequency': len(actions),
                    'sequence': [a.get('action', '')[:50] for a in actions[:3]]
                })

        return patterns

    def _identify_learning_moments(self, phase: Dict) -> Optional[Dict]:
        """Identify key learning moments in error resolution"""
        resolution = phase.get('resolution')
        if not resolution:
            return None

        errors = phase.get('errors', [])
        attempted_solutions = phase.get('attempted_solutions', [])

        if len(attempted_solutions) > 1:
            return {
                'type': 'iterative_learning',
                'description': f'Learned through {len(attempted_solutions)} attempts',
                'key_insight': 'Multiple approaches led to understanding',
                'final_solution': resolution.get('final_approach', {}).get('approach', '')[:100]
            }

        return None

    def _assess_resolution_quality(self, analysis: Dict) -> str:
        """Assess the overall quality of error resolution"""
        error_phases = analysis.get('error_phases', [])

        if not error_phases:
            return 'no_errors'

        avg_attempts = sum(len(phase.get('attempted_solutions', [])) for phase in error_phases) / len(error_phases)

        if avg_attempts <= 2:
            return 'efficient'
        elif avg_attempts <= 4:
            return 'moderate'
        else:
            return 'complex'

    def _extract_key_insight(self, resolution: Dict) -> str:
        """Extract the key insight that led to resolution"""
        final_approach = resolution.get('final_approach', {})
        approach_text = final_approach.get('approach', '') if final_approach else ''

        # Simple extraction of key insight
        insight_indicators = ['because', 'the issue was', 'turned out', 'realized', 'found that']
        for indicator in insight_indicators:
            if indicator in approach_text.lower():
                return approach_text.lower().split(indicator)[1][:100].strip()

        return approach_text[:100] if approach_text else 'Resolution approach unclear'

    def _classify_breakthrough(self, resolution: Dict) -> str:
        """Classify the type of breakthrough that led to success"""
        success_signal = resolution.get('success_signal', '').lower()

        if 'perfect' in success_signal or 'exactly' in success_signal:
            return 'perfect_solution'
        elif 'works' in success_signal or 'working' in success_signal:
            return 'functional_solution'
        elif 'fixed' in success_signal or 'resolved' in success_signal:
            return 'problem_fixed'
        else:
            return 'general_success'