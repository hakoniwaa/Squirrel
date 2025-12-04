"""Factory for creating the best available pattern detector based on installed modules"""

from typing import Optional, TYPE_CHECKING
from rich.console import Console

if TYPE_CHECKING:
    from .knowledge_base import KnowledgeBase

console = Console()


class PatternDetectorFactory:
    """Factory for creating the most capable pattern detector available"""

    @staticmethod
    def get_detector(knowledge_base: Optional['KnowledgeBase'] = None):
        """
        Return the best available pattern detector based on installed modules

        Priority order:
        1. IntelligentDetector - Multi-signal fusion with conversation understanding
        2. BehavioralDetector - Smart behavioral analysis
        3. EnhancedDetector - Enhanced features (if available)
        4. BasicDetector - Simple keyword matching (fallback)
        """

        # Try to use the intelligent detector first (best option)
        try:
            from .intelligent_detector import IntelligentDetector
            detector = IntelligentDetector()
            if not (knowledge_base and knowledge_base.silent):
                console.print("[bright_green]🤖 Using Intelligent Multi-Signal Detector[/bright_green]")
            return detector
        except ImportError:
            pass

        # Try the behavioral detector (second best)
        try:
            from .behavioral_detector import BehavioralDetector
            detector = BehavioralDetector()
            if not (knowledge_base and knowledge_base.silent):
                console.print("[green]🧠 Using Smart Behavioral Detector[/green]")
            return detector
        except ImportError:
            pass

        # Check for enhanced features
        try:
            from .enhanced_detector import EnhancedSuccessDetector
            detector = EnhancedSuccessDetector()
            if not (knowledge_base and knowledge_base.silent):
                console.print("[yellow]✨ Using Enhanced Detector[/yellow]")
            return detector
        except ImportError:
            pass

        # Fallback to basic detector
        from .success_detector import SuccessDetector
        detector = SuccessDetector()
        if not (knowledge_base and knowledge_base.silent):
            console.print("[blue]📊 Using Basic Pattern Detector[/blue]")
        return detector

    @staticmethod
    def get_capabilities():
        """Check what pattern detection capabilities are available"""
        capabilities = {
            'basic': True,  # Always available
            'intelligent': False,
            'behavioral': False,
            'semantic': False,
            'meta_scoring': False,
            'enhanced': False,
            'extraction_prompts': False,
            'error_resolution': True,  # Part of basic detector now
            'journey_patterns': True,   # Database tables always created
            'anti_patterns': True,      # Database tables always created
        }

        try:
            from .intelligent_detector import IntelligentDetector
            capabilities['intelligent'] = True
        except ImportError:
            pass

        try:
            from .behavioral_detector import BehavioralDetector
            capabilities['behavioral'] = True
        except ImportError:
            pass

        try:
            from .semantic_matcher import SemanticMatcher
            capabilities['semantic'] = True
        except ImportError:
            pass

        try:
            from .meta_pattern_scorer import MetaPatternScorer
            capabilities['meta_scoring'] = True
        except ImportError:
            pass

        try:
            from .enhanced_detector import EnhancedSuccessDetector
            capabilities['enhanced'] = True
        except ImportError:
            pass

        try:
            from .extraction_prompts import ExtractionPrompts
            capabilities['extraction_prompts'] = True
        except ImportError:
            pass

        return capabilities

    @staticmethod
    def print_capabilities():
        """Print a summary of available pattern detection capabilities"""
        caps = PatternDetectorFactory.get_capabilities()

        console.print("\n[bold cyan]🔍 Pattern Detection Capabilities[/bold cyan]")
        console.print("─" * 40)

        status_icon = lambda enabled: "✅" if enabled else "❌"

        console.print(f"{status_icon(caps['basic'])} Basic Pattern Detection")
        console.print(f"{status_icon(caps['intelligent'])} Intelligent Multi-Signal Detection")
        console.print(f"{status_icon(caps['behavioral'])} Behavioral Pattern Analysis")
        console.print(f"{status_icon(caps['semantic'])} Semantic Similarity Matching")
        console.print(f"{status_icon(caps['meta_scoring'])} Meta-Pattern Scoring")
        console.print(f"{status_icon(caps['enhanced'])} Enhanced Multi-Signal Detection")
        console.print(f"{status_icon(caps['extraction_prompts'])} Structured Extraction Prompts")
        console.print(f"{status_icon(caps['error_resolution'])} Error→Success Resolution Tracking")
        console.print(f"{status_icon(caps['journey_patterns'])} Journey Pattern Detection")
        console.print(f"{status_icon(caps['anti_patterns'])} Anti-Pattern Learning")

        # Provide recommendations
        if not caps['semantic']:
            console.print("\n[yellow]💡 Tip: Install enhanced features with:[/yellow]")
            console.print("    [cyan]pip install sentence-transformers[/cyan]")
            console.print("    This enables semantic understanding for 2x better pattern matching")

        return caps