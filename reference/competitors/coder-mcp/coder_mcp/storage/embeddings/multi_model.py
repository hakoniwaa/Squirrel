"""
Multi-Model Embedding System
Uses multiple embedding models for better coverage and understanding
"""

import logging
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from ..providers import EmbeddingProvider, LocalEmbeddingProvider, OpenAIEmbeddingProvider

logger = logging.getLogger(__name__)


class CodeEmbeddingProvider(EmbeddingProvider):
    """Code-specific embedding provider using CodeBERT or similar models"""

    def __init__(self, model_name: str = "microsoft/codebert-base"):
        self.model_name = model_name
        self.dimensions = 768  # CodeBERT dimensions
        self.max_tokens = 512
        self._model = None

    async def create_embedding(self, text: str) -> Optional[List[float]]:
        """Create code-specific embedding"""
        try:
            # For now, use a hash-based approach similar to LocalEmbeddingProvider
            # In production, you'd want to use sentence-transformers or similar
            import hashlib

            # Add code-specific preprocessing
            processed_text = self._preprocess_code(text)

            try:
                hash_obj = hashlib.md5(processed_text.encode("utf-8"), usedforsecurity=False)
            except TypeError:
                # Fallback for older Python versions that don't support usedforsecurity parameter
                hash_obj = hashlib.md5(processed_text.encode("utf-8"))  # nosec B324

            hash_bytes = hash_obj.digest()
            embedding = []

            for i in range(self.dimensions):
                byte_val = hash_bytes[i % len(hash_bytes)]
                # Scale to [-1, 1] with code-specific bias
                float_val = (byte_val / 127.5) - 1.0
                # Add slight code-specific adjustment
                float_val *= 0.9  # Reduce magnitude slightly for code
                embedding.append(float_val)

            return embedding

        except Exception as e:
            logger.error(f"Failed to create code embedding: {e}")
            return None

    def _preprocess_code(self, text: str) -> str:
        """Preprocess code text for better embedding"""
        # Remove excess whitespace
        text = " ".join(text.split())

        # Normalize common code patterns
        text = text.replace("  ", " ")
        text = text.replace("\t", " ")

        # Add code-specific markers
        if "def " in text:
            text = f"[FUNCTION] {text}"
        elif "class " in text:
            text = f"[CLASS] {text}"
        elif "import " in text:
            text = f"[IMPORT] {text}"

        return text

    def get_dimensions(self) -> int:
        return self.dimensions

    def get_max_tokens(self) -> int:
        return self.max_tokens


