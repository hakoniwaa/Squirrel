#!/usr/bin/env python3
"""
Language Detection Component
Efficient language detection for template generation
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class LanguageDetector:
    """Efficient language detection for project analysis"""

    # Language detection patterns - optimized for performance
    LANGUAGE_INDICATORS = {
        "python": {
            "files": ["pyproject.toml", "requirements.txt", "setup.py", "Pipfile", "setup.cfg"],
            "extensions": [".py", ".pyw", ".pyi"],
            "priority": 1,
        },
        "javascript": {
            "files": ["package.json", "yarn.lock", "package-lock.json"],
            "extensions": [".js", ".jsx", ".mjs", ".cjs"],
            "priority": 2,
        },
        "typescript": {
            "files": ["tsconfig.json", "tslint.json"],
            "extensions": [".ts", ".tsx"],
            "priority": 1,  # Higher priority than JS if TS files exist
        },
        "java": {
            "files": ["pom.xml", "build.gradle", "build.gradle.kts"],
            "extensions": [".java"],
            "priority": 2,
        },
        "go": {
            "files": ["go.mod", "go.sum"],
            "extensions": [".go"],
            "priority": 2,
        },
        "rust": {
            "files": ["Cargo.toml", "Cargo.lock"],
            "extensions": [".rs"],
            "priority": 2,
        },
    }

    def __init__(self, workspace_root: Path):
        """Initialize language detector

        Args:
            workspace_root: Root directory of the workspace
        """
        self.workspace_root = workspace_root
        self._cache: Optional[str] = None

    def detect(self, use_cache: bool = True) -> str:
        """Detect the primary language of the project

        Args:
            use_cache: Whether to use cached result

        Returns:
            Detected language name
        """
        # Return cached result if available
        if use_cache and self._cache:
            return self._cache

        # Multi-stage detection for accuracy
        detected = self._detect_by_config_files() or self._detect_by_file_count()

        # Cache and return result
        self._cache = detected
        return detected

    def _detect_by_config_files(self) -> Optional[str]:
        """Detect language by configuration files"""
        detected_languages: List[tuple[str, int]] = []
        for language, config_any in self.LANGUAGE_INDICATORS.items():
            config: Dict[str, Any] = config_any  # type: ignore
            files: list = config["files"]
            for file_name in files:
                file_path = self.workspace_root / file_name
                if file_path.exists():
                    if file_name == "package.json":
                        lang = self._analyze_package_json(file_path)
                        detected_languages.append((str(lang), int(config["priority"])))
                    else:
                        detected_languages.append((str(language), int(config["priority"])))
                    break

        # Return highest priority language
        if detected_languages:
            detected_languages.sort(key=lambda x: x[1])
            return detected_languages[0][0]

        return None

    def _analyze_package_json(self, package_json_path: Path) -> str:
        """Analyze package.json to distinguish between JS and TS"""
        try:
            with open(package_json_path, "r", encoding="utf-8") as f:
                package_data = json.load(f)
            ts_indicators = [
                "typescript" in package_data.get("devDependencies", {}),
                "typescript" in package_data.get("dependencies", {}),
                "@types/" in str(package_data.get("devDependencies", {})),
                (self.workspace_root / "tsconfig.json").exists(),
            ]
            return "typescript" if any(ts_indicators) else "javascript"
        except (OSError, IOError, json.JSONDecodeError, UnicodeDecodeError, ValueError) as e:
            logger.warning("Failed to analyze package.json: %s", e)
            return "javascript"

    def _detect_by_file_count(self) -> str:
        """Detect language by counting source files"""
        try:
            file_counts: Dict[str, int] = {}

            # Count files with language-specific extensions
            for language, config_any in self.LANGUAGE_INDICATORS.items():
                config: Dict[str, Any] = config_any  # type: ignore
                count = 0
                extensions: list = config["extensions"]
                for ext in extensions:
                    count += len(list(self.workspace_root.rglob(f"*{ext}")))

                if count > 0:
                    file_counts[language] = count

            # Return language with most files
            if file_counts:
                return max(file_counts, key=lambda k: file_counts[k])

        except (OSError, IOError, ValueError) as e:
            logger.warning("File count detection failed: %s", e)

        # Fallback to Python
        return "python"

    def get_supported_languages(self) -> List[str]:
        """Get list of supported languages"""
        return list(self.LANGUAGE_INDICATORS.keys())

    def is_language_supported(self, language: str) -> bool:
        """Check if a language is supported"""
        return language in self.LANGUAGE_INDICATORS

    def get_language_info(self, language: str) -> Dict[str, Any]:
        """Get information about a specific language"""
        if language not in self.LANGUAGE_INDICATORS:
            return {"error": f"Unsupported language: {language}"}

        config = self.LANGUAGE_INDICATORS[language]
        return {
            "language": language,
            "indicator_files": config["files"],
            "extensions": config["extensions"],
            "priority": config["priority"],
            "supported": True,
        }

    def clear_cache(self) -> None:
        """Clear the language detection cache"""
        self._cache = None
