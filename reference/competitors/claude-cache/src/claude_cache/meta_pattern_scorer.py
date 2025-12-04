"""Unified meta-pattern scoring system that evaluates all pattern types together"""

from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import json


class MetaPatternScorer:
    """Unified pattern evaluation that considers success, journey, anti-patterns, and cross-project intelligence"""

    def __init__(self, knowledge_base=None):
        self.kb = knowledge_base

        # Weights for different pattern types in overall scoring
        self.pattern_weights = {
            'success_patterns': 0.35,
            'journey_patterns': 0.25,
            'anti_patterns': 0.20,
            'cross_project_patterns': 0.20
        }

        # Quality thresholds for different pattern types
        self.quality_thresholds = {
            'success_patterns': {
                'high': 0.8,
                'medium': 0.6,
                'low': 0.4
            },
            'journey_patterns': {
                'gold': 0.9,
                'silver': 0.75,
                'bronze': 0.6,
                'caution': 0.4
            },
            'anti_patterns': {
                'critical': 0.8,  # Clear anti-pattern with high confidence
                'warning': 0.6,   # Potential anti-pattern
                'note': 0.4       # Minor concern
            },
            'cross_project_patterns': {
                'universal': 0.9,
                'transferable': 0.7,
                'context_dependent': 0.5,
                'project_specific': 0.3
            }
        }

    def evaluate_session_patterns(self, session_entries: List[Dict], session_context: Dict = None) -> Dict:
        """Comprehensive evaluation of all pattern types for a session"""

        # Initialize pattern analysis results
        pattern_analysis = {
            'success_score': 0.0,
            'journey_score': 0.0,
            'anti_pattern_score': 0.0,
            'cross_project_score': 0.0,
            'meta_score': 0.0,
            'confidence': 'low',
            'pattern_types_detected': [],
            'recommendations': [],
            'quality_indicators': {},
            'cross_validation_signals': {}
        }

        if not session_entries:
            return pattern_analysis

        # Analyze each pattern type
        success_analysis = self._analyze_success_patterns(session_entries)
        journey_analysis = self._analyze_journey_patterns(session_entries)
        anti_pattern_analysis = self._analyze_anti_patterns(session_entries)
        cross_project_analysis = self._analyze_cross_project_patterns(session_entries, session_context)

        # Store individual pattern scores
        pattern_analysis['success_score'] = success_analysis.get('score', 0.0)
        pattern_analysis['journey_score'] = journey_analysis.get('score', 0.0)
        pattern_analysis['anti_pattern_score'] = anti_pattern_analysis.get('score', 0.0)
        pattern_analysis['cross_project_score'] = cross_project_analysis.get('score', 0.0)

        # Perform cross-validation between pattern types
        cross_validation = self._cross_validate_patterns(
            success_analysis, journey_analysis, anti_pattern_analysis, cross_project_analysis
        )
        pattern_analysis['cross_validation_signals'] = cross_validation

        # Calculate unified meta-score
        meta_score = self._calculate_meta_score(
            success_analysis, journey_analysis, anti_pattern_analysis,
            cross_project_analysis, cross_validation
        )
        pattern_analysis['meta_score'] = meta_score

        # Determine overall confidence
        pattern_analysis['confidence'] = self._determine_confidence_level(
            pattern_analysis, cross_validation
        )

        # Identify detected pattern types
        pattern_analysis['pattern_types_detected'] = self._identify_pattern_types(
            success_analysis, journey_analysis, anti_pattern_analysis, cross_project_analysis
        )

        # Generate recommendations
        pattern_analysis['recommendations'] = self._generate_recommendations(
            pattern_analysis, cross_validation
        )

        # Extract quality indicators
        pattern_analysis['quality_indicators'] = self._extract_quality_indicators(
            success_analysis, journey_analysis, anti_pattern_analysis, cross_project_analysis
        )

        return pattern_analysis

    def _analyze_success_patterns(self, session_entries: List[Dict]) -> Dict:
        """Analyze success patterns with enhanced scoring"""
        # This would integrate with existing SuccessDetector
        # For now, simulate the analysis
        return {
            'score': 0.0,  # Would be populated by SuccessDetector
            'indicators': {},
            'confidence': 'medium',
            'pattern_data': {}
        }

    def _analyze_journey_patterns(self, session_entries: List[Dict]) -> Dict:
        """Analyze journey patterns using DualPathDetector"""
        # This would integrate with DualPathDetector
        return {
            'score': 0.0,
            'pattern_type': None,
            'attempts': [],
            'final_outcome': None,
            'confidence': 0.0
        }

    def _analyze_anti_patterns(self, session_entries: List[Dict]) -> Dict:
        """Analyze anti-patterns and failure modes"""
        anti_pattern_score = 0.0
        detected_anti_patterns = []

        # Common anti-pattern indicators
        anti_pattern_signals = {
            'repeated_errors': 0,
            'inefficient_approaches': 0,
            'broken_solutions': 0,
            'context_mismatches': 0
        }

        for entry in session_entries:
            content = str(entry.get('content', '')).lower()

            # Detect repeated error patterns
            if any(error_word in content for error_word in ['error', 'failed', 'broken', 'exception']):
                anti_pattern_signals['repeated_errors'] += 0.1

            # Detect inefficient approaches (multiple tool calls for same task)
            if entry.get('type') == 'tool_call':
                # Would analyze tool call efficiency
                pass

        # Calculate anti-pattern score (inverse - higher means more problems)
        total_signals = sum(anti_pattern_signals.values())
        anti_pattern_score = min(total_signals, 1.0)

        return {
            'score': anti_pattern_score,
            'signals': anti_pattern_signals,
            'detected_patterns': detected_anti_patterns,
            'severity': 'low' if anti_pattern_score < 0.3 else 'medium' if anti_pattern_score < 0.7 else 'high'
        }

    def _analyze_cross_project_patterns(self, session_entries: List[Dict], context: Dict = None) -> Dict:
        """Analyze transferability and cross-project applicability"""
        if not context:
            context = {}

        transferability_score = 0.0
        universal_elements = []

        # Analyze for universal patterns
        for entry in session_entries:
            content = str(entry.get('content', '')).lower()

            # Common universal patterns
            if any(pattern in content for pattern in ['authentication', 'validation', 'error handling']):
                transferability_score += 0.2
                universal_elements.append('common_pattern')

            # Technology-agnostic approaches
            if any(approach in content for approach in ['design pattern', 'architecture', 'best practice']):
                transferability_score += 0.3
                universal_elements.append('architectural_pattern')

        return {
            'score': min(transferability_score, 1.0),
            'universal_elements': universal_elements,
            'transferability': 'high' if transferability_score > 0.7 else 'medium' if transferability_score > 0.4 else 'low'
        }

    def _cross_validate_patterns(self, success_analysis: Dict, journey_analysis: Dict,
                                anti_pattern_analysis: Dict, cross_project_analysis: Dict) -> Dict:
        """Cross-validate patterns to identify conflicts and confirmations"""

        validation_signals = {
            'pattern_consistency': 0.0,
            'conflict_indicators': [],
            'confirmation_signals': [],
            'reliability_score': 0.0
        }

        # Check for success vs anti-pattern conflicts
        success_score = success_analysis.get('score', 0.0)
        anti_pattern_score = anti_pattern_analysis.get('score', 0.0)

        if success_score > 0.6 and anti_pattern_score > 0.6:
            validation_signals['conflict_indicators'].append('success_vs_antipattern_conflict')
            validation_signals['reliability_score'] -= 0.2

        # Check for journey pattern confirmation
        journey_score = journey_analysis.get('score', 0.0)
        if success_score > 0.5 and journey_score > 0.5:
            validation_signals['confirmation_signals'].append('success_journey_alignment')
            validation_signals['reliability_score'] += 0.3

        # Check cross-project transferability alignment
        cross_project_score = cross_project_analysis.get('score', 0.0)
        if success_score > 0.7 and cross_project_score > 0.7:
            validation_signals['confirmation_signals'].append('transferable_success_pattern')
            validation_signals['reliability_score'] += 0.2

        # Calculate pattern consistency
        all_scores = [success_score, journey_score, 1.0 - anti_pattern_score, cross_project_score]
        score_variance = self._calculate_variance(all_scores)
        validation_signals['pattern_consistency'] = 1.0 - score_variance

        # Normalize reliability score
        validation_signals['reliability_score'] = max(0.0, min(1.0,
            0.5 + validation_signals['reliability_score']))

        return validation_signals

    def _calculate_meta_score(self, success_analysis: Dict, journey_analysis: Dict,
                             anti_pattern_analysis: Dict, cross_project_analysis: Dict,
                             cross_validation: Dict) -> float:
        """Calculate unified meta-score considering all pattern types"""

        # Base scores from individual pattern analyses
        success_score = success_analysis.get('score', 0.0)
        journey_score = journey_analysis.get('score', 0.0)
        anti_pattern_penalty = anti_pattern_analysis.get('score', 0.0)  # This is a penalty
        cross_project_score = cross_project_analysis.get('score', 0.0)

        # Weighted combination
        base_meta_score = (
            success_score * self.pattern_weights['success_patterns'] +
            journey_score * self.pattern_weights['journey_patterns'] +
            (1.0 - anti_pattern_penalty) * self.pattern_weights['anti_patterns'] +  # Invert anti-pattern score
            cross_project_score * self.pattern_weights['cross_project_patterns']
        )

        # Apply cross-validation adjustments
        reliability_score = cross_validation.get('reliability_score', 0.5)
        consistency_score = cross_validation.get('pattern_consistency', 0.5)

        # Adjust meta-score based on cross-validation
        adjusted_meta_score = base_meta_score * (reliability_score + consistency_score) / 2.0

        return min(adjusted_meta_score, 1.0)

    def _determine_confidence_level(self, pattern_analysis: Dict, cross_validation: Dict) -> str:
        """Determine overall confidence level"""
        meta_score = pattern_analysis.get('meta_score', 0.0)
        reliability_score = cross_validation.get('reliability_score', 0.0)
        consistency_score = cross_validation.get('pattern_consistency', 0.0)

        # High confidence: high scores across all metrics
        if meta_score > 0.7 and reliability_score > 0.7 and consistency_score > 0.7:
            return 'high'

        # Medium confidence: decent scores with some validation
        elif meta_score > 0.5 and (reliability_score > 0.5 or consistency_score > 0.5):
            return 'medium'

        # Low confidence: low scores or conflicts
        else:
            return 'low'

    def _identify_pattern_types(self, success_analysis: Dict, journey_analysis: Dict,
                               anti_pattern_analysis: Dict, cross_project_analysis: Dict) -> List[str]:
        """Identify which pattern types were detected"""
        detected_types = []

        if success_analysis.get('score', 0.0) > 0.4:
            detected_types.append('success_pattern')

        journey_score = journey_analysis.get('score', 0.0)
        if journey_score > 0.4:
            pattern_type = journey_analysis.get('pattern_type', 'journey')
            detected_types.append(f'journey_pattern_{pattern_type}')

        if anti_pattern_analysis.get('score', 0.0) > 0.4:
            detected_types.append('anti_pattern')

        if cross_project_analysis.get('score', 0.0) > 0.4:
            transferability = cross_project_analysis.get('transferability', 'low')
            detected_types.append(f'cross_project_{transferability}')

        return detected_types

    def _generate_recommendations(self, pattern_analysis: Dict, cross_validation: Dict) -> List[str]:
        """Generate actionable recommendations based on pattern analysis"""
        recommendations = []

        meta_score = pattern_analysis.get('meta_score', 0.0)
        confidence = pattern_analysis.get('confidence', 'low')

        # Recommendations based on overall score
        if meta_score < 0.3:
            recommendations.append("Consider reviewing approach - low pattern quality detected")
        elif meta_score > 0.8:
            recommendations.append("High-quality pattern detected - consider promoting for reuse")

        # Recommendations based on confidence
        if confidence == 'low':
            recommendations.append("Gather more validation signals to increase confidence")
        elif confidence == 'high':
            recommendations.append("Pattern validated across multiple signals - safe to apply")

        # Anti-pattern recommendations
        anti_pattern_score = pattern_analysis.get('anti_pattern_score', 0.0)
        if anti_pattern_score > 0.6:
            recommendations.append("Anti-patterns detected - review for potential improvements")

        # Cross-project recommendations
        cross_project_score = pattern_analysis.get('cross_project_score', 0.0)
        if cross_project_score > 0.7:
            recommendations.append("Pattern shows high transferability - consider adding to global patterns")

        return recommendations

    def _extract_quality_indicators(self, success_analysis: Dict, journey_analysis: Dict,
                                   anti_pattern_analysis: Dict, cross_project_analysis: Dict) -> Dict:
        """Extract quality indicators from all pattern types"""
        return {
            'execution_evidence': success_analysis.get('indicators', {}).get('execution_success', False),
            'user_satisfaction': success_analysis.get('indicators', {}).get('user_satisfied', False),
            'journey_complexity': journey_analysis.get('pattern_type', 'unknown'),
            'anti_pattern_severity': anti_pattern_analysis.get('severity', 'unknown'),
            'transferability': cross_project_analysis.get('transferability', 'unknown'),
            'pattern_completeness': len(self._identify_pattern_types(
                success_analysis, journey_analysis, anti_pattern_analysis, cross_project_analysis
            ))
        }

    def _calculate_variance(self, scores: List[float]) -> float:
        """Calculate variance of scores to measure consistency"""
        if not scores:
            return 1.0

        mean = sum(scores) / len(scores)
        variance = sum((score - mean) ** 2 for score in scores) / len(scores)
        return variance

    def should_store_pattern(self, pattern_analysis: Dict) -> Tuple[bool, str]:
        """Determine if a pattern should be stored and why"""
        meta_score = pattern_analysis.get('meta_score', 0.0)
        confidence = pattern_analysis.get('confidence', 'low')

        # High-confidence, high-quality patterns
        if meta_score > 0.7 and confidence == 'high':
            return True, "High-quality pattern with strong validation"

        # Medium quality with specific value
        elif meta_score > 0.5 and len(pattern_analysis.get('pattern_types_detected', [])) >= 2:
            return True, "Multi-signal pattern with medium quality"

        # Anti-patterns are valuable for learning
        elif pattern_analysis.get('anti_pattern_score', 0.0) > 0.6:
            return True, "Anti-pattern detected - valuable for prevention"

        # Cross-project patterns are valuable
        elif pattern_analysis.get('cross_project_score', 0.0) > 0.7:
            return True, "High transferability - valuable for reuse"

        else:
            return False, f"Quality threshold not met (score: {meta_score:.2f}, confidence: {confidence})"