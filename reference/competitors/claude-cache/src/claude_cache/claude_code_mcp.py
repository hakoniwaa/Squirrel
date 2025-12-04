#!/usr/bin/env python3
"""
MCP Server optimized specifically for Claude Code.
Provides intelligent, context-aware tools that understand coding workflow.
"""

import sys
import os
import logging
import json
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime
import hashlib

# Configure logging to stderr only (stdout corrupts MCP)
logging.basicConfig(level=logging.ERROR, stream=sys.stderr)

# Suppress noisy libraries
import warnings
warnings.filterwarnings("ignore")

# Import with minimal overhead
import contextlib
import io

with contextlib.redirect_stdout(io.StringIO()):
    from mcp.server.fastmcp import FastMCP
    # Import Claude Cache components silently
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))
    from claude_cache.knowledge_base import KnowledgeBase
    from claude_cache.intelligent_detector import IntelligentDetector
    from claude_cache.conversation_analyzer import ConversationAnalyzer

# Initialize server
mcp = FastMCP("cache")

# Initialize components in silent mode
kb = KnowledgeBase(silent=True)
detector = IntelligentDetector()
analyzer = ConversationAnalyzer()

# Session tracking for real-time analysis
current_session = {
    'entries': [],
    'last_analysis': None,
    'auto_saved': False,
    'session_id': None
}


@mcp.tool()
async def cache_query(what: str, smart: bool = True) -> str:
    """
    Intelligently search your coding patterns.

    This tool understands context and finds truly relevant solutions,
    not just keyword matches.

    Args:
        what: Natural language description of what you're looking for
        smart: Use intelligent context-aware search (default: True)

    Examples:
        cache_query("how did I handle auth in React")
        cache_query("that database connection issue from last week")
        cache_query("tests failing", smart=True)
    """
    try:
        # Get current project context
        project = _detect_current_project()

        # If smart search, add context
        if smart and current_session['entries']:
            # Analyze current session for context
            current_context = analyzer.analyze_conversation(current_session['entries'][-5:])
            enhanced_query = f"{what} (context: {current_context.get('problem', '')[:50]})"
        else:
            enhanced_query = what

        # Search with context
        patterns = kb.find_similar_patterns(enhanced_query, project, threshold=0.15)

        if not patterns:
            return f"No patterns found. I'm monitoring this session - when we solve it, I'll save it automatically!"

        # Format results intelligently
        output = [f"🔍 Found {len(patterns)} relevant patterns:\n"]

        for i, p in enumerate(patterns[:3], 1):
            quality = p.get('pattern_quality', 'bronze')
            signal = p.get('signal_strength', 'medium')

            # Choose icon based on quality and relevance
            if quality == 'gold' and p.get('similarity', 0) > 0.8:
                icon = "🎯"  # Perfect match
            elif quality == 'gold':
                icon = "🏆"  # High quality
            elif quality == 'silver':
                icon = "✨"  # Good solution
            elif quality == 'anti':
                icon = "⚠️"  # What not to do
            else:
                icon = "📝"  # Standard pattern

            # Show the pattern with context
            request = p.get('request', 'Pattern')[:80]
            approach = p.get('approach', 'Solution')[:150]
            confidence = p.get('similarity', 0)

            output.append(f"\n{i}. {icon} {request}")
            output.append(f"   Solution: {approach}")
            output.append(f"   Match: {confidence:.0%} | Quality: {quality}")

            # Add insights if available
            if quality == 'anti':
                output.append(f"   ⚠️ Avoid: This approach didn't work")

        # Add contextual suggestion
        if current_session['entries'] and patterns:
            output.append(f"\n💡 Based on your current problem, pattern #{1} seems most relevant")

        return "\n".join(output)

    except Exception as e:
        return f"Search failed: {str(e)}"


