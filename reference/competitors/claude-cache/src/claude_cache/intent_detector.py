"""Semantic intent detection for user feedback using embeddings and patterns"""

import re
from typing import List, Dict, Tuple, Optional
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np


class IntentDetector:
    """Detect user intent using semantic understanding, not just keywords"""

    def __init__(self):
        # Positive intent examples with semantic meaning
        self.positive_examples = [
            # Direct success
            "that worked", "it's working", "fixed the issue", "solved the problem",
            "that did it", "problem solved", "issue resolved", "bug fixed",

            # Satisfaction
            "perfect", "excellent", "great job", "awesome", "fantastic",
            "exactly what I needed", "just what I wanted", "that's it",

            # Gratitude
            "thanks", "thank you", "appreciate it", "helpful", "that helps",

            # Confirmation
            "yes that's right", "correct", "exactly", "spot on", "nailed it",

            # Progress
            "good progress", "we're getting there", "almost there", "on the right track",

            # Understanding
            "I see", "makes sense", "got it", "I understand now", "clear now",

            # Completion
            "done", "finished", "complete", "all set", "ready to go",

            # Relief
            "finally", "at last", "phew", "glad that's done",

            # Implicit positive
            "ok let's move on", "next step", "now we can proceed",
            "let's continue", "what's next", "ready for the next part"
        ]

        # Negative intent examples
        self.negative_examples = [
            # Errors
            "still broken", "doesn't work", "failed", "error", "not working",
            "still having issues", "same problem", "didn't fix it",

            # Frustration
            "this is wrong", "that's not right", "no that's incorrect",
            "not what I wanted", "try again", "do it differently",

            # Confusion
            "I don't understand", "confused", "what's happening", "unclear",

            # Problems persist
            "still not working", "issue remains", "problem continues",
            "same error", "didn't help", "no improvement"
        ]

        # Neutral/continuing work
        self.neutral_examples = [
            "ok", "alright", "I see", "hmm", "let me check",
            "hold on", "wait", "one moment", "let me try"
        ]

        # Context patterns that modify intent
        self.context_modifiers = {
            'after_error': -0.3,  # Positive feedback after error might be sarcastic
            'after_success': 0.2,  # Neutral feedback after success likely positive
            'multiple_attempts': -0.2,  # Many attempts suggest frustration
            'quick_resolution': 0.3,  # Fast fix suggests success
        }

        # Initialize vectorizer for semantic similarity
        self.vectorizer = TfidfVectorizer(
            ngram_range=(1, 3),
            stop_words='english',
            max_features=500
        )

        # Prepare training data
        all_examples = (
            [(ex, 'positive') for ex in self.positive_examples] +
            [(ex, 'negative') for ex in self.negative_examples] +
            [(ex, 'neutral') for ex in self.neutral_examples]
        )

        self.example_texts = [ex[0] for ex in all_examples]
        self.example_labels = [ex[1] for ex in all_examples]

        # Fit vectorizer
        self.example_vectors = self.vectorizer.fit_transform(self.example_texts)

    def detect_intent(self, user_message: str, context: Dict = None) -> Tuple[str, float]:
        """
        Detect the intent of a user message

        Returns:
            Tuple of (intent_type, confidence)
            intent_type: 'positive', 'negative', 'neutral'
            confidence: 0.0 to 1.0
        """
        if not user_message:
            return 'neutral', 0.0

        # Clean and prepare message
        message_lower = user_message.lower().strip()

        # Quick exact match check
        for positive in self.positive_examples:
            if positive in message_lower:
                return 'positive', 0.9

        for negative in self.negative_examples:
            if negative in message_lower:
                return 'negative', 0.9

        # Semantic similarity check
        try:
            message_vector = self.vectorizer.transform([message_lower])
            similarities = cosine_similarity(message_vector, self.example_vectors)[0]

            # Get top 3 most similar examples
            top_indices = np.argsort(similarities)[-3:][::-1]
            top_similarities = similarities[top_indices]
            top_labels = [self.example_labels[i] for i in top_indices]

            # Weight by similarity
            label_scores = {'positive': 0, 'negative': 0, 'neutral': 0}
            for label, sim in zip(top_labels, top_similarities):
                if sim > 0.3:  # Threshold for relevance
                    label_scores[label] += sim

            # Apply context modifiers if provided
            if context:
                label_scores = self._apply_context_modifiers(label_scores, context)

            # Determine winner
            max_label = max(label_scores, key=label_scores.get)
            max_score = label_scores[max_label]
            total_score = sum(label_scores.values())

            if total_score > 0:
                confidence = max_score / total_score
                return max_label, confidence

        except Exception:
            # Fallback to simple keyword matching
            pass

        # Pattern-based detection as fallback
        return self._pattern_based_detection(message_lower)

    def _pattern_based_detection(self, message: str) -> Tuple[str, float]:
        """Fallback pattern-based detection"""
        # Positive patterns
        positive_patterns = [
            r'\b(work|fix|solv|help|great|perfect|thank|correct|done|complete)',
            r'(👍|✓|✅|💯|🎉|🙏)',
            r'\b(yes|yep|yeah|good|nice|excellent)\b',
            r"(that's it|got it|makes sense|I see)"
        ]

        # Negative patterns
        negative_patterns = [
            r'\b(error|fail|broke|wrong|issue|problem|not work|doesn)',
            r'(❌|⚠️|🔴|😞|😤)',
            r'\b(no|nope|incorrect|bad|still)\b',
            r"(doesn't|won't|can't|isn't)"
        ]

        positive_count = sum(1 for p in positive_patterns if re.search(p, message))
        negative_count = sum(1 for p in negative_patterns if re.search(p, message))

        if positive_count > negative_count:
            confidence = min(0.7 + (0.1 * positive_count), 1.0)
            return 'positive', confidence
        elif negative_count > positive_count:
            confidence = min(0.7 + (0.1 * negative_count), 1.0)
            return 'negative', confidence
        else:
            return 'neutral', 0.5

    def _apply_context_modifiers(self, scores: Dict, context: Dict) -> Dict:
        """Apply context-based score modifications"""
        modified_scores = scores.copy()

        # If we just had an error, positive feedback might be sarcastic
        if context.get('after_error'):
            modified_scores['positive'] *= 0.7

        # If we just had success, neutral feedback is likely positive
        if context.get('after_success'):
            modified_scores['positive'] += modified_scores['neutral'] * 0.3

        # Multiple attempts suggest frustration
        if context.get('attempt_count', 0) > 3:
            modified_scores['negative'] *= 1.3

        return modified_scores

    def analyze_conversation_flow(self, messages: List[Dict]) -> Dict:
        """
        Analyze a full conversation to understand overall success

        Args:
            messages: List of message dictionaries with 'role' and 'content'

        Returns:
            Dictionary with overall intent analysis
        """
        if not messages:
            return {'overall_intent': 'neutral', 'confidence': 0.0}

        # Track intent progression
        intents = []

        for i, msg in enumerate(messages):
            if msg.get('role') == 'user':
                # Build context from previous messages
                context = {
                    'after_error': False,
                    'after_success': False,
                    'attempt_count': 0
                }

                # Check previous assistant message for errors/success
                if i > 0 and messages[i-1].get('role') == 'assistant':
                    prev_content = messages[i-1].get('content', '').lower()
                    context['after_error'] = 'error' in prev_content or 'failed' in prev_content
                    context['after_success'] = 'success' in prev_content or '✓' in prev_content

                # Count attempts (how many user messages about same topic)
                context['attempt_count'] = sum(
                    1 for j in range(max(0, i-5), i)
                    if messages[j].get('role') == 'user'
                )

                intent, confidence = self.detect_intent(msg.get('content', ''), context)
                intents.append({
                    'intent': intent,
                    'confidence': confidence,
                    'message': msg.get('content', '')[:100]
                })

        # Determine overall intent
        if not intents:
            return {'overall_intent': 'neutral', 'confidence': 0.0}

        # Weight later messages more heavily (more recent = more important)
        weights = [0.5 + (0.5 * i / len(intents)) for i in range(len(intents))]

        intent_scores = {'positive': 0, 'negative': 0, 'neutral': 0}
        total_weight = sum(weights)

        for intent_data, weight in zip(intents, weights):
            intent_scores[intent_data['intent']] += (
                intent_data['confidence'] * weight / total_weight
            )

        overall_intent = max(intent_scores, key=intent_scores.get)
        overall_confidence = intent_scores[overall_intent]

        return {
            'overall_intent': overall_intent,
            'confidence': overall_confidence,
            'intents': intents,
            'scores': intent_scores
        }