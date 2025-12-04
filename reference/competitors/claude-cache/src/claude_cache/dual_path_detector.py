"""Dual-path learning system that captures both successes and failures"""

import json
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path


class PatternType(Enum):
    """Classification of pattern types"""
    GOLD = "gold"           # Worked first time, elegant
    SILVER = "silver"       # Worked after 2-3 attempts
    BRONZE = "bronze"       # Eventually worked
    ANTI_PATTERN = "anti"   # Confirmed failure
    JOURNEY = "journey"     # Path from problem to solution
    CAUTION = "caution"     # Works but has tradeoffs


class OutcomeType(Enum):
    """Outcome of an attempt"""
    SUCCESS = "success"
    FAILURE = "failure"
    PARTIAL = "partial"
    INSIGHT = "insight"
    ERROR = "error"


@dataclass
class Attempt:
    """Single attempt at solving a problem"""
    approach: str
    outcome: OutcomeType
    reason: str
    time_spent: str
    tool_calls: List[Dict] = field(default_factory=list)
    error_messages: List[str] = field(default_factory=list)
    files_changed: List[str] = field(default_factory=list)


@dataclass
class JourneyPattern:
    """Complete journey from problem to solution (or failure)"""
    pattern_id: str
    pattern_type: PatternType
    problem: str
    context: Dict[str, Any]
    attempts: List[Attempt]
    final_outcome: OutcomeType
    key_learning: str
    anti_patterns: List[str]
    success_factors: List[str]
    confidence: float
    project: str
    timestamp: str
    session_id: str


