"""Semantic similarity matching for implicit success pattern detection"""

import re
from typing import List, Dict, Set, Tuple, Optional
from difflib import SequenceMatcher
import json


class SemanticMatcher:
    """Enhanced pattern matching using semantic similarity and context"""

    def __init__(self):
        # Semantic clusters for success patterns
        self.success_clusters = {
            'completion': {
                'explicit': ['done', 'completed', 'finished', 'ready', 'delivered'],
                'implicit': ['works', 'functioning', 'operational', 'active', 'live'],
                'contextual': ['fixed', 'resolved', 'solved', 'implemented', 'deployed']
            },
            'satisfaction': {
                'explicit': ['perfect', 'excellent', 'great', 'awesome', 'amazing'],
                'implicit': ['good', 'nice', 'solid', 'clean', 'smooth'],
                'contextual': ['exactly', 'spot on', 'nailed it', 'what i needed']
            },
            'progression': {
                'explicit': ['next', 'moving on', 'continue', 'proceed'],
                'implicit': ['now', 'lets', 'also', 'additionally'],
                'contextual': ['ready for', 'time to', 'going to']
            },
            'validation': {
                'explicit': ['correct', 'right', 'accurate', 'valid'],
                'implicit': ['looks good', 'seems right', 'makes sense'],
                'contextual': ['thats it', 'you got it', 'exactly right']
            }
        }

        # Technical domain vocabularies
        self.domain_vocabularies = {
            'frontend': {
                'components': ['component', 'render', 'ui', 'interface', 'view'],
                'styling': ['css', 'style', 'layout', 'design', 'responsive'],
                'interaction': ['click', 'hover', 'animation', 'transition', 'interactive'],
                'state': ['state', 'props', 'context', 'redux', 'store']
            },
            'backend': {
                'api': ['endpoint', 'route', 'api', 'rest', 'graphql'],
                'data': ['database', 'query', 'model', 'schema', 'migration'],
                'auth': ['authentication', 'authorization', 'login', 'token', 'session'],
                'performance': ['cache', 'optimize', 'scaling', 'load', 'performance']
            },
            'devops': {
                'deployment': ['deploy', 'build', 'release', 'environment', 'production'],
                'infrastructure': ['server', 'cloud', 'docker', 'kubernetes', 'container'],
                'monitoring': ['logs', 'metrics', 'health', 'monitoring', 'alerts'],
                'pipeline': ['ci', 'cd', 'pipeline', 'automation', 'workflow']
            }
        }

        # Success transition patterns
        self.transition_patterns = [
            # Problem → Solution patterns
            (r'(error|issue|problem|bug)', r'(fixed|resolved|solved|working)'),
            (r'(not working|broken|failing)', r'(now works|functioning|operational)'),
            (r'(trying to|need to|want to)', r'(managed to|successfully|accomplished)'),

            # Question → Answer patterns
            (r'(how do i|can you|help me)', r'(here\'s how|you can|this works)'),
            (r'(what about|should i)', r'(yes|go ahead|that\'s right)'),

            # Uncertainty → Confirmation patterns
            (r'(not sure|maybe|possibly)', r'(definitely|exactly|correct)'),
            (r'(think|assume|guess)', r'(confirmed|verified|proven)')
        ]

    def calculate_semantic_similarity(self, text1: str, text2: str) -> float:
        """Calculate semantic similarity between two texts"""
        # Normalize texts
        text1_norm = self._normalize_text(text1)
        text2_norm = self._normalize_text(text2)

        # Basic string similarity
        seq_similarity = SequenceMatcher(None, text1_norm, text2_norm).ratio()

        # Semantic cluster similarity
        cluster_similarity = self._calculate_cluster_similarity(text1_norm, text2_norm)

        # Domain vocabulary similarity
        domain_similarity = self._calculate_domain_similarity(text1_norm, text2_norm)

        # Combined similarity score
        return (seq_similarity * 0.3) + (cluster_similarity * 0.4) + (domain_similarity * 0.3)

    def detect_implicit_success_signals(self, conversation: List[Dict]) -> List[Dict]:
        """Detect implicit success signals in conversation flow"""
        signals = []

        for i, entry in enumerate(conversation):
            if entry.get('role') == 'user':
                content = entry.get('content', '').lower()

                # Check for transition patterns
                transitions = self._detect_success_transitions(conversation, i)
                if transitions:
                    signals.extend(transitions)

                # Check for semantic clusters
                cluster_matches = self._find_cluster_matches(content)
                if cluster_matches:
                    signals.extend(cluster_matches)

                # Check for domain-specific success indicators
                domain_signals = self._detect_domain_success(content, conversation)
                if domain_signals:
                    signals.extend(domain_signals)

        return signals

    def _normalize_text(self, text: str) -> str:
        """Normalize text for better matching"""
        # Convert to lowercase
        text = text.lower()

        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text).strip()

        # Remove punctuation for keyword matching
        text = re.sub(r'[^\w\s]', ' ', text)

        return text

    def _calculate_cluster_similarity(self, text1: str, text2: str) -> float:
        """Calculate similarity based on semantic clusters"""
        text1_clusters = set()
        text2_clusters = set()

        # Find which clusters each text belongs to
        for cluster_name, cluster_data in self.success_clusters.items():
            for category, keywords in cluster_data.items():
                if any(keyword in text1 for keyword in keywords):
                    text1_clusters.add(f"{cluster_name}_{category}")
                if any(keyword in text2 for keyword in keywords):
                    text2_clusters.add(f"{cluster_name}_{category}")

        # Calculate Jaccard similarity
        if not text1_clusters and not text2_clusters:
            return 0.0

        intersection = len(text1_clusters.intersection(text2_clusters))
        union = len(text1_clusters.union(text2_clusters))

        return intersection / union if union > 0 else 0.0

    def _calculate_domain_similarity(self, text1: str, text2: str) -> float:
        """Calculate similarity based on domain vocabularies"""
        text1_domains = set()
        text2_domains = set()

        # Find which domains each text relates to
        for domain_name, domain_data in self.domain_vocabularies.items():
            for category, keywords in domain_data.items():
                if any(keyword in text1 for keyword in keywords):
                    text1_domains.add(f"{domain_name}_{category}")
                if any(keyword in text2 for keyword in keywords):
                    text2_domains.add(f"{domain_name}_{category}")

        # Calculate domain overlap
        if not text1_domains and not text2_domains:
            return 0.0

        intersection = len(text1_domains.intersection(text2_domains))
        union = len(text1_domains.union(text2_domains))

        return intersection / union if union > 0 else 0.0

    def _detect_success_transitions(self, conversation: List[Dict], current_index: int) -> List[Dict]:
        """Detect success transition patterns in conversation"""
        signals = []

        if current_index == 0:
            return signals

        # Look at previous assistant message and current user message
        prev_entry = conversation[current_index - 1] if current_index > 0 else None
        current_entry = conversation[current_index]

        if not prev_entry or prev_entry.get('role') != 'assistant':
            return signals

        prev_content = prev_entry.get('content', '').lower()
        current_content = current_entry.get('content', '').lower()

        # Check for transition patterns
        for problem_pattern, solution_pattern in self.transition_patterns:
            if (re.search(problem_pattern, prev_content) and
                re.search(solution_pattern, current_content)):
                signals.append({
                    'type': 'transition',
                    'pattern': f"{problem_pattern} → {solution_pattern}",
                    'confidence': 0.8,
                    'context': f"Problem: {problem_pattern}, Solution: {solution_pattern}"
                })

        return signals

    def _find_cluster_matches(self, content: str) -> List[Dict]:
        """Find semantic cluster matches in content"""
        matches = []

        for cluster_name, cluster_data in self.success_clusters.items():
            for category, keywords in cluster_data.items():
                for keyword in keywords:
                    if keyword in content:
                        confidence = self._calculate_keyword_confidence(keyword, content, category)
                        matches.append({
                            'type': 'cluster_match',
                            'cluster': cluster_name,
                            'category': category,
                            'keyword': keyword,
                            'confidence': confidence
                        })

        return matches

    def _calculate_keyword_confidence(self, keyword: str, content: str, category: str) -> float:
        """Calculate confidence for keyword match based on context"""
        base_confidence = 0.6

        # Boost confidence for explicit categories
        if category == 'explicit':
            base_confidence = 0.8
        elif category == 'contextual':
            base_confidence = 0.7

        # Boost if keyword appears multiple times
        keyword_count = content.count(keyword)
        if keyword_count > 1:
            base_confidence += min(keyword_count * 0.1, 0.2)

        # Boost if surrounded by positive context
        positive_context = ['really', 'very', 'quite', 'absolutely', 'definitely']
        for context_word in positive_context:
            if f"{context_word} {keyword}" in content or f"{keyword} {context_word}" in content:
                base_confidence += 0.1
                break

        return min(base_confidence, 1.0)

    def _detect_domain_success(self, content: str, conversation: List[Dict]) -> List[Dict]:
        """Detect domain-specific success indicators"""
        signals = []

        # Determine the domain context from conversation
        domain_context = self._determine_conversation_domain(conversation)

        if not domain_context:
            return signals

        # Look for domain-specific success patterns
        for domain in domain_context:
            if domain in self.domain_vocabularies:
                for category, keywords in self.domain_vocabularies[domain].items():
                    for keyword in keywords:
                        if keyword in content:
                            # Check if keyword is used in a success context
                            if self._is_success_context(keyword, content):
                                signals.append({
                                    'type': 'domain_success',
                                    'domain': domain,
                                    'category': category,
                                    'keyword': keyword,
                                    'confidence': 0.7
                                })

        return signals

    def _determine_conversation_domain(self, conversation: List[Dict]) -> Set[str]:
        """Determine the technical domain(s) of the conversation"""
        domains = set()

        for entry in conversation:
            content = entry.get('content', '').lower()

            for domain_name, domain_data in self.domain_vocabularies.items():
                domain_score = 0
                for category, keywords in domain_data.items():
                    for keyword in keywords:
                        if keyword in content:
                            domain_score += 1

                # Consider domain relevant if it has multiple keyword matches
                if domain_score >= 2:
                    domains.add(domain_name)

        return domains

    def _is_success_context(self, keyword: str, content: str) -> bool:
        """Check if a keyword is used in a success context"""
        # Look for positive verbs around the keyword
        positive_verbs = ['works', 'working', 'fixed', 'implemented', 'completed', 'successful']
        negative_verbs = ['broken', 'failing', 'error', 'issue', 'problem']

        # Create a window around the keyword
        keyword_index = content.find(keyword)
        if keyword_index == -1:
            return False

        window_start = max(0, keyword_index - 30)
        window_end = min(len(content), keyword_index + len(keyword) + 30)
        window = content[window_start:window_end]

        # Check for positive vs negative context
        positive_count = sum(1 for verb in positive_verbs if verb in window)
        negative_count = sum(1 for verb in negative_verbs if verb in window)

        return positive_count > negative_count

    def analyze_conversation_success_signals(self, conversation: List[Dict]) -> Dict:
        """Comprehensive analysis of success signals in conversation"""
        all_signals = self.detect_implicit_success_signals(conversation)

        # Aggregate signals by type
        signal_summary = {
            'transition_signals': [],
            'cluster_signals': [],
            'domain_signals': [],
            'overall_confidence': 0.0,
            'success_probability': 0.0
        }

        for signal in all_signals:
            signal_type = signal.get('type', '')
            if signal_type == 'transition':
                signal_summary['transition_signals'].append(signal)
            elif signal_type == 'cluster_match':
                signal_summary['cluster_signals'].append(signal)
            elif signal_type == 'domain_success':
                signal_summary['domain_signals'].append(signal)

        # Calculate overall confidence
        if all_signals:
            total_confidence = sum(signal.get('confidence', 0) for signal in all_signals)
            signal_summary['overall_confidence'] = total_confidence / len(all_signals)

            # Calculate success probability based on signal types and confidence
            transition_weight = len(signal_summary['transition_signals']) * 0.4
            cluster_weight = len(signal_summary['cluster_signals']) * 0.3
            domain_weight = len(signal_summary['domain_signals']) * 0.3

            signal_summary['success_probability'] = min(
                (transition_weight + cluster_weight + domain_weight) *
                signal_summary['overall_confidence'],
                1.0
            )

        return signal_summary