@mcp.tool()
async def cache_analyze() -> str:
    """
    Analyze the current conversation for success patterns.

    This shows you what Claude Cache is learning from this session
    and whether it detected a successful solution.

    No arguments needed - analyzes current session automatically.
    """
    try:
        if not current_session['entries']:
            return "No session data yet. I'm monitoring the conversation..."

        # Perform intelligent analysis
        result = detector.detect(current_session['entries'])

        # Format analysis results
        output = ["📊 Current Session Analysis:\n"]

        # Success detection
        if result.is_success:
            output.append(f"✅ Success Detected! (Confidence: {result.confidence.value})")
        else:
            output.append(f"⏳ No clear success yet (Probability: {result.success_probability:.0%})")

        # Problem and solution
        if result.problem:
            output.append(f"\n🎯 Problem: {result.problem[:100]}")
        if result.solution and result.is_success:
            output.append(f"💡 Solution: {result.solution[:150]}")

        # Key insights
        if result.key_insights:
            output.append("\n🔍 Key Insights:")
            for insight in result.key_insights[:3]:
                output.append(f"   • {insight}")

        # Quality assessment
        if result.pattern_quality != 'unknown':
            quality_emoji = {
                'gold': '🏆',
                'silver': '✨',
                'bronze': '🥉',
                'anti': '⚠️'
            }.get(result.pattern_quality, '📝')
            output.append(f"\n{quality_emoji} Pattern Quality: {result.pattern_quality}")

        # Recommendation
        output.append(f"\n💭 {result.recommendation}")

        # Auto-save status
        if current_session['auto_saved']:
            output.append("\n✅ Already auto-saved this pattern!")
        elif result.is_success and result.confidence.value in ['certain', 'high']:
            output.append("\n💾 Ready to auto-save when you confirm or move on")

        return "\n".join(output)

    except Exception as e:
        return f"Analysis failed: {str(e)}"


@mcp.tool()
async def cache_save(confirm: bool = True) -> str:
    """
    Save the current solution to your knowledge base.

    Called automatically when high confidence success is detected,
    or manually when you want to save something.

    Args:
        confirm: Whether to save (default: True, set False to skip)

    Examples:
        cache_save()  # Save current solution
        cache_save(False)  # Don't save this one
    """
    try:
        if not confirm:
            current_session['auto_saved'] = True  # Mark to prevent re-asking
            return "Skipped saving this pattern."

        if not current_session['entries']:
            return "No session to save yet."

        if current_session['auto_saved']:
            return "This pattern was already saved!"

        # Analyze session
        result = detector.detect(current_session['entries'])

        if not result.is_success and result.pattern_quality != 'anti':
            return "No clear pattern to save yet. Let me know when something works!"

        # Prepare pattern data
        project = _detect_current_project()

        pattern_data = {
            'user_request': result.problem,
            'approach': result.solution,
            'solution_steps': result.key_insights,
            'pattern_quality': result.pattern_quality,
            'signal_strength': result.confidence.value,
            'tags': _extract_tags_from_session(),
            'files_involved': _extract_files_from_session()
        }

        # Store the pattern
        kb.store_success_pattern(
            pattern_data,
            project,
            success_score=result.success_probability
        )

        # Store anti-patterns separately
        if result.pattern_quality == 'anti':
            kb.store_anti_pattern({
                'project_name': project,
                'problem': result.problem,
                'failed_approach': result.solution,
                'error_reason': ', '.join(result.key_insights[:2]),
                'context': json.dumps(result.evidence)
            })
            emoji = "⚠️"
            message = "Anti-pattern saved - I'll remember not to do this!"
        else:
            emoji = "🏆" if result.pattern_quality == 'gold' else "✅"
            message = f"Pattern saved successfully! Quality: {result.pattern_quality}"

        current_session['auto_saved'] = True

        return f"{emoji} {message}\nThis will help next time you face a similar problem."

    except Exception as e:
        return f"Save failed: {str(e)}"


