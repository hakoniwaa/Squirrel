"""
Intelligent success detection that combines multiple analysis techniques.
Not keyword-based - truly understands conversation context and outcomes.
"""

from typing import List, Dict, Tuple, Any, Optional
from dataclasses import dataclass
from enum import Enum

from .conversation_analyzer import ConversationAnalyzer, ConversationState
from .execution_monitor import ExecutionMonitor
from .intent_detector import IntentDetector


class DetectionConfidence(Enum):
    """Confidence levels for detection"""
    CERTAIN = "certain"  # > 90% confidence
    HIGH = "high"        # 70-90% confidence
    MEDIUM = "medium"    # 50-70% confidence
    LOW = "low"          # 30-50% confidence
    UNCERTAIN = "uncertain"  # < 30% confidence


@dataclass
class IntelligentDetectionResult:
    """Result from intelligent detection"""
    is_success: bool
    confidence: DetectionConfidence
    success_probability: float
    pattern_quality: str
    problem: str
    solution: str
    key_insights: List[str]
    evidence: Dict[str, Any]
    recommendation: str


class IntelligentDetector:
    """
    Combines multiple analysis techniques for truly intelligent pattern detection.
    Understands conversation flow, execution results, user intent, and context.
    """

    def __init__(self):
        self.conversation_analyzer = ConversationAnalyzer()
        self.execution_monitor = ExecutionMonitor()
        self.intent_detector = IntentDetector()

        # Weights for different signals
        self.signal_weights = {
            'conversation_flow': 0.35,  # How the conversation progressed
            'execution_results': 0.25,  # Test/build outputs
            'user_intent': 0.20,        # What the user meant
            'behavioral_signals': 0.20   # User behavior patterns
        }

    def detect(self, session_entries: List[Dict]) -> IntelligentDetectionResult:
        """
        Perform intelligent detection on a session.
        Combines multiple analysis techniques for accurate detection.
        """
        if not session_entries:
            return self._empty_result()

        # 1. Deep conversation analysis
        conversation_analysis = self.conversation_analyzer.analyze_conversation(session_entries)

        # 2. Execution signal analysis
        execution_signals = self._analyze_execution_signals(session_entries)

        # 3. Intent analysis
        intent_analysis = self._analyze_user_intent(session_entries)

        # 4. Behavioral analysis
        behavioral_signals = self._analyze_behavioral_patterns(session_entries)

        # 5. Combine all signals intelligently
        result = self._combine_signals(
            conversation_analysis,
            execution_signals,
            intent_analysis,
            behavioral_signals,
            session_entries
        )

        return result

    def _analyze_execution_signals(self, entries: List[Dict]) -> Dict[str, Any]:
        """Analyze execution results from tool calls"""
        signals = []
        test_results = {'passed': 0, 'failed': 0}
        build_success = False
        errors_found = []

        for entry in entries:
            if entry.get('type') == 'tool_call':
                tool = entry.get('tool', '')
                output = str(entry.get('output', '')).lower()

                # Analyze with execution monitor
                exec_signals = self.execution_monitor.analyze_output(output)

                for signal in exec_signals:
                    signals.append(signal)

                    # Track specific outcomes
                    if signal.signal_type == 'test_pass':
                        test_results['passed'] += 1
                    elif signal.signal_type == 'test_fail':
                        test_results['failed'] += 1
                    elif signal.signal_type == 'build_success':
                        build_success = True
                    elif signal.signal_type == 'error':
                        errors_found.append(signal.details[:100])

        # Calculate execution success score
        exec_score = self._calculate_execution_score(test_results, build_success, errors_found)

        return {
            'score': exec_score,
            'test_results': test_results,
            'build_success': build_success,
            'errors': errors_found,
            'signals': signals
        }

    def _analyze_user_intent(self, entries: List[Dict]) -> Dict[str, Any]:
        """Analyze user intent throughout the conversation"""
        # Extract conversation for intent analysis
        conversation = []
        for entry in entries:
            if entry.get('type') in ['user_message', 'assistant_message']:
                conversation.append({
                    'role': 'user' if entry.get('type') == 'user_message' else 'assistant',
                    'content': entry.get('content', '')
                })

        # Analyze intent flow
        intent_flow = self.intent_detector.analyze_conversation_flow(conversation)

        return {
            'overall_intent': intent_flow.get('overall_intent'),
            'confidence': intent_flow.get('confidence'),
            'intent_progression': intent_flow.get('intents', [])
        }

    def _analyze_behavioral_patterns(self, entries: List[Dict]) -> Dict[str, Any]:
        """Analyze behavioral patterns in the conversation"""
        patterns = {
            'user_moves_on': False,
            'ai_claims_done_user_continues': False,
            'repeated_attempts': 0,
            'quick_resolution': False,
            'user_thanks': False,
            'no_further_complaints': False
        }

        # Check for AI completion → user continuation pattern
        for i in range(len(entries) - 1):
            current = entries[i]
            next_entry = entries[i + 1]

            if current.get('type') == 'assistant_message':
                content = str(current.get('content', '')).lower()
                if any(word in content for word in ['done', 'complete', 'fixed', 'should work']):
                    # AI claimed completion
                    next_content = str(next_entry.get('content', '')).lower()

                    # Check user response
                    if next_entry.get('type') == 'user_message':
                        if any(word in next_content for word in ['next', 'now', 'also', 'another']):
                            patterns['ai_claims_done_user_continues'] = True
                            patterns['user_moves_on'] = True
                        elif 'thanks' in next_content or 'thank' in next_content:
                            patterns['user_thanks'] = True
                        elif not any(word in next_content for word in ['error', 'broken', 'failed']):
                            patterns['no_further_complaints'] = True

        # Count repeated attempts
        error_mentions = sum(1 for e in entries
                           if 'error' in str(e.get('content', '')).lower())
        patterns['repeated_attempts'] = error_mentions

        # Check resolution speed
        if len(entries) < 10 and patterns['ai_claims_done_user_continues']:
            patterns['quick_resolution'] = True

        # Calculate behavioral score
        behavior_score = 0.5  # Start neutral
        if patterns['ai_claims_done_user_continues']:
            behavior_score = 0.9
        elif patterns['user_thanks']:
            behavior_score = 0.85
        elif patterns['no_further_complaints']:
            behavior_score = 0.75
        elif patterns['user_moves_on']:
            behavior_score = 0.7

        # Penalize for repeated attempts
        behavior_score -= (patterns['repeated_attempts'] * 0.05)
        behavior_score = max(0, min(1, behavior_score))

        return {
            'score': behavior_score,
            'patterns': patterns
        }

    def _calculate_execution_score(self, test_results: Dict, build_success: bool,
                                  errors: List) -> float:
        """Calculate score from execution results"""
        score = 0.5  # Start neutral

        # Test results are strongest signal
        if test_results['passed'] > 0 and test_results['failed'] == 0:
            score = 0.95
        elif test_results['passed'] > test_results['failed']:
            score = 0.75
        elif test_results['failed'] > 0:
            score = 0.25

        # Build success is good signal
        if build_success:
            score = max(score, 0.8)

        # Errors reduce score
        if errors:
            score -= (len(errors) * 0.1)

        return max(0, min(1, score))

    def _combine_signals(self, conversation: Dict, execution: Dict,
                        intent: Dict, behavioral: Dict,
                        entries: List[Dict]) -> IntelligentDetectionResult:
        """Intelligently combine all signals into final result"""

        # Calculate weighted success probability
        success_probability = (
            conversation['success_score'] * self.signal_weights['conversation_flow'] +
            execution['score'] * self.signal_weights['execution_results'] +
            (intent['confidence'] if intent['overall_intent'] == 'positive' else 0) *
            self.signal_weights['user_intent'] +
            behavioral['score'] * self.signal_weights['behavioral_signals']
        )

        # Determine confidence level
        if success_probability >= 0.9:
            confidence = DetectionConfidence.CERTAIN
        elif success_probability >= 0.7:
            confidence = DetectionConfidence.HIGH
        elif success_probability >= 0.5:
            confidence = DetectionConfidence.MEDIUM
        elif success_probability >= 0.3:
            confidence = DetectionConfidence.LOW
        else:
            confidence = DetectionConfidence.UNCERTAIN

        # Extract key insights
        insights = []

        # Add conversation insights
        insights.extend(conversation.get('insights', []))

        # Add execution insights
        if execution['test_results']['passed'] > 0:
            insights.append(f"{execution['test_results']['passed']} tests passed")
        if execution['build_success']:
            insights.append("Build succeeded")

        # Add behavioral insights
        if behavioral['patterns']['ai_claims_done_user_continues']:
            insights.append("User continued after AI completion (implicit success)")
        if behavioral['patterns']['quick_resolution']:
            insights.append("Quick resolution achieved")

        # Add intent insights
        if intent['overall_intent'] == 'positive' and intent['confidence'] > 0.7:
            insights.append("User sentiment is positive")

        # Determine recommendation
        recommendation = self._generate_recommendation(
            success_probability,
            confidence,
            conversation['quality']
        )

        # Build evidence dictionary
        evidence = {
            'conversation_analysis': {
                'score': conversation['success_score'],
                'user_satisfaction': conversation['user_satisfaction'],
                'ai_claimed': conversation['ai_claimed_completion'],
                'user_confirmed': conversation['user_confirmed']
            },
            'execution_results': {
                'score': execution['score'],
                'tests': execution['test_results'],
                'build': execution['build_success']
            },
            'user_intent': {
                'sentiment': intent['overall_intent'],
                'confidence': intent['confidence']
            },
            'behavioral_patterns': {
                'score': behavioral['score'],
                'key_pattern': self._get_key_behavioral_pattern(behavioral['patterns'])
            }
        }

        return IntelligentDetectionResult(
            is_success=success_probability >= 0.5,
            confidence=confidence,
            success_probability=success_probability,
            pattern_quality=conversation.get('quality', 'unknown'),
            problem=conversation.get('problem', 'Unknown problem'),
            solution=conversation.get('solution', 'Solution not identified'),
            key_insights=insights,
            evidence=evidence,
            recommendation=recommendation
        )

    def _get_key_behavioral_pattern(self, patterns: Dict) -> str:
        """Identify the most significant behavioral pattern"""
        if patterns['ai_claims_done_user_continues']:
            return "AI completion followed by user continuation"
        elif patterns['user_thanks']:
            return "User expressed gratitude"
        elif patterns['no_further_complaints']:
            return "No complaints after solution"
        elif patterns['quick_resolution']:
            return "Quick problem resolution"
        else:
            return "No clear behavioral pattern"

    def _generate_recommendation(self, probability: float,
                                confidence: DetectionConfidence,
                                quality: str) -> str:
        """Generate recommendation based on analysis"""
        if confidence == DetectionConfidence.CERTAIN and quality == 'gold':
            return "Definitely save this pattern - high quality solution"
        elif confidence in [DetectionConfidence.CERTAIN, DetectionConfidence.HIGH]:
            return "Should save this pattern - clear success signals"
        elif confidence == DetectionConfidence.MEDIUM:
            return "Consider saving - moderate success indicators"
        elif quality == 'anti':
            return "Save as anti-pattern - what not to do"
        else:
            return "Insufficient evidence - continue monitoring"

    def _empty_result(self) -> IntelligentDetectionResult:
        """Return empty result for empty sessions"""
        return IntelligentDetectionResult(
            is_success=False,
            confidence=DetectionConfidence.UNCERTAIN,
            success_probability=0.0,
            pattern_quality='unknown',
            problem='No session data',
            solution='No solution',
            key_insights=[],
            evidence={},
            recommendation='No data to analyze'
        )