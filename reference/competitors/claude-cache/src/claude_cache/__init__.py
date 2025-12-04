"""Claude Cache - Memory for your AI coding assistant"""

__version__ = "0.9.1"

from .log_watcher import LogWatcher
from .log_processor import LogProcessor
from .success_detector import SuccessDetector
from .knowledge_base import KnowledgeBase
from .context_injector import ContextInjector
from .agent import CacheAgent
from .pattern_factory import PatternDetectorFactory

# Import enhanced modules with graceful fallback
try:
    from .semantic_matcher import SemanticMatcher
    _has_semantic = True
except ImportError:
    _has_semantic = False

try:
    from .meta_pattern_scorer import MetaPatternScorer
    _has_meta_scorer = True
except ImportError:
    _has_meta_scorer = False

try:
    from .extraction_prompts import ExtractionPrompts
    _has_extraction = True
except ImportError:
    _has_extraction = False

# Import new intelligent modules with graceful fallback
try:
    from .behavioral_detector import BehavioralDetector
    _has_behavioral = True
except ImportError:
    _has_behavioral = False

try:
    from .conversation_analyzer import ConversationAnalyzer
    _has_conversation = True
except ImportError:
    _has_conversation = False

try:
    from .intelligent_detector import IntelligentDetector
    _has_intelligent = True
except ImportError:
    _has_intelligent = False

__all__ = [
    "LogWatcher",
    "LogProcessor",
    "SuccessDetector",
    "KnowledgeBase",
    "ContextInjector",
    "CacheAgent",
    "PatternDetectorFactory",
]

# Add enhanced modules if available
if _has_semantic:
    __all__.append("SemanticMatcher")
if _has_meta_scorer:
    __all__.append("MetaPatternScorer")
if _has_extraction:
    __all__.append("ExtractionPrompts")
if _has_behavioral:
    __all__.append("BehavioralDetector")
if _has_conversation:
    __all__.append("ConversationAnalyzer")
if _has_intelligent:
    __all__.append("IntelligentDetector")