@mcp.tool()
async def cache_track(entry: Dict[str, Any]) -> str:
    """
    Track conversation entries for real-time analysis.

    This is called automatically by Claude Code to feed conversation
    data for intelligent pattern detection.

    Args:
        entry: Conversation entry (message, tool call, etc.)

    Note: This is typically called automatically, not manually.
    """
    try:
        # Add to current session
        current_session['entries'].append(entry)

        # Generate session ID if needed
        if not current_session['session_id']:
            current_session['session_id'] = hashlib.md5(
                str(datetime.now()).encode()
            ).hexdigest()[:8]

        # Limit session size (keep last 100 entries)
        if len(current_session['entries']) > 100:
            current_session['entries'] = current_session['entries'][-100:]

        # Check for auto-save triggers
        if not current_session['auto_saved']:
            # Quick analysis for auto-save
            if len(current_session['entries']) >= 5:
                result = detector.detect(current_session['entries'])

                # Auto-save on high confidence success
                if (result.is_success and
                    result.confidence.value in ['certain', 'high'] and
                    _should_auto_save(entry)):

                    # Trigger auto-save
                    await cache_save(confirm=True)
                    return "✅ Auto-saved successful pattern!"

        return "tracked"

    except Exception:
        return "tracking_error"


@mcp.tool()
async def cache_suggest() -> str:
    """
    Get intelligent suggestions based on current context.

    Analyzes what you're working on and suggests relevant patterns
    or warns about potential issues.
    """
    try:
        if not current_session['entries']:
            # No current context, show recent patterns
            patterns = kb.get_project_patterns(_detect_current_project(), limit=3)

            if not patterns:
                return "💡 No patterns yet. I'll learn as we work together!"

            output = ["💡 Recent patterns from this project:\n"]
            for p in patterns:
                output.append(f"• {p.get('approach', '')[:80]}")

            return "\n".join(output)

        # Analyze current context
        analysis = analyzer.analyze_conversation(current_session['entries'])

        # Find relevant patterns
        if analysis['problem']:
            patterns = kb.find_similar_patterns(
                analysis['problem'],
                _detect_current_project(),
                threshold=0.3
            )

            if patterns:
                output = [f"💡 Based on current problem: '{analysis['problem'][:50]}':\n"]

                # Warn about anti-patterns
                anti_patterns = [p for p in patterns if p.get('pattern_quality') == 'anti']
                if anti_patterns:
                    output.append("⚠️ Avoid these approaches:")
                    for p in anti_patterns[:2]:
                        output.append(f"   • {p.get('approach', '')[:60]}")
                    output.append("")

                # Suggest good patterns
                good_patterns = [p for p in patterns if p.get('pattern_quality') != 'anti']
                if good_patterns:
                    output.append("✅ Try these approaches:")
                    for p in good_patterns[:2]:
                        output.append(f"   • {p.get('approach', '')[:80]}")

                return "\n".join(output)

        # Provide phase-specific suggestions
        phase = analysis.get('conversation_phase', 'unknown')
        if phase == 'testing':
            return "💡 In testing phase - I'll save the pattern if tests pass!"
        elif phase == 'implementation':
            return "💡 Implementing solution - I'm tracking what works..."
        else:
            return "💡 I'm analyzing the conversation - will detect patterns automatically!"

    except Exception as e:
        return f"Suggestion failed: {str(e)}"