class MultiModelEmbedding:
    """
    Use multiple embedding models for better coverage:
    - Code-specific model (CodeBERT/CodeT5)
    - General purpose (OpenAI Ada)
    - Local fallback (Sentence Transformers)
    """

    def __init__(self, openai_api_key: Optional[str] = None):
        self.models = {
            "code": CodeEmbeddingProvider(),
            "general": OpenAIEmbeddingProvider(openai_api_key) if openai_api_key else None,
            "local": LocalEmbeddingProvider(dimensions=384),
        }

    async def create_hybrid_embedding(self, text: str, context_type: str = "auto") -> List[float]:
        """Create embeddings using multiple models based on content type"""

        # Detect content type if not provided
        if context_type == "auto":
            context_type = self._detect_content_type(text)

        # Get embeddings from relevant models
        embeddings = []

        if context_type in ["code", "mixed"]:
            code_provider = self.models["code"]
            if code_provider:
                code_emb = await code_provider.create_embedding(text)
                if code_emb:
                    embeddings.append(("code", code_emb, 0.6))  # Higher weight for code

        if context_type in ["docs", "mixed", "comments"] and self.models["general"]:
            general_provider = self.models["general"]
            if general_provider:
                general_emb = await general_provider.create_embedding(text)
                if general_emb:
                    embeddings.append(("general", general_emb, 0.4))

        # Always include local fallback
        if self.models["local"]:
            local_emb = await self.models["local"].create_embedding(text)
            if local_emb:
                weight = 0.3 if embeddings else 1.0  # Higher weight if it's the only model
                embeddings.append(("local", local_emb, weight))

        # Combine embeddings with weighted average
        return self._combine_embeddings(embeddings)

    def _detect_content_type(self, text: str) -> str:
        """Detect the type of content for appropriate model selection"""
        text_lower = text.lower()

        # Code indicators
        code_indicators = [
            "def ",
            "class ",
            "function ",
            "import ",
            "from ",
            "()",
            "{",
            "}",
            "var ",
            "let ",
            "const ",
        ]
        code_score = sum(1 for indicator in code_indicators if indicator in text_lower)

        # Documentation indicators
        doc_indicators = [
            "description",
            "example",
            "usage",
            "note:",
            "todo:",
            "fixme:",
            "bug:",
            "feature:",
        ]
        doc_score = sum(1 for indicator in doc_indicators if indicator in text_lower)

        # Comment indicators
        comment_indicators = ["#", "//", "/*", '"""', "'''"]
        comment_score = sum(1 for indicator in comment_indicators if indicator in text)

        if code_score > doc_score and code_score > comment_score:
            return "code"
        elif doc_score > 0:
            return "docs"
        elif comment_score > 0:
            return "comments"
        else:
            return "mixed"

    def _combine_embeddings(self, embeddings: List[Tuple[str, List[float], float]]) -> List[float]:
        """Combine multiple embeddings with weights"""
        if not embeddings:
            return []

        # Normalize dimensions - use the largest dimension
        max_dim = max(len(emb[1]) for emb in embeddings)
        combined = np.zeros(max_dim)

        total_weight = sum(emb[2] for emb in embeddings)

        for name, embedding, weight in embeddings:
            # Pad if necessary
            embedding_array = np.array(embedding)
            if len(embedding_array) < max_dim:
                embedding_array = np.pad(embedding_array, (0, max_dim - len(embedding_array)))
            elif len(embedding_array) > max_dim:
                embedding_array = embedding_array[:max_dim]

            combined += embedding_array * (weight / total_weight)

        return combined.tolist()


class ContextualEmbedding:
    """Add context to embeddings for better relevance"""

    def __init__(self, base_embedding: MultiModelEmbedding):
        self.base_embedding = base_embedding

    async def create_contextual_embedding(
        self,
        text: str,
        file_path: str,
        surrounding_code: Optional[str] = None,
        imports: Optional[List[str]] = None,
        class_context: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Create embeddings with rich context"""

        # Build context string
        context_parts = []

        # Add file path context
        context_parts.append(f"File: {file_path}")

        # Add language context
        language = self._detect_language(file_path)
        context_parts.append(f"Language: {language}")

        # Add import context
        if imports:
            context_parts.append(f"Imports: {', '.join(imports[:5])}")

        # Add class/function context
        if class_context:
            context_parts.append(f"Context: {class_context}")

        # Add surrounding code context
        if surrounding_code:
            context_parts.append(f"Surrounding: {surrounding_code[:200]}...")

        # Create enriched text
        enriched_text = "\n".join(context_parts) + "\n\n" + text

        # Generate embedding with context
        embedding = await self.base_embedding.create_hybrid_embedding(enriched_text, "mixed")

        return {
            "embedding": embedding,
            "metadata": {
                "file_path": file_path,
                "language": language,
                "has_context": True,
                "context_types": ["file", "language"]
                + (["imports"] if imports else [])
                + (["class"] if class_context else [])
                + (["surrounding"] if surrounding_code else []),
            },
        }

    def _detect_language(self, file_path: str) -> str:
        """Detect programming language from file path"""
        from pathlib import Path

        suffix = Path(file_path).suffix.lower()

        language_map = {
            ".py": "python",
            ".js": "javascript",
            ".ts": "typescript",
            ".jsx": "javascript",
            ".tsx": "typescript",
            ".java": "java",
            ".cpp": "cpp",
            ".c": "c",
            ".cs": "csharp",
            ".go": "go",
            ".rs": "rust",
            ".rb": "ruby",
            ".php": "php",
            ".swift": "swift",
            ".kt": "kotlin",
            ".scala": "scala",
            ".md": "markdown",
            ".txt": "text",
            ".json": "json",
            ".yaml": "yaml",
            ".yml": "yaml",
            ".xml": "xml",
            ".html": "html",
            ".css": "css",
            ".scss": "scss",
            ".sass": "sass",
            ".sql": "sql",
        }

        return language_map.get(suffix, "unknown")