class DualPathDetector:
    """Detect patterns from both successful and failed attempts"""

    def __init__(self, knowledge_base=None):
        self.kb = knowledge_base
        self.current_journeys = {}  # Active problem-solving journeys
        self.completed_journeys = []  # Completed patterns

    def start_journey(self, session_id: str, problem: str, context: Dict):
        """Start tracking a new problem-solving journey"""
        self.current_journeys[session_id] = {
            'problem': problem,
            'context': context,
            'attempts': [],
            'start_time': datetime.now(),
            'insights': []
        }

    def add_attempt(self, session_id: str, attempt: Attempt):
        """Add an attempt to the current journey"""
        if session_id in self.current_journeys:
            self.current_journeys[session_id]['attempts'].append(attempt)

            # Check if this attempt provides an insight
            if attempt.outcome == OutcomeType.INSIGHT:
                self.current_journeys[session_id]['insights'].append(attempt.reason)

    def analyze_session_journey(self, session_entries: List[Dict]) -> Optional[JourneyPattern]:
        """Analyze a complete session to extract journey patterns"""
        if not session_entries:
            return None

        # Group entries into problem-solving sequences
        sequences = self._identify_sequences(session_entries)

        patterns = []
        for sequence in sequences:
            pattern = self._extract_journey_pattern(sequence)
            if pattern and self._is_pattern_valuable(pattern):
                patterns.append(pattern)

        # Return the most valuable pattern from this session
        return self._select_best_pattern(patterns) if patterns else None

    def _identify_sequences(self, entries: List[Dict]) -> List[List[Dict]]:
        """Identify problem-solving sequences in the session"""
        sequences = []
        current_sequence = []

        for entry in entries:
            # Start new sequence on user request
            if entry.get('type') == 'user' and not self._is_continuation(entry):
                if current_sequence:
                    sequences.append(current_sequence)
                current_sequence = [entry]
            else:
                current_sequence.append(entry)

        if current_sequence:
            sequences.append(current_sequence)

        return sequences

    def _is_continuation(self, entry: Dict) -> bool:
        """Check if this is a continuation of current problem"""
        content = str(entry.get('content', '')).lower()
        continuation_phrases = ['try', 'what about', 'how about', 'maybe', 'also',
                              'actually', 'wait', 'hmm', 'ok', 'still']
        return any(phrase in content for phrase in continuation_phrases)

    def _extract_journey_pattern(self, sequence: List[Dict]) -> Optional[JourneyPattern]:
        """Extract a journey pattern from a sequence"""
        if len(sequence) < 2:
            return None

        # Extract problem from first user message
        problem = self._extract_problem(sequence[0])

        # Extract attempts from the sequence
        attempts = self._extract_attempts(sequence)

        if not attempts:
            return None

        # Determine pattern type and outcome
        pattern_type, final_outcome = self._classify_pattern(attempts)

        # Extract key learnings
        key_learning = self._extract_key_learning(attempts, final_outcome)

        # Extract anti-patterns (what didn't work)
        anti_patterns = self._extract_anti_patterns(attempts)

        # Extract success factors (what did work)
        success_factors = self._extract_success_factors(attempts)

        # Calculate confidence score
        confidence = self._calculate_confidence(attempts, final_outcome)

        return JourneyPattern(
            pattern_id=self._generate_id(),
            pattern_type=pattern_type,
            problem=problem,
            context=self._extract_context(sequence),
            attempts=attempts,
            final_outcome=final_outcome,
            key_learning=key_learning,
            anti_patterns=anti_patterns,
            success_factors=success_factors,
            confidence=confidence,
            project=sequence[0].get('project', 'unknown'),
            timestamp=datetime.now().isoformat(),
            session_id=sequence[0].get('session_id', '')
        )

    def _extract_attempts(self, sequence: List[Dict]) -> List[Attempt]:
        """Extract attempts from a sequence"""
        attempts = []
        current_attempt = None

        for entry in sequence:
            if entry.get('type') == 'assistant':
                # Extract tool calls from assistant message
                tool_calls = self._extract_tool_calls(entry)
                if tool_calls:
                    approach = self._summarize_approach(tool_calls)
                    current_attempt = Attempt(
                        approach=approach,
                        outcome=OutcomeType.PARTIAL,
                        reason='',
                        time_spent='',
                        tool_calls=tool_calls
                    )

            elif entry.get('type') == 'user' and current_attempt:
                # User feedback determines outcome
                outcome, reason = self._determine_outcome(entry)
                current_attempt.outcome = outcome
                current_attempt.reason = reason
                attempts.append(current_attempt)
                current_attempt = None

        # Add last attempt if pending
        if current_attempt:
            attempts.append(current_attempt)

        return attempts

    def _extract_tool_calls(self, entry: Dict) -> List[Dict]:
        """Extract tool calls from an assistant entry"""
        tool_calls = []

        # Check if this entry has tool_calls in the expected format
        if 'tool_calls' in entry:
            tool_calls.extend(entry['tool_calls'])

        # Also check message content for tool use
        message = entry.get('message', {})
        if isinstance(message, dict):
            content = message.get('content', [])
            if isinstance(content, list):
                for item in content:
                    if isinstance(item, dict) and item.get('type') == 'tool_use':
                        tool_calls.append({
                            'tool': item.get('name'),
                            'args': item.get('input', {})
                        })

        return tool_calls

    def _determine_outcome(self, user_entry: Dict) -> Tuple[OutcomeType, str]:
        """Determine outcome based on user feedback"""
        content = str(user_entry.get('content', '')).lower()

        # Success indicators
        if any(word in content for word in ['perfect', 'works', 'thanks', 'great', 'exactly']):
            return OutcomeType.SUCCESS, 'User confirmed success'

        # Failure indicators
        if any(word in content for word in ['error', 'failed', 'broken', 'wrong', "doesn't work"]):
            return OutcomeType.FAILURE, self._extract_error_reason(content)

        # Insight indicators
        if any(word in content for word in ['ah', 'oh', 'i see', 'actually', 'wait']):
            return OutcomeType.INSIGHT, 'User gained understanding'

        # Partial success
        if any(word in content for word in ['almost', 'close', 'but', 'except']):
            return OutcomeType.PARTIAL, 'Partial success'

        return OutcomeType.PARTIAL, 'Continuing iteration'

    def _classify_pattern(self, attempts: List[Attempt]) -> Tuple[PatternType, OutcomeType]:
        """Classify the pattern based on attempts"""
        successful_attempts = [a for a in attempts if a.outcome == OutcomeType.SUCCESS]
        failed_attempts = [a for a in attempts if a.outcome == OutcomeType.FAILURE]

        if not successful_attempts and failed_attempts:
            # Pure anti-pattern
            return PatternType.ANTI_PATTERN, OutcomeType.FAILURE

        if successful_attempts:
            if len(attempts) == 1:
                # First-time success
                return PatternType.GOLD, OutcomeType.SUCCESS
            elif len(attempts) <= 3:
                # Quick success
                return PatternType.SILVER, OutcomeType.SUCCESS
            elif len(attempts) <= 5:
                # Eventually successful
                return PatternType.BRONZE, OutcomeType.SUCCESS
            else:
                # Long journey but successful
                return PatternType.JOURNEY, OutcomeType.SUCCESS

        # Has both successes and failures - journey pattern
        if successful_attempts and failed_attempts:
            return PatternType.JOURNEY, OutcomeType.SUCCESS

        # Unclear outcome
        return PatternType.CAUTION, OutcomeType.PARTIAL

    def _calculate_confidence(self, attempts: List[Attempt], outcome: OutcomeType) -> float:
        """Calculate confidence score for the pattern"""
        confidence = 0.5  # Base confidence

        # Adjust based on outcome
        if outcome == OutcomeType.SUCCESS:
            confidence += 0.3
        elif outcome == OutcomeType.FAILURE:
            confidence += 0.2  # Failures are still valuable learning

        # Adjust based on number of attempts
        if len(attempts) == 1 and outcome == OutcomeType.SUCCESS:
            confidence += 0.2  # Clean win
        elif len(attempts) > 5:
            confidence -= 0.1  # Too many attempts

        # Adjust based on insights gained
        insight_count = sum(1 for a in attempts if a.outcome == OutcomeType.INSIGHT)
        confidence += min(insight_count * 0.05, 0.15)

        return min(confidence, 1.0)

    def _is_pattern_valuable(self, pattern: JourneyPattern) -> bool:
        """Determine if a pattern is valuable enough to store"""
        # Anti-patterns are always valuable
        if pattern.pattern_type == PatternType.ANTI_PATTERN:
            return True

        # High confidence patterns are valuable
        if pattern.confidence >= 0.7:
            return True

        # Journey patterns with clear learnings are valuable
        if pattern.pattern_type == PatternType.JOURNEY and pattern.key_learning:
            return True

        # Gold patterns are always valuable
        if pattern.pattern_type == PatternType.GOLD:
            return True

        return False

    def _extract_problem(self, entry: Dict) -> str:
        """Extract the problem statement from user message"""
        content = entry.get('content', '')
        if isinstance(content, dict):
            content = content.get('content', '')
        return str(content)[:200]  # First 200 chars

    def _extract_context(self, sequence: List[Dict]) -> Dict:
        """Extract context from the sequence"""
        return {
            'project': sequence[0].get('project', 'unknown'),
            'cwd': sequence[0].get('cwd', ''),
            'timestamp': sequence[0].get('timestamp', ''),
            'session_id': sequence[0].get('session_id', '')
        }

    def _summarize_approach(self, tool_calls: List[Dict]) -> str:
        """Summarize the approach based on tool calls"""
        if not tool_calls:
            return "No specific approach"

        tools_used = [tc.get('tool', '') for tc in tool_calls]
        unique_tools = list(dict.fromkeys(tools_used))  # Preserve order, remove duplicates

        return f"Used {', '.join(unique_tools[:3])}"  # First 3 tools

    def _extract_error_reason(self, content: str) -> str:
        """Extract error reason from content"""
        # Simple extraction - could be enhanced with regex
        if 'error:' in content:
            return content.split('error:')[1][:100]
        return "Error encountered"

    def _extract_key_learning(self, attempts: List[Attempt], outcome: OutcomeType) -> str:
        """Extract the key learning from attempts"""
        if outcome == OutcomeType.SUCCESS and attempts:
            last_success = [a for a in attempts if a.outcome == OutcomeType.SUCCESS][-1]
            return f"Solution: {last_success.approach}"
        elif outcome == OutcomeType.FAILURE:
            return f"Avoid: {attempts[0].approach if attempts else 'Unknown'}"
        return "Multiple approaches needed"

    def _extract_anti_patterns(self, attempts: List[Attempt]) -> List[str]:
        """Extract what didn't work"""
        return [a.approach for a in attempts if a.outcome == OutcomeType.FAILURE]

    def _extract_success_factors(self, attempts: List[Attempt]) -> List[str]:
        """Extract what did work"""
        return [a.approach for a in attempts if a.outcome == OutcomeType.SUCCESS]

    def _select_best_pattern(self, patterns: List[JourneyPattern]) -> Optional[JourneyPattern]:
        """Select the most valuable pattern from a list"""
        if not patterns:
            return None

        # Sort by confidence and pattern type
        return max(patterns, key=lambda p: (p.confidence, p.pattern_type.value))

    def _generate_id(self) -> str:
        """Generate unique pattern ID"""
        import uuid
        return str(uuid.uuid4())

    def store_pattern(self, pattern: JourneyPattern):
        """Store a pattern in the knowledge base"""
        if self.kb:
            pattern_data = {
                'pattern_id': pattern.pattern_id,
                'type': pattern.pattern_type.value,
                'problem': pattern.problem,
                'solution': pattern.key_learning,
                'confidence': pattern.confidence,
                'project': pattern.project,
                'context': json.dumps(pattern.context),
                'attempts': json.dumps([{
                    'approach': a.approach,
                    'outcome': a.outcome.value,
                    'reason': a.reason
                } for a in pattern.attempts]),
                'anti_patterns': json.dumps(pattern.anti_patterns),
                'success_factors': json.dumps(pattern.success_factors)
            }

            # Store based on type
            if pattern.pattern_type == PatternType.ANTI_PATTERN:
                self.kb.store_anti_pattern(pattern_data)
            else:
                self.kb.store_pattern(pattern_data)