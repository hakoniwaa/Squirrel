"""
Intelligent Query Processing
Query understanding, expansion, and intent detection for better search
"""

import logging
import re
from typing import Any, Dict, List, Optional, Set

logger = logging.getLogger(__name__)


class QueryProcessor:
    """Intelligent query understanding and expansion"""

    def __init__(self):
        self.synonym_map = self._load_programming_synonyms()
        self.abbreviation_map = self._load_common_abbreviations()
        self.language_keywords = self._load_language_keywords()

    async def process_query(self, query: str) -> Dict[str, Any]:
        """Process and enhance search query"""

        # 1. Detect query intent
        intent = self._detect_intent(query)

        # 2. Extract entities (function names, variables, etc.)
        entities = self._extract_code_entities(query)

        # 3. Expand abbreviations
        expanded_query = self._expand_abbreviations(query)

        # 4. Generate synonyms and related terms
        synonyms = self._get_synonyms(expanded_query)

        # 5. Detect programming language context
        language_hint = self._detect_language_context(query)

        # 6. Generate sub-queries for different aspects
        sub_queries = self._generate_sub_queries(query, intent)

        # 7. Extract technical terms
        technical_terms = self._extract_technical_terms(query)

        return {
            "original": query,
            "expanded": expanded_query,
            "intent": intent,
            "entities": entities,
            "synonyms": synonyms,
            "language_hint": language_hint,
            "sub_queries": sub_queries,
            "technical_terms": technical_terms,
            "search_strategies": self._recommend_strategies(intent, entities, language_hint),
        }

    def _detect_intent(self, query: str) -> str:
        """Detect search intent: definition, usage, error, implementation, etc."""
        intent_keywords = {
            "definition": ["what is", "define", "meaning", "explain", "description of"],
            "usage": ["how to", "use", "example", "tutorial", "guide", "implement"],
            "error": ["error", "exception", "fix", "debug", "problem", "issue", "bug"],
            "implementation": ["implement", "create", "build", "write", "code"],
            "optimization": ["optimize", "performance", "faster", "improve", "efficient"],
            "comparison": ["vs", "versus", "compare", "difference", "better"],
            "configuration": ["config", "setup", "install", "configure", "settings"],
            "testing": ["test", "testing", "unit test", "mock", "assert"],
            "documentation": ["docs", "documentation", "readme", "api", "reference"],
        }

        query_lower = query.lower()
        intent_scores = {}

        for intent, keywords in intent_keywords.items():
            score = sum(1 for kw in keywords if kw in query_lower)
            if score > 0:
                intent_scores[intent] = score

        if intent_scores:
            return max(intent_scores.items(), key=lambda x: x[1])[0]

        return "general"

    def _extract_code_entities(self, query: str) -> Dict[str, List[str]]:
        """Extract code entities like function names, class names, variables"""
        entities: Dict[str, List[str]] = {
            "functions": [],
            "classes": [],
            "variables": [],
            "modules": [],
            "files": [],
        }

        # Function patterns
        function_patterns = [
            r"\b([a-zA-Z_][a-zA-Z0-9_]*)\s*\(",  # function_name(
            r"\bdef\s+([a-zA-Z_][a-zA-Z0-9_]*)",  # def function_name
            r"\bfunction\s+([a-zA-Z_][a-zA-Z0-9_]*)",  # function function_name
        ]

        for pattern in function_patterns:
            matches = re.findall(pattern, query)
            entities["functions"].extend(matches)

        # Class patterns
        class_patterns = [
            r"\bclass\s+([A-Z][a-zA-Z0-9_]*)",  # class ClassName
            r"\b([A-Z][a-zA-Z0-9_]*)\s*\(",  # ClassName(
        ]

        for pattern in class_patterns:
            matches = re.findall(pattern, query)
            entities["classes"].extend(matches)

        # Variable patterns (camelCase, snake_case)
        variable_patterns = [
            r"\b([a-z][a-zA-Z0-9_]*)\b",  # camelCase or snake_case
        ]

        for pattern in variable_patterns:
            matches = re.findall(pattern, query)
            # Filter out common words
            filtered_matches = [m for m in matches if m not in self._get_common_words()]
            entities["variables"].extend(filtered_matches[:5])  # Limit to avoid noise

        # File patterns
        file_patterns = [
            r"\b([a-zA-Z0-9_\-]+\.[a-zA-Z0-9]+)\b",  # filename.ext
            r"\.py|\.js|\.ts|\.java|\.cpp|\.c\b",  # file extensions
        ]

        for pattern in file_patterns:
            matches = re.findall(pattern, query)
            entities["files"].extend(matches)

        # Remove duplicates and empty entries
        for key in entities:
            entities[key] = list(set(filter(None, entities[key])))

        return entities

    def _expand_abbreviations(self, query: str) -> str:
        """Expand common abbreviations"""
        expanded = query

        for abbrev, full_form in self.abbreviation_map.items():
            # Use word boundaries to avoid partial matches
            pattern = r"\b" + re.escape(abbrev) + r"\b"
            expanded = re.sub(pattern, full_form, expanded, flags=re.IGNORECASE)

        return expanded

    def _get_synonyms(self, query: str) -> List[str]:
        """Generate synonyms and related terms"""
        synonyms = []
        words = query.lower().split()

        for word in words:
            if word in self.synonym_map:
                synonyms.extend(self.synonym_map[word])

        # Remove duplicates and original words
        original_words = set(words)
        synonyms = [s for s in set(synonyms) if s not in original_words]

        return synonyms[:10]  # Limit to avoid overwhelming

    def _detect_language_context(self, query: str) -> Optional[str]:
        """Detect programming language context from query"""
        query_lower = query.lower()

        language_scores = {}

        for language, keywords in self.language_keywords.items():
            score = sum(1 for keyword in keywords if keyword in query_lower)
            if score > 0:
                language_scores[language] = score

        if language_scores:
            best_language = max(language_scores.items(), key=lambda x: x[1])[0]
            return str(best_language)

        return None

    def _generate_sub_queries(self, query: str, intent: str) -> List[str]:
        """Generate sub-queries for different aspects"""
        sub_queries = []

        if intent == "definition":
            sub_queries.extend(
                [f"what is {query}", f"{query} explanation", f"{query} documentation"]
            )
        elif intent == "usage":
            sub_queries.extend([f"how to use {query}", f"{query} example", f"{query} tutorial"])
        elif intent == "error":
            sub_queries.extend([f"{query} fix", f"{query} solution", f"{query} troubleshooting"])
        elif intent == "implementation":
            sub_queries.extend(
                [f"implement {query}", f"{query} code example", f"how to build {query}"]
            )

        # Add language-specific sub-queries if language detected
        entities = self._extract_code_entities(query)
        if entities["functions"]:
            for func in entities["functions"][:2]:
                sub_queries.append(f"{func} function")

        if entities["classes"]:
            for cls in entities["classes"][:2]:
                sub_queries.append(f"{cls} class")

        return sub_queries[:5]  # Limit number of sub-queries

    def _extract_technical_terms(self, query: str) -> List[str]:
        """Extract technical terms and concepts"""
        technical_patterns = [
            r"\b(API|REST|GraphQL|JSON|XML|HTTP|HTTPS|SQL|NoSQL)\b",
            r"\b(async|await|promise|callback|closure|decorator)\b",
            r"\b(database|cache|redis|mongodb|postgresql|mysql)\b",
            r"\b(framework|library|package|module|component)\b",
            r"\b(authentication|authorization|security|encryption)\b",
            r"\b(testing|debugging|logging|monitoring|performance)\b",
        ]

        technical_terms = []
        for pattern in technical_patterns:
            matches = re.findall(pattern, query, re.IGNORECASE)
            technical_terms.extend(matches)

        return list(set(technical_terms))

    def _recommend_strategies(
        self, intent: str, entities: Dict[str, List[str]], language_hint: Optional[str]
    ) -> List[str]:
        """Recommend search strategies based on query analysis"""
        strategies = []

        if intent == "definition":
            strategies.append("semantic_first")
        elif intent == "usage" or intent == "implementation":
            strategies.append("hybrid")
        elif intent == "error":
            strategies.append("text_first")
        else:
            strategies.append("adaptive")

        if entities["functions"] or entities["classes"]:
            strategies.append("code_focused")

        if language_hint:
            strategies.append(f"language_specific_{language_hint}")

        return strategies

    def _load_programming_synonyms(self) -> Dict[str, List[str]]:
        """Load programming-related synonyms"""
        return {
            "function": ["method", "procedure", "routine", "subroutine"],
            "variable": ["var", "parameter", "argument", "field", "property"],
            "class": ["object", "type", "struct", "interface"],
            "error": ["exception", "bug", "issue", "problem", "failure"],
            "fix": ["solve", "resolve", "repair", "correct", "debug"],
            "create": ["make", "build", "generate", "construct", "implement"],
            "use": ["utilize", "employ", "apply", "invoke", "call"],
            "test": ["check", "verify", "validate", "assert", "mock"],
            "data": ["information", "content", "payload", "input", "output"],
            "code": ["source", "script", "program", "implementation"],
            "file": ["document", "script", "module", "component"],
            "database": ["db", "store", "repository", "storage"],
            "server": ["backend", "service", "api", "endpoint"],
            "client": ["frontend", "ui", "interface", "app"],
            "config": ["configuration", "settings", "options", "parameters"],
            "install": ["setup", "configure", "initialize", "deploy"],
            "update": ["upgrade", "modify", "change", "edit"],
            "delete": ["remove", "destroy", "clear", "drop"],
            "search": ["find", "lookup", "query", "filter"],
            "sort": ["order", "arrange", "organize", "rank"],
            "connect": ["link", "join", "attach", "bind"],
            "async": ["asynchronous", "concurrent", "parallel", "non-blocking"],
            "sync": ["synchronous", "blocking", "sequential"],
        }

    def _load_common_abbreviations(self) -> Dict[str, str]:
        """Load common programming abbreviations"""
        return {
            "js": "javascript",
            "ts": "typescript",
            "py": "python",
            "db": "database",
            "api": "application programming interface",
            "ui": "user interface",
            "ux": "user experience",
            "css": "cascading style sheets",
            "html": "hypertext markup language",
            "http": "hypertext transfer protocol",
            "url": "uniform resource locator",
            "json": "javascript object notation",
            "xml": "extensible markup language",
            "sql": "structured query language",
            "crud": "create read update delete",
            "mvc": "model view controller",
            "orm": "object relational mapping",
            "jwt": "json web token",
            "rest": "representational state transfer",
            "soap": "simple object access protocol",
            "tcp": "transmission control protocol",
            "udp": "user datagram protocol",
            "dns": "domain name system",
            "ssl": "secure sockets layer",
            "tls": "transport layer security",
            "ssh": "secure shell",
            "ftp": "file transfer protocol",
            "smtp": "simple mail transfer protocol",
            "ide": "integrated development environment",
            "cli": "command line interface",
            "gui": "graphical user interface",
            "os": "operating system",
            "vm": "virtual machine",
            "ci": "continuous integration",
            "cd": "continuous deployment",
            "qa": "quality assurance",
            "tdd": "test driven development",
            "bdd": "behavior driven development",
        }

    def _load_language_keywords(self) -> Dict[str, List[str]]:
        """Load programming language specific keywords"""
        return {
            "python": [
                "def",
                "class",
                "import",
                "from",
                "pip",
                "django",
                "flask",
                "pandas",
                "numpy",
                "python",
            ],
            "javascript": [
                "function",
                "var",
                "let",
                "const",
                "npm",
                "node",
                "react",
                "vue",
                "angular",
                "javascript",
            ],
            "typescript": ["interface", "type", "typescript", "ts", "angular", "nest"],
            "java": [
                "public",
                "private",
                "static",
                "void",
                "class",
                "java",
                "spring",
                "maven",
                "gradle",
            ],
            "csharp": [
                "public",
                "private",
                "static",
                "void",
                "class",
                "namespace",
                "csharp",
                "dotnet",
                ".net",
            ],
            "cpp": ["include", "namespace", "std", "cpp", "c++", "cmake"],
            "c": ["include", "stdio", "stdlib", "main", "gcc"],
            "go": ["func", "package", "import", "golang", "go"],
            "rust": ["fn", "let", "mut", "cargo", "rust"],
            "ruby": ["def", "class", "require", "gem", "rails", "ruby"],
            "php": ["function", "class", "require", "composer", "laravel", "php"],
            "swift": ["func", "var", "let", "class", "swift", "ios"],
            "kotlin": ["fun", "val", "var", "class", "kotlin", "android"],
            "scala": ["def", "val", "var", "class", "object", "scala"],
            "sql": ["select", "insert", "update", "delete", "create", "table", "database"],
        }

    def _get_common_words(self) -> Set[str]:
        """Get set of common English words to filter out"""
        return {
            "the",
            "a",
            "an",
            "and",
            "or",
            "but",
            "in",
            "on",
            "at",
            "to",
            "for",
            "of",
            "with",
            "by",
            "from",
            "as",
            "is",
            "are",
            "was",
            "were",
            "be",
            "been",
            "being",
            "have",
            "has",
            "had",
            "do",
            "does",
            "did",
            "will",
            "would",
            "could",
            "should",
            "may",
            "might",
            "can",
            "this",
            "that",
            "these",
            "those",
            "i",
            "you",
            "he",
            "she",
            "it",
            "we",
            "they",
            "me",
            "him",
            "her",
            "us",
            "them",
            "my",
            "your",
            "his",
            "our",
            "their",
            "what",
            "when",
            "where",
            "why",
            "how",
            "which",
            "who",
            "whom",
        }
