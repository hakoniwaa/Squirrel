from typing import Any, Dict, List

try:
    from sentence_transformers import CrossEncoder

    HAS_SENTENCE_TRANSFORMERS = True
except ImportError:
    CrossEncoder = None  # type: ignore
    HAS_SENTENCE_TRANSFORMERS = False


class FeatureExtractor:
    """Extract additional ranking features"""

    def extract(self, query: str, content: str, metadata: Dict[str, Any]) -> Dict[str, float]:
        """Extract features for ranking"""
        import re

        features = {}

        # Handle None or empty content
        if content is None:
            content = ""

        # More sophisticated exact match score
        # Check if query words are contained within content words
        query_words = set(re.findall(r"[a-zA-Z_]+", query.lower()))
        content_lower = content.lower()

        if not query_words:
            features["exact_match_score"] = 0.0
        else:
            # Check how many query words are found in content
            matched_words = 0
            for word in query_words:
                if word in content_lower:
                    matched_words += 1

            # Calculate match ratio
            features["exact_match_score"] = matched_words / len(query_words)

        # Recency score (based on file modification time if available)
        features["recency_score"] = metadata.get("recency_score", 0.5)

        # Popularity score (based on usage frequency if available)
        features["popularity_score"] = metadata.get("popularity_score", 0.5)

        # Length penalty (prefer shorter, more focused results)
        content_length = len(content)
        features["length_score"] = max(0, 1 - (content_length / 10000))  # Normalize to 0-1

        return features


class SearchReranker:
    """Re-rank search results for better relevance"""

    def __init__(self):
        # Use a cross-encoder for accurate relevance scoring
        self.cross_encoder: Any = None  # Type annotation to avoid mypy issues
        if HAS_SENTENCE_TRANSFORMERS:
            try:
                self.cross_encoder = CrossEncoder("microsoft/codebert-base")
            except Exception:
                # Fallback to a simpler model if CodeBERT is not available
                self.cross_encoder = None
        else:
            self.cross_encoder = None
        self.feature_extractor = FeatureExtractor()

    async def rerank(
        self, query: str, candidates: List[Dict[str, Any]], top_k: int = 10
    ) -> List[Dict[str, Any]]:
        """Re-rank candidates using multiple signals"""

        # Handle empty candidates
        if not candidates:
            return []

        # 1. Extract features for each candidate
        scored_candidates = []

        for candidate in candidates:
            # Get content and handle None
            content = candidate.get("content", "")
            if content is None:
                content = ""

            # Convert to string if not already
            if not isinstance(content, str):
                content = str(content)

            # Cross-encoder score
            if self.cross_encoder:
                try:
                    ce_score = self.cross_encoder.predict([[query, content]])[0]
                except Exception:
                    # Fallback if cross-encoder fails
                    ce_score = 1.0 if query.lower() in content.lower() else 0.5
            else:
                # Simple fallback scoring
                ce_score = 1.0 if query.lower() in content.lower() else 0.5

            # Extract additional features
            features = self.feature_extractor.extract(
                query=query, content=content, metadata=candidate.get("metadata", {})
            )

            # Calculate final score
            final_score = self._calculate_final_score(
                vector_score=candidate.get("score", 0),
                cross_encoder_score=ce_score,
                features=features,
            )

            scored_candidates.append(
                {
                    **candidate,
                    "final_score": final_score,
                    "ranking_details": {
                        "vector_score": candidate.get("score", 0),
                        "ce_score": ce_score,
                        "features": features,  # Changed from feature_scores to features
                    },
                }
            )

        # Sort by final score
        scored_candidates.sort(key=lambda x: x["final_score"], reverse=True)

        return scored_candidates[:top_k]

    def _calculate_final_score(
        self, vector_score: float, cross_encoder_score: float, features: Dict[str, float]
    ) -> float:
        """Combine multiple signals into final score"""

        # Weighted combination
        weights = {
            "vector": 0.3,
            "cross_encoder": 0.4,
            "recency": 0.1,
            "popularity": 0.1,
            "exact_match": 0.1,
        }

        score = (
            weights["vector"] * vector_score
            + weights["cross_encoder"] * cross_encoder_score
            + weights["recency"] * features.get("recency_score", 0)
            + weights["popularity"] * features.get("popularity_score", 0)
            + weights["exact_match"] * features.get("exact_match_score", 0)
        )

        return score


# Make CrossEncoderReranker a proper alias instead of a wrapper
CrossEncoderReranker = SearchReranker
