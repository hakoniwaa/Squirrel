"""Behavioral success detection - focuses on user actions over keywords"""

from typing import List, Dict, Any, Tuple, Optional
from enum import Enum
import re


class SignalStrength(Enum):
    """Simple 3-tier signal strength"""
    STRONG = "strong"    # Clear success indicators
    MEDIUM = "medium"    # Probable success
    WEAK = "weak"        # Possible success


class PatternQuality(Enum):
    """Pattern quality classification"""
    GOLD = "gold"        # Worked immediately, elegant solution
    SILVER = "silver"    # Worked after 2-3 attempts
    BRONZE = "bronze"    # Eventually worked after multiple attempts
    ANTI = "anti"        # Confirmed doesn't work


class BehavioralDetector:
    """
    Simplified success detection focusing on user behavior patterns.
    Philosophy: Actions speak louder than keywords.
    """

    def __init__(self):
        # Only keep the most reliable keywords (top 20)
        self.core_keywords = {
            'strong_success': ['perfect', 'thanks', 'that worked', 'exactly'],
            'test_success': ['passed', '✓', 'success', 'ok'],
            'clear_failure': ['error', 'failed', 'broken', 'doesn\'t work']
        }

        # Behavioral patterns that indicate success
        self.behavioral_patterns = {
            'user_moves_on': re.compile(r'(now|next|also|another|can you|please|let\'s)', re.IGNORECASE),
            'ai_confirms_complete': re.compile(r'(completed|finished|done|should work|all set|ready)', re.IGNORECASE),
            'test_output': re.compile(r'(\d+)\s+passed|all tests pass|✓.*test', re.IGNORECASE),
            'build_success': re.compile(r'build successful|compiled successfully|server running', re.IGNORECASE)
        }

    def detect_success(self, session_entries: List[Dict]) -> Tuple[bool, SignalStrength, PatternQuality]:
        """
        Detect success based on behavioral patterns.
        Returns: (is_success, signal_strength, pattern_quality)
        """
        if not session_entries:
            return False, SignalStrength.WEAK, PatternQuality.BRONZE

        # Primary signal: User behavior after AI response
        behavior_signal = self._analyze_conversation_flow(session_entries)

        # Secondary signal: Test/build outputs
        execution_signal = self._analyze_execution_results(session_entries)

        # Tertiary signal: Keywords (but weighted less)
        keyword_signal = self._analyze_keywords(session_entries)

        # Combine signals - if any strong signal exists, consider success
        # Execution is most reliable, then behavior, then keywords
        if execution_signal >= 0.8:
            success_score = execution_signal  # Trust test results
        elif behavior_signal >= 0.6:
            success_score = behavior_signal   # Trust behavioral patterns
        else:
            # Weighted combination for weak signals
            success_score = (
                behavior_signal * 0.5 +
                execution_signal * 0.3 +
                keyword_signal * 0.2
            )

        # Determine pattern quality based on attempt count
        attempt_count = self._count_attempts(session_entries)
        quality = self._determine_quality(attempt_count, success_score)

        # Determine signal strength
        if success_score >= 0.7:
            strength = SignalStrength.STRONG
        elif success_score >= 0.4:
            strength = SignalStrength.MEDIUM
        else:
            strength = SignalStrength.WEAK

        return success_score >= 0.4, strength, quality

    def _analyze_conversation_flow(self, entries: List[Dict]) -> float:
        """
        Analyze the conversation flow for behavioral success signals.
        Key insight: If AI says it's done and user moves to next task = success
        """
        score = 0.0

        for i in range(len(entries) - 1):
            current = entries[i]
            next_entry = entries[i + 1]

            # Pattern: AI confirms completion → User moves on
            if current.get('type') == 'assistant_message' and next_entry.get('type') == 'user_message':
                ai_content = str(current.get('content', '')).lower()
                user_content = str(next_entry.get('content', '')).lower()

                # Check if AI indicated completion
                if self.behavioral_patterns['ai_confirms_complete'].search(ai_content):
                    # Check if user moved on without complaint
                    if self.behavioral_patterns['user_moves_on'].search(user_content):
                        # No error keywords in user response = strong success signal
                        if not any(word in user_content for word in self.core_keywords['clear_failure']):
                            score += 0.8
                        else:
                            score -= 0.3

                    # User explicitly confirms success
                    elif any(word in user_content for word in self.core_keywords['strong_success']):
                        score += 1.0

        return min(score, 1.0)

    def _analyze_execution_results(self, entries: List[Dict]) -> float:
        """
        Analyze concrete execution results (test outputs, build results).
        This is the most reliable signal when available.
        """
        score = 0.0

        for entry in entries:
            if entry.get('type') == 'tool_call':
                tool = entry.get('tool', '')
                output = str(entry.get('output', '')).lower()

                # Check for test success patterns
                if tool in ['Bash', 'ExecuteCommand', 'Shell']:
                    if self.behavioral_patterns['test_output'].search(output):
                        score = max(score, 0.9)  # Strong success signal
                    elif self.behavioral_patterns['build_success'].search(output):
                        score = max(score, 0.8)
                    elif 'error' in output or 'failed' in output:
                        score -= 0.5

        return max(0, min(score, 1.0))

    def _analyze_keywords(self, entries: List[Dict]) -> float:
        """
        Simple keyword analysis as a tertiary signal.
        Only uses the most reliable keywords.
        """
        score = 0.0

        # Look at last few user messages (most recent = most relevant)
        user_messages = [e for e in entries if e.get('type') == 'user_message'][-3:]

        for message in user_messages:
            content = str(message.get('content', '')).lower()

            # Strong positive signals
            if any(word in content for word in self.core_keywords['strong_success']):
                score = max(score, 0.8)  # Strong signal

            # Test success signals
            elif any(word in content for word in self.core_keywords['test_success']):
                score = max(score, 0.6)

            # Clear failure signals
            if any(word in content for word in self.core_keywords['clear_failure']):
                score -= 0.5

        return max(0, min(score, 1.0))

    def _count_attempts(self, entries: List[Dict]) -> int:
        """Count how many attempts were made to solve the problem"""
        # Count error→fix cycles
        error_count = 0
        for entry in entries:
            content = str(entry.get('content', '')).lower()
            if any(word in content for word in ['error', 'failed', 'fix', 'retry']):
                error_count += 1

        return max(1, error_count // 2)  # Roughly 2 mentions = 1 attempt

    def _determine_quality(self, attempts: int, success_score: float) -> PatternQuality:
        """Determine pattern quality based on attempts and success"""
        if success_score < 0.4:
            return PatternQuality.ANTI
        elif attempts == 1 and success_score >= 0.7:
            return PatternQuality.GOLD
        elif attempts <= 3 and success_score >= 0.5:
            return PatternQuality.SILVER
        else:
            return PatternQuality.BRONZE

    def extract_learning(self, entries: List[Dict], quality: PatternQuality) -> Dict[str, Any]:
        """Extract the key learning from a session based on quality"""
        learning = {
            'quality': quality.value,
            'problem': self._extract_problem(entries),
            'solution': self._extract_solution(entries),
            'key_insight': None,
            'avoid': []
        }

        # For anti-patterns, focus on what to avoid
        if quality == PatternQuality.ANTI:
            learning['avoid'] = self._extract_failures(entries)
            learning['key_insight'] = "This approach doesn't work"

        # For gold patterns, extract the elegant solution
        elif quality == PatternQuality.GOLD:
            learning['key_insight'] = "Clean solution that works immediately"

        # For silver/bronze, extract the journey
        else:
            learning['key_insight'] = self._extract_breakthrough_moment(entries)

        return learning

    def _extract_problem(self, entries: List[Dict]) -> str:
        """Extract the initial problem from session"""
        for entry in entries[:5]:  # Look at first 5 entries
            if entry.get('type') == 'user_message':
                return entry.get('content', '')[:200]  # First 200 chars
        return "Unknown problem"

    def _extract_solution(self, entries: List[Dict]) -> str:
        """Extract the solution that worked"""
        # Look for the last significant code change or command
        for entry in reversed(entries):
            if entry.get('type') == 'tool_call':
                tool = entry.get('tool', '')
                if tool in ['Edit', 'Write', 'MultiEdit']:
                    return f"{tool}: {entry.get('args', {}).get('file_path', 'unknown')}"
        return "Solution not clearly identified"

    def _extract_failures(self, entries: List[Dict]) -> List[str]:
        """Extract what didn't work"""
        failures = []
        for entry in entries:
            content = str(entry.get('content', '')).lower()
            if 'error' in content or 'failed' in content:
                # Extract the specific failure
                failures.append(content[:100])
        return failures[:3]  # Top 3 failures

    def _extract_breakthrough_moment(self, entries: List[Dict]) -> str:
        """Find the moment when the solution clicked"""
        for i in range(len(entries) - 1):
            current = entries[i]
            next_entry = entries[i + 1]

            # Look for error→success transition
            if 'error' in str(current.get('content', '')).lower():
                if any(word in str(next_entry.get('content', '')).lower()
                       for word in ['works', 'fixed', 'success']):
                    return f"Key: {next_entry.get('content', '')[:100]}"

        return "Gradual problem solving"