@mcp.tool()
async def cache_stats() -> str:
    """
    Quick overview of your knowledge base.

    Shows how much Claude Cache has learned and what it knows.
    """
    try:
        import sqlite3
        conn = sqlite3.connect(kb.db_path)
        cursor = conn.cursor()

        # Get statistics
        cursor.execute("SELECT COUNT(*) FROM success_patterns")
        total_patterns = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM success_patterns WHERE pattern_quality = 'gold'")
        gold_patterns = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM anti_patterns")
        anti_patterns = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(DISTINCT project_name) FROM success_patterns")
        projects = cursor.fetchone()[0]

        # Get quality distribution
        cursor.execute("""
            SELECT pattern_quality, COUNT(*)
            FROM success_patterns
            WHERE pattern_quality IS NOT NULL
            GROUP BY pattern_quality
        """)
        quality_dist = dict(cursor.fetchall())

        conn.close()

        # Format output
        output = ["📊 Claude Cache Intelligence Stats:\n"]
        output.append(f"🧠 Total Patterns: {total_patterns}")
        output.append(f"🏆 Gold Patterns: {gold_patterns}")
        output.append(f"⚠️ Anti-patterns: {anti_patterns}")
        output.append(f"📁 Projects: {projects}")

        if quality_dist:
            output.append("\n📈 Quality Distribution:")
            for quality, count in quality_dist.items():
                emoji = {'gold': '🏆', 'silver': '✨', 'bronze': '🥉'}.get(quality, '📝')
                output.append(f"   {emoji} {quality}: {count}")

        # Add search capabilities info
        output.append("\n🔍 Search Capabilities:")
        if kb.vector_search:
            caps = kb.vector_search.get_capabilities()
            if caps['mode'] == 'semantic':
                output.append("   Mode: Semantic Search ✨")
                output.append(f"   Model: {caps['model']}")
                output.append("   Features: Understanding context and meaning")
            else:
                output.append("   Mode: TF-IDF ⚡")
                output.append("   Features: Fast keyword matching")
        else:
            output.append("   Mode: Basic keyword search")

        # Current session status
        if current_session['entries']:
            output.append(f"\n🔄 Current session: {len(current_session['entries'])} entries")
            if current_session['auto_saved']:
                output.append("   ✅ Pattern saved from this session")

        output.append("\n💡 I'm learning from every coding session!")

        return "\n".join(output)

    except Exception as e:
        return f"Stats failed: {str(e)}"


# Helper functions

def _detect_current_project() -> str:
    """Detect current project from working directory"""
    try:
        # First check session context
        if current_session['entries']:
            for entry in current_session['entries']:
                if 'cwd' in entry:
                    path = Path(entry['cwd'])
                    return path.name.lower()

        # Fallback to current directory
        cwd = Path.cwd()
        project = cwd.name.lower()

        # Skip common directories
        if project in ['src', 'lib', 'test']:
            project = cwd.parent.name.lower()

        return project
    except:
        return "default"


def _extract_tags_from_session() -> List[str]:
    """Extract relevant tags from current session"""
    tags = set()

    for entry in current_session['entries']:
        content = str(entry.get('content', '')).lower()

        # Extract technology tags
        tech_keywords = {
            'react': ['react', 'jsx', 'component', 'hooks'],
            'typescript': ['typescript', 'ts', 'type', 'interface'],
            'python': ['python', 'pip', 'django', 'flask'],
            'database': ['sql', 'database', 'query', 'schema'],
            'api': ['api', 'endpoint', 'rest', 'graphql'],
            'testing': ['test', 'jest', 'pytest', 'spec'],
            'auth': ['auth', 'login', 'jwt', 'session']
        }

        for tag, keywords in tech_keywords.items():
            if any(kw in content for kw in keywords):
                tags.add(tag)

    return list(tags)[:5]  # Limit to 5 tags


def _extract_files_from_session() -> List[str]:
    """Extract files involved in the session"""
    files = set()

    for entry in current_session['entries']:
        if entry.get('type') == 'tool_call':
            tool = entry.get('tool', '')
            if tool in ['Edit', 'Write', 'Read']:
                file_path = entry.get('args', {}).get('file_path', '')
                if file_path:
                    files.add(Path(file_path).name)

    return list(files)[:10]  # Limit to 10 files


def _should_auto_save(entry: Dict) -> bool:
    """Determine if we should auto-save based on current entry"""
    # Auto-save triggers
    if entry.get('type') == 'user_message':
        content = str(entry.get('content', '')).lower()

        # User confirms success
        if any(word in content for word in ['perfect', 'thanks', 'that worked']):
            return True

        # User moves to next task
        if any(word in content for word in ['now let', 'next', 'moving on']):
            return True

    return False


def main():
    """Run the MCP server"""
    try:
        mcp.run()
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()