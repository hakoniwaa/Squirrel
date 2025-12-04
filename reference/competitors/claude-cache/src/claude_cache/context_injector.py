"""Inject context and generate slash commands for Claude Code"""

import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
from rich.console import Console
from rich.markdown import Markdown

console = Console()


class ContextInjector:
    """Generate context and slash commands from knowledge base"""

    # Maximum size for CLAUDE.md file (in characters)
    MAX_CONTEXT_SIZE = 50000  # ~50KB, reasonable for Claude to read
    MAX_LESSONS_PER_DOC = 5
    MAX_PATTERNS_IN_CONTEXT = 10
    MAX_DOCS_IN_CONTEXT = 5

    def __init__(self, knowledge_base, silent=False):
        self.kb = knowledge_base
        self.commands_dir = Path('.claude/commands')
        self.lessons_dir = Path('.claude/lessons')
        self.silent = silent

    def generate_context_for_request(self, user_request: str, project_name: str) -> Optional[str]:
        """Generate context for a specific request"""
        similar_patterns = self.kb.find_similar_patterns(user_request, project_name)

        if not similar_patterns:
            console.print("[yellow]No similar patterns found[/yellow]")
            return None

        context = self.build_context_prompt(similar_patterns, project_name)

        self.save_as_slash_command(context, 'project-context', project_name)

        return context

    def build_context_prompt(self, patterns: List[Dict], project_name: str) -> str:
        """Build a comprehensive context prompt"""
        context_lines = [
            f"# Project Context: {project_name}",
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            ""
        ]

        # Include manual documentation first
        docs = self.kb.get_documentation_for_context(project_name)
        if docs:
            context_lines.extend([
                "## Project Documentation & Lessons Learned",
                ""
            ])

            for doc in docs:
                import json
                doc_data = json.loads(doc['content'])

                context_lines.append(f"### From: {doc['file_path']}")

                if doc_data.get('lessons_learned'):
                    context_lines.append("\n**Lessons Learned:**")
                    for lesson in doc_data['lessons_learned'][:5]:
                        context_lines.append(f"- {lesson}")

                if doc_data.get('warnings'):
                    context_lines.append("\n**Important Warnings:**")
                    for warning in doc_data['warnings'][:3]:
                        context_lines.append(f"⚠️  {warning}")

                if doc_data.get('best_practices'):
                    context_lines.append("\n**Best Practices:**")
                    for practice in doc_data['best_practices'][:3]:
                        context_lines.append(f"✓ {practice}")

                context_lines.append("")

        context_lines.extend([
            "## Relevant Successful Patterns",
            ""
        ])

        for i, pattern in enumerate(patterns, 1):
            similarity = pattern['similarity']
            context_lines.extend([
                f"### Pattern {i} (Similarity: {similarity:.1%})",
                "",
                f"**Previous Request:**",
                f"> {pattern['request']}",
                "",
                f"**Approach:** {pattern['approach']}",
                ""
            ])

            if pattern['solution_steps']:
                context_lines.append("**Solution Steps:**")
                for step in pattern['solution_steps'][:3]:
                    context_lines.append(f"- {step.get('action', 'Step')}")
                context_lines.append("")

            if pattern['files_involved']:
                context_lines.append("**Files Involved:**")
                for file in pattern['files_involved'][:5]:
                    context_lines.append(f"- `{Path(file).name}`")
                context_lines.append("")

            if pattern['key_operations']:
                context_lines.append("**Key Operations:**")
                for op in pattern['key_operations'][:3]:
                    tool = op.get('tool', 'Unknown')
                    if op.get('file'):
                        context_lines.append(f"- {tool}: `{Path(op['file']).name}`")
                    else:
                        context_lines.append(f"- {tool}")
                context_lines.append("")

        context_lines.extend([
            "## Recommendations",
            "",
            "Based on previous successful sessions:",
            "1. Consider using the same approach that worked before",
            "2. Check the files that were previously involved",
            "3. Follow similar solution steps adapted to current context",
            ""
        ])

        return '\n'.join(context_lines)

    def save_as_slash_command(self, content: str, command_name: str, project_name: str):
        """Save content as a Claude Code slash command"""
        self.commands_dir.mkdir(parents=True, exist_ok=True)

        command_file = self.commands_dir / f"{command_name}.md"

        header = f"""# {command_name.replace('-', ' ').title()}

Load relevant context for: $ARGUMENTS

---

"""

        with open(command_file, 'w') as f:
            f.write(header + content)

        if not self.silent:
            console.print(f"[green]✓ Saved command: /{command_name}[/green]")

    def generate_all_commands(self, project_name: str):
        """Generate all useful slash commands for a project"""
        stats = self.kb.get_statistics(project_name)

        if stats.get('patterns', 0) == 0:
            if not self.silent:
                console.print("[yellow]No patterns found for project[/yellow]")
            return

        self._generate_best_practices_command(project_name)
        self._generate_conventions_command(project_name)
        self._generate_quick_reference_command(project_name)
        self._generate_debug_helper_command(project_name)

        if not self.silent:
            console.print(f"[green]✓ Generated all commands for {project_name}[/green]")

    def _generate_best_practices_command(self, project_name: str):
        """Generate best practices command"""
        conn = self.kb.db_path
        import sqlite3
        conn = sqlite3.connect(self.kb.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT approach, COUNT(*) as count, AVG(success_score) as avg_score
            FROM success_patterns
            WHERE project_name = ?
            GROUP BY approach
            ORDER BY avg_score DESC, count DESC
            LIMIT 10
        ''', (project_name,))

        approaches = cursor.fetchall()
        conn.close()

        if not approaches:
            return

        content_lines = [
            f"# Best Practices for {project_name}",
            "",
            "## Most Successful Approaches",
            ""
        ]

        for approach, count, score in approaches:
            content_lines.append(f"- **{approach}**: Used {count} times (Success: {score:.1%})")

        content_lines.extend([
            "",
            "## Usage Tips",
            "",
            "1. Start with exploration if unfamiliar with the codebase",
            "2. Test changes incrementally",
            "3. Review similar successful patterns before starting",
            ""
        ])

        self.save_as_slash_command('\n'.join(content_lines), 'best-practices', project_name)

    def _generate_conventions_command(self, project_name: str):
        """Generate project conventions command"""
        conventions = self.kb.get_project_conventions(project_name)

        if not conventions:
            return

        content_lines = [
            f"# Project Conventions for {project_name}",
            "",
            "## Detected Patterns",
            ""
        ]

        by_type = {}
        for conv in conventions:
            conv_type = conv['type']
            if conv_type not in by_type:
                by_type[conv_type] = []
            by_type[conv_type].append(conv)

        for conv_type, items in by_type.items():
            content_lines.append(f"### {conv_type.replace('_', ' ').title()}")
            content_lines.append("")

            for item in items[:5]:
                content_lines.append(f"- {item['pattern']}")
                if item['description']:
                    content_lines.append(f"  {item['description']}")

            content_lines.append("")

        self.save_as_slash_command('\n'.join(content_lines), 'conventions', project_name)

    def _generate_quick_reference_command(self, project_name: str):
        """Generate quick reference command"""
        import sqlite3
        conn = sqlite3.connect(self.kb.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT files_involved
            FROM success_patterns
            WHERE project_name = ?
        ''', (project_name,))

        all_files = []
        for row in cursor.fetchall():
            if row[0]:
                files = json.loads(row[0])
                all_files.extend(files)

        from collections import Counter
        file_counts = Counter(all_files)
        common_files = file_counts.most_common(10)

        cursor.execute('''
            SELECT tool, COUNT(*) as count
            FROM tool_usage
            WHERE project_name = ? AND success = 1
            GROUP BY tool
            ORDER BY count DESC
            LIMIT 10
        ''', (project_name,))

        common_tools = cursor.fetchall()
        conn.close()

        content_lines = [
            f"# Quick Reference for {project_name}",
            "",
            "## Most Modified Files",
            ""
        ]

        for file_path, count in common_files:
            file_name = Path(file_path).name
            content_lines.append(f"- `{file_name}` ({count} times)")

        content_lines.extend([
            "",
            "## Most Used Tools",
            ""
        ])

        for tool, count in common_tools:
            content_lines.append(f"- **{tool}**: {count} uses")

        self.save_as_slash_command('\n'.join(content_lines), 'quick-ref', project_name)

    def _generate_debug_helper_command(self, project_name: str):
        """Generate debugging helper command"""
        import sqlite3
        conn = sqlite3.connect(self.kb.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT user_request, solution_steps
            FROM success_patterns
            WHERE project_name = ? AND request_type = 'debugging'
            ORDER BY success_score DESC
            LIMIT 5
        ''', (project_name,))

        debug_patterns = cursor.fetchall()
        conn.close()

        if not debug_patterns:
            return

        content_lines = [
            f"# Debug Helper for {project_name}",
            "",
            "## Previous Debugging Solutions",
            ""
        ]

        for i, (request, steps_json) in enumerate(debug_patterns, 1):
            content_lines.extend([
                f"### Debug Case {i}",
                "",
                f"**Issue:** {request[:100]}",
                ""
            ])

            if steps_json:
                steps = json.loads(steps_json)
                if steps:
                    content_lines.append("**Solution:**")
                    for step in steps[:3]:
                        content_lines.append(f"- {step.get('action', 'Step')}")
                    content_lines.append("")

        content_lines.extend([
            "## Debug Checklist",
            "",
            "1. Check error messages and stack traces",
            "2. Review recent changes to affected files",
            "3. Verify dependencies and imports",
            "4. Test with minimal reproduction case",
            "5. Check similar patterns above",
            ""
        ])

        self.save_as_slash_command('\n'.join(content_lines), 'debug-helper', project_name)

    def export_commands_to_claude_md(self, project_name: str):
        """Export patterns to a CLAUDE.md file with smart length management"""
        # Use the new lesson organizer for better structure
        from .lesson_organizer import LessonOrganizer

        organizer = LessonOrganizer(self.kb)

        # Organize lessons into categories
        categorized_lessons = organizer.organize_lessons_by_category(project_name)

        # The organizer creates the main CLAUDE.md with intelligent references
        # So we just need to add recent patterns to it
        self._append_recent_patterns_to_index(project_name)

        return

    def export_commands_to_claude_md_old(self, project_name: str):
        """Legacy export method - kept for reference"""
        # Include both auto-learned patterns and manual documentation
        claude_md_path = Path('.claude') / 'CLAUDE.md'
        claude_md_path.parent.mkdir(exist_ok=True)

        stats = self.kb.get_statistics(project_name)
        patterns = self.kb.find_similar_patterns('', project_name)[:self.MAX_PATTERNS_IN_CONTEXT]

        content_lines = [
            f"# Claude Code Knowledge Base for {project_name}",
            "",
            f"*Auto-generated from {stats.get('patterns', 0)} successful patterns*",
            ""
        ]

        # Add manual documentation section first (prioritized)
        docs = self.kb.get_documentation_for_context(project_name)
        if docs:
            content_lines.extend([
                "## 📚 Project Documentation & Lessons Learned",
                "",
                "*From your existing documentation files:*",
                ""
            ])

            # Limit to MAX_DOCS_IN_CONTEXT most relevant docs
            for doc in docs[:self.MAX_DOCS_IN_CONTEXT]:
                import json
                doc_data = json.loads(doc['content'])

                content_lines.append(f"### {doc['file_path']}")

                # Prioritize warnings first (most important)
                if doc_data.get('warnings'):
                    content_lines.append("\n**⚠️  Critical Warnings:**")
                    for warning in doc_data['warnings'][:3]:
                        # Truncate long warnings
                        warning_text = warning[:200] + "..." if len(warning) > 200 else warning
                        content_lines.append(f"- {warning_text}")

                # Then lessons learned
                if doc_data.get('lessons_learned'):
                    content_lines.append("\n**Key Lessons:**")
                    for lesson in doc_data['lessons_learned'][:self.MAX_LESSONS_PER_DOC]:
                        lesson_text = lesson[:150] + "..." if len(lesson) > 150 else lesson
                        content_lines.append(f"- {lesson_text}")

                # Best practices last
                if doc_data.get('best_practices'):
                    content_lines.append("\n**Best Practices:**")
                    for practice in doc_data['best_practices'][:2]:
                        practice_text = practice[:150] + "..." if len(practice) > 150 else practice
                        content_lines.append(f"✓ {practice_text}")

                content_lines.append("")

                # Check if we're approaching size limit
                current_size = len('\n'.join(content_lines))
                if current_size > self.MAX_CONTEXT_SIZE * 0.4:  # Use 40% for docs
                    content_lines.append("*[Additional documentation truncated for size...]*")
                    break

        content_lines.extend([
            "## Project Overview",
            "",
            f"- Total Patterns: {stats.get('patterns', 0)}",
            f"- Conventions: {stats.get('conventions', 0)}",
            f"- Analyzed Requests: {stats.get('requests', 0)}",
            f"- Documentation Files: {len(docs) if docs else 0}",
            "",
            "## Key Success Patterns",
            ""
        ])

        # Add patterns with size management
        patterns_added = 0
        for i, pattern in enumerate(patterns, 1):
            # Check current size before adding more patterns
            current_size = len('\n'.join(content_lines))
            if current_size > self.MAX_CONTEXT_SIZE * 0.8:  # Leave 20% buffer
                content_lines.append(f"*[{len(patterns) - patterns_added} additional patterns available via slash commands]*")
                break

            content_lines.extend([
                f"### Pattern {i}",
                f"- **Request:** {pattern['request'][:100]}...",
                f"- **Approach:** {pattern['approach'][:80]}",
                f"- **Success Score:** {pattern['success_score']:.1%}",
                ""
            ])
            patterns_added += 1

            if patterns_added >= 5:  # Limit to top 5 patterns in main context
                break

        content_lines.extend([
            "## Usage",
            "",
            "This knowledge base is automatically maintained by Claude Cache.",
            "Use slash commands to access specific patterns:",
            "",
            "- `/project-context [task]` - Get relevant patterns for a task",
            "- `/best-practices` - Show successful approaches",
            "- `/conventions` - Show project conventions",
            "- `/quick-ref` - Quick reference for files and tools",
            "- `/debug-helper` - Debugging assistance",
            ""
        ])

        # Final size check and write
        final_content = '\n'.join(content_lines)

        if len(final_content) > self.MAX_CONTEXT_SIZE:
            # Truncate and add notice
            final_content = final_content[:self.MAX_CONTEXT_SIZE - 200]
            final_content += "\n\n---\n*[Content truncated. Use slash commands for full access to patterns]*"

            # Create overflow file for additional patterns
            overflow_path = claude_md_path.parent / 'CLAUDE_EXTENDED.md'
            self._create_overflow_document(overflow_path, patterns[5:], project_name)

        with open(claude_md_path, 'w') as f:
            f.write(final_content)

        console.print(f"[green]✓ Exported to {claude_md_path}[/green]")

        if len(final_content) > self.MAX_CONTEXT_SIZE * 0.9:
            console.print(f"[yellow]Note: Document approaching size limit. Older patterns moved to slash commands.[/yellow]")

    def _create_overflow_document(self, path: Path, patterns: List[Dict], project_name: str):
        """Create overflow document for patterns that don't fit in main CLAUDE.md"""
        content_lines = [
            f"# Extended Patterns for {project_name}",
            "",
            "*Additional patterns that don't fit in the main context file*",
            "",
            "Access these via slash commands:",
            "- `/project-context [task]` - Search all patterns",
            "- `/best-practices` - View successful approaches",
            ""
        ]

        for i, pattern in enumerate(patterns[:20], 6):  # Continue numbering from 6
            content_lines.extend([
                f"### Pattern {i}",
                f"- **Request:** {pattern['request'][:100]}",
                f"- **Success Score:** {pattern['success_score']:.1%}",
                ""
            ])

        with open(path, 'w') as f:
            f.write('\n'.join(content_lines))

    def _append_recent_patterns_to_index(self, project_name: str):
        """Append most recent successful patterns to the main index"""
        claude_md_path = Path('.claude') / 'CLAUDE.md'

        if not claude_md_path.exists():
            return

        # Get recent high-success patterns
        patterns = self.kb.find_similar_patterns('', project_name)
        recent_wins = [p for p in patterns[:5] if p.get('success_score', 0) > 0.85]

        if not recent_wins:
            return

        # Read existing content
        with open(claude_md_path, 'r') as f:
            content = f.read()

        # Find where to insert recent patterns (before the statistics section)
        insert_marker = "## 📊 Knowledge Statistics"
        if insert_marker not in content:
            insert_marker = "## 🔄 Auto-Learning Active"

        if insert_marker in content:
            parts = content.split(insert_marker)

            recent_section = [
                "",
                "## 🎯 Recent Successful Patterns",
                "",
                "*Most recent wins from your coding sessions:*",
                ""
            ]

            for i, pattern in enumerate(recent_wins[:3], 1):
                recent_section.extend([
                    f"{i}. **{pattern['request'][:60]}...**",
                    f"   - Approach: {pattern['approach'][:80]}",
                    f"   - Success: {pattern['success_score']:.0%}",
                    ""
                ])

            # Reassemble content
            new_content = parts[0] + '\n'.join(recent_section) + "\n" + insert_marker + parts[1]

            # Keep under size limit
            if len(new_content) > 35000:
                # Trim from the middle sections
                new_content = new_content[:34000] + "\n\n*[Content optimized for size]*\n" + insert_marker + parts[1]

            with open(claude_md_path, 'w') as f:
                f.write(new_content)