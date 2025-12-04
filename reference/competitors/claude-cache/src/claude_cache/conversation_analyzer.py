"""
Deep conversation analysis for intelligent pattern detection.
Goes beyond keywords to understand conversation dynamics, context, and outcomes.
"""

from typing import List, Dict, Tuple, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
import re
from datetime import datetime
import json


class ConversationPhase(Enum):
    """Phases of problem-solving conversation"""
    PROBLEM_STATEMENT = "problem"
    EXPLORATION = "exploration"
    IMPLEMENTATION = "implementation"
    TESTING = "testing"
    RESOLUTION = "resolution"
    CONTINUATION = "continuation"


class TaskStatus(Enum):
    """Status of the current task"""
    INITIATED = "initiated"
    IN_PROGRESS = "in_progress"
    BLOCKED = "blocked"
    TESTING = "testing"
    COMPLETED = "completed"
    ABANDONED = "abandoned"


@dataclass
class ConversationState:
    """Maintains state across the conversation"""
    current_phase: ConversationPhase = ConversationPhase.PROBLEM_STATEMENT
    task_status: TaskStatus = TaskStatus.INITIATED
    problem_description: str = ""
    attempted_solutions: List[str] = field(default_factory=list)
    errors_encountered: List[str] = field(default_factory=list)
    tests_status: Dict[str, Any] = field(default_factory=dict)
    confidence_signals: List[float] = field(default_factory=list)
    user_satisfaction_level: float = 0.5  # 0-1 scale
    ai_claimed_completion: bool = False
    user_confirmed_success: bool = False
    last_tool_results: Dict[str, Any] = field(default_factory=dict)
    topic_switches: int = 0
    momentum_score: float = 0.0  # Are we making progress?


class ConversationAnalyzer:
    """
    Sophisticated conversation analysis that understands context, flow, and outcomes.
    Not just keywords - true understanding of the coding session.
    """

    def __init__(self):
        # Conversation flow patterns
        self.flow_patterns = {
            'problem_to_solution': [
                ('problem|issue|error|bug|broken', 'fixed|solved|working|resolved'),
                ('help|how|can you', 'here|this should|try this'),
                ('not working|failing', 'now works|success|passing')
            ],
            'iterative_refinement': [
                ('try|attempt|let me', 'better|improved|closer'),
                ('almost|nearly|close', 'perfect|exactly|that\'s it'),
                ('one more|also need', 'done|complete|finished')
            ],
            'confirmation_sequence': [
                ('does this|will this|should i', 'yes|correct|exactly'),
                ('right\\?|correct\\?', 'yes|indeed|that\'s right'),
                ('is this good', 'perfect|great|excellent')
            ]
        }

        # Implicit success indicators (beyond keywords)
        self.implicit_success_patterns = {
            'task_transition': re.compile(
                r'(now|next|also|another|moving on|let\'s|can you also)',
                re.IGNORECASE
            ),
            'casual_confirmation': re.compile(
                r'(ok cool|alright|got it|i see|makes sense|ah|oh nice)',
                re.IGNORECASE
            ),
            'assumption_of_completion': re.compile(
                r'(since that\'s done|now that works|with that fixed|having completed)',
                re.IGNORECASE
            ),
            'no_followup_complaint': None  # Special case - detected by absence
        }

        # Problem persistence indicators
        self.problem_persistence_patterns = {
            'still_broken': re.compile(
                r'(still|same|again|continues|persists|not fixed)',
                re.IGNORECASE
            ),
            'frustration': re.compile(
                r'(ugh|argh|damn|frustrated|annoying|why|confused)',
                re.IGNORECASE
            ),
            'escalation': re.compile(
                r'(this is urgent|need this|critical|blocking|asap)',
                re.IGNORECASE
            )
        }

    def analyze_conversation(self, entries: List[Dict]) -> Dict[str, Any]:
        """
        Perform deep analysis of entire conversation.
        Returns comprehensive understanding of what happened.
        """
        if not entries:
            return self._empty_analysis()

        state = ConversationState()

        # Process each entry in sequence
        for i, entry in enumerate(entries):
            self._update_state(state, entry, i, entries)

        # Compute final analysis
        return self._compute_final_analysis(state, entries)

    def _update_state(self, state: ConversationState, entry: Dict,
                      index: int, all_entries: List[Dict]):
        """Update conversation state based on current entry"""

        entry_type = entry.get('type', '')
        content = str(entry.get('content', '')).lower()

        if entry_type == 'user_message':
            self._analyze_user_message(state, content, index, all_entries)
        elif entry_type == 'assistant_message':
            self._analyze_assistant_message(state, content, index, all_entries)
        elif entry_type == 'tool_call':
            self._analyze_tool_call(state, entry, index, all_entries)

        # Update momentum (are we making progress?)
        self._update_momentum(state, entry_type, content)

    def _analyze_user_message(self, state: ConversationState, content: str,
                              index: int, all_entries: List[Dict]):
        """Analyze user message for intent and satisfaction"""

        # First message is usually problem statement
        if index == 0 or not state.problem_description:
            state.problem_description = content[:200]
            state.current_phase = ConversationPhase.PROBLEM_STATEMENT
            return

        # Check if previous message was AI claiming completion
        if index > 0 and all_entries[index-1].get('type') == 'assistant_message':
            prev_content = str(all_entries[index-1].get('content', '')).lower()
            if any(word in prev_content for word in ['done', 'complete', 'fixed', 'should work']):
                state.ai_claimed_completion = True

                # Now check user's response
                if self._is_positive_response(content):
                    state.user_confirmed_success = True
                    state.user_satisfaction_level = 0.9
                elif self._is_task_transition(content):
                    # Moving on without complaint = implicit success
                    state.user_confirmed_success = True
                    state.user_satisfaction_level = 0.8
                elif self._is_negative_response(content):
                    state.user_confirmed_success = False
                    state.user_satisfaction_level = 0.2
                    state.errors_encountered.append(content[:100])

        # Check for topic switches
        if self._is_topic_switch(content, state.problem_description):
            state.topic_switches += 1

        # Update satisfaction based on sentiment
        satisfaction_delta = self._compute_satisfaction_delta(content)
        state.user_satisfaction_level = max(0, min(1,
            state.user_satisfaction_level + satisfaction_delta))

    def _analyze_assistant_message(self, state: ConversationState, content: str,
                                   index: int, all_entries: List[Dict]):
        """Analyze assistant message for solution attempts"""

        # Check if claiming completion
        if any(phrase in content for phrase in
               ['done', 'complete', 'fixed', 'should work', 'all set', 'ready']):
            state.ai_claimed_completion = True
            state.current_phase = ConversationPhase.RESOLUTION

        # Track solution attempts
        if any(phrase in content for phrase in
               ['try this', 'here\'s', 'let me', 'i\'ll']):
            state.attempted_solutions.append(content[:100])
            state.current_phase = ConversationPhase.IMPLEMENTATION

    def _analyze_tool_call(self, state: ConversationState, entry: Dict,
                           index: int, all_entries: List[Dict]):
        """Analyze tool call results for execution signals"""

        tool = entry.get('tool', '')
        output = str(entry.get('output', '')).lower()
        success = entry.get('success', True)

        # Store last results
        state.last_tool_results[tool] = {
            'output': output[:500],
            'success': success,
            'timestamp': entry.get('timestamp', '')
        }

        # Analyze test results
        if tool in ['Bash', 'ExecuteCommand']:
            if 'test' in output or 'spec' in output:
                state.current_phase = ConversationPhase.TESTING

                # Parse test results
                passed_match = re.search(r'(\d+)\s+passed', output)
                failed_match = re.search(r'(\d+)\s+failed', output)

                if passed_match or failed_match:
                    state.tests_status = {
                        'passed': int(passed_match.group(1)) if passed_match else 0,
                        'failed': int(failed_match.group(1)) if failed_match else 0,
                        'success': failed_match is None or int(failed_match.group(1)) == 0
                    }

                    if state.tests_status['success']:
                        state.confidence_signals.append(0.9)

            # Check for build/compilation success
            if 'build successful' in output or 'compiled successfully' in output:
                state.confidence_signals.append(0.8)

            # Check for errors
            if 'error' in output or 'failed' in output:
                state.errors_encountered.append(output[:200])
                state.confidence_signals.append(-0.5)

        # File edits indicate implementation
        elif tool in ['Edit', 'Write', 'MultiEdit'] and success:
            state.current_phase = ConversationPhase.IMPLEMENTATION
            state.momentum_score += 0.1

    def _is_positive_response(self, content: str) -> bool:
        """Check if user response is positive"""
        positive_indicators = [
            'thanks', 'perfect', 'great', 'excellent', 'exactly',
            'that worked', 'awesome', 'good', 'yes', 'correct',
            'right', 'works', 'fixed', 'solved'
        ]
        return any(word in content for word in positive_indicators)

    def _is_negative_response(self, content: str) -> bool:
        """Check if user response is negative"""
        negative_indicators = [
            'error', 'failed', 'broken', 'doesn\'t work', 'still not',
            'wrong', 'incorrect', 'no', 'issue', 'problem'
        ]
        return any(word in content for word in negative_indicators)

    def _is_task_transition(self, content: str) -> bool:
        """Check if user is moving to next task"""
        return bool(self.implicit_success_patterns['task_transition'].search(content))

    def _is_topic_switch(self, content: str, original_problem: str) -> bool:
        """Detect if user switched topics"""
        # Simple heuristic: very different content = topic switch
        original_words = set(original_problem.lower().split())
        current_words = set(content.lower().split())
        overlap = len(original_words & current_words) / max(len(original_words), 1)
        return overlap < 0.2 and len(content) > 20

    def _compute_satisfaction_delta(self, content: str) -> float:
        """Compute change in user satisfaction based on message"""
        delta = 0.0

        # Positive signals
        if self.implicit_success_patterns['casual_confirmation'].search(content):
            delta += 0.1
        if self.implicit_success_patterns['assumption_of_completion'].search(content):
            delta += 0.2

        # Negative signals
        if self.problem_persistence_patterns['still_broken'].search(content):
            delta -= 0.3
        if self.problem_persistence_patterns['frustration'].search(content):
            delta -= 0.2

        return delta

    def _update_momentum(self, state: ConversationState, entry_type: str, content: str):
        """Update momentum score - are we making progress?"""
        if entry_type == 'tool_call':
            # Tools indicate action
            state.momentum_score += 0.05
        elif entry_type == 'user_message':
            # Positive user messages increase momentum
            if self._is_positive_response(content):
                state.momentum_score += 0.2
            elif self._is_negative_response(content):
                state.momentum_score -= 0.3

        # Decay momentum over time
        state.momentum_score *= 0.95
        state.momentum_score = max(-1, min(1, state.momentum_score))

    def _compute_final_analysis(self, state: ConversationState,
                                entries: List[Dict]) -> Dict[str, Any]:
        """Compute final analysis from conversation state"""

        # Calculate overall success probability
        success_score = self._calculate_success_score(state)

        # Determine pattern quality
        quality = self._determine_quality(state, success_score)

        # Extract key insights
        insights = self._extract_insights(state, entries)

        return {
            'success': success_score >= 0.6,
            'success_score': success_score,
            'quality': quality,
            'user_satisfaction': state.user_satisfaction_level,
            'problem': state.problem_description,
            'solution': state.attempted_solutions[-1] if state.attempted_solutions else None,
            'errors_encountered': state.errors_encountered,
            'tests_passed': state.tests_status.get('success', False),
            'ai_claimed_completion': state.ai_claimed_completion,
            'user_confirmed': state.user_confirmed_success,
            'conversation_phase': state.current_phase.value,
            'momentum': state.momentum_score,
            'topic_switches': state.topic_switches,
            'insights': insights,
            'confidence_signals': state.confidence_signals
        }

    def _calculate_success_score(self, state: ConversationState) -> float:
        """Calculate overall success score from all signals"""
        score = 0.5  # Start neutral

        # Strongest signal: User confirmed success after AI claimed completion
        if state.ai_claimed_completion and state.user_confirmed_success:
            score = 0.9
        elif state.ai_claimed_completion and not state.user_confirmed_success:
            score = 0.2

        # Test results are strong signals
        if state.tests_status.get('success'):
            score = max(score, 0.85)
        elif state.tests_status.get('failed', 0) > 0:
            score = min(score, 0.3)

        # User satisfaction is important
        score = (score * 0.7) + (state.user_satisfaction_level * 0.3)

        # Confidence signals modify score
        if state.confidence_signals:
            avg_confidence = sum(state.confidence_signals) / len(state.confidence_signals)
            score = (score * 0.8) + (max(0, min(1, avg_confidence)) * 0.2)

        # Momentum indicates progress
        if state.momentum_score > 0.5:
            score = min(1.0, score + 0.1)
        elif state.momentum_score < -0.3:
            score = max(0.0, score - 0.1)

        return score

    def _determine_quality(self, state: ConversationState, success_score: float) -> str:
        """Determine pattern quality based on conversation analysis"""
        if success_score < 0.4:
            return 'anti'

        # High quality: Quick resolution, high satisfaction, tests pass
        if (len(state.attempted_solutions) <= 1 and
            state.user_satisfaction_level >= 0.8 and
            success_score >= 0.8):
            return 'gold'

        # Medium quality: Few attempts, decent satisfaction
        elif (len(state.attempted_solutions) <= 3 and
              state.user_satisfaction_level >= 0.6 and
              success_score >= 0.6):
            return 'silver'

        # Low quality: Many attempts but eventually worked
        else:
            return 'bronze'

    def _extract_insights(self, state: ConversationState,
                         entries: List[Dict]) -> List[str]:
        """Extract key insights from the conversation"""
        insights = []

        if state.ai_claimed_completion and state.user_confirmed_success:
            insights.append("User confirmed solution worked")

        if state.tests_status.get('success'):
            insights.append(f"Tests passed: {state.tests_status.get('passed', 0)}")

        if state.momentum_score > 0.5:
            insights.append("Steady progress throughout session")

        if state.topic_switches == 0 and len(entries) > 10:
            insights.append("Focused problem-solving session")

        if len(state.errors_encountered) > 0 and state.user_confirmed_success:
            insights.append(f"Overcame {len(state.errors_encountered)} errors")

        return insights

    def _empty_analysis(self) -> Dict[str, Any]:
        """Return empty analysis structure"""
        return {
            'success': False,
            'success_score': 0.0,
            'quality': 'unknown',
            'user_satisfaction': 0.5,
            'problem': None,
            'solution': None,
            'errors_encountered': [],
            'tests_passed': False,
            'ai_claimed_completion': False,
            'user_confirmed': False,
            'conversation_phase': 'unknown',
            'momentum': 0.0,
            'topic_switches': 0,
            'insights': [],
            'confidence_signals': []
        }