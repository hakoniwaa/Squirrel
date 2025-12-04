"""Organizes lessons into categories and manages hierarchical documentation"""

import json
from pathlib import Path
from typing import Dict, List, Any, Optional
from collections import defaultdict
from datetime import datetime
import hashlib

class LessonOrganizer:
    """Organizes lessons learned into topic-based files for better management"""

    # Configuration for lesson organization
    MAX_LESSONS_PER_PRIORITY = 10  # Max lessons shown per priority level
    MAX_CATEGORIES_IN_INDEX = 8    # Max categories shown in main CLAUDE.md
    MAX_CRITICAL_IN_INDEX = 5      # Max critical warnings in main file
    LESSON_PREVIEW_LENGTH = 200     # Characters to show in lesson preview

    # Categories for organizing lessons
    CATEGORIES = {
        'authentication': ['auth', 'login', 'jwt', 'oauth', 'session', 'password', 'user'],
        'database': ['database', 'sql', 'query', 'migration', 'schema', 'orm', 'postgres', 'mysql'],
        'api': ['api', 'endpoint', 'rest', 'graphql', 'request', 'response', 'http'],
        'frontend': ['component', 'ui', 'react', 'vue', 'css', 'style', 'render', 'dom'],
        'testing': ['test', 'jest', 'pytest', 'mock', 'fixture', 'coverage', 'unit', 'integration'],
        'performance': ['performance', 'optimize', 'speed', 'cache', 'lazy', 'memory', 'cpu'],
        'security': ['security', 'vulnerability', 'xss', 'csrf', 'injection', 'encryption'],
        'deployment': ['deploy', 'docker', 'kubernetes', 'ci', 'cd', 'pipeline', 'build'],
        'debugging': ['debug', 'error', 'exception', 'stack', 'trace', 'log', 'fix', 'bug'],
        'architecture': ['architecture', 'design', 'pattern', 'structure', 'refactor', 'solid']
    }

    def __init__(self, knowledge_base):
        self.kb = knowledge_base
        self.claude_dir = Path('.claude')
        self.lessons_dir = self.claude_dir / 'lessons'

    def organize_lessons_by_category(self, project_name: str):
        """Organize all lessons into category-based files"""
        self.lessons_dir.mkdir(parents=True, exist_ok=True)

        # Get all documentation from knowledge base
        docs = self.kb.get_documentation_for_context(project_name)
        patterns = self.kb.find_similar_patterns('', project_name)

        # Categorize lessons
        categorized_lessons = defaultdict(list)
        uncategorized_lessons = []

        # Process documentation lessons
        for doc in docs:
            doc_data = json.loads(doc['content'])

            for lesson in doc_data.get('lessons_learned', []):
                category = self._categorize_text(lesson)
                lesson_entry = {
                    'lesson': lesson,
                    'source': doc['file_path'],
                    'type': 'documentation',
                    'priority': 'high' if 'critical' in lesson.lower() or 'important' in lesson.lower() else 'medium'
                }

                if category:
                    categorized_lessons[category].append(lesson_entry)
                else:
                    uncategorized_lessons.append(lesson_entry)

            # Add warnings as high-priority lessons
            for warning in doc_data.get('warnings', []):
                category = self._categorize_text(warning)
                warning_entry = {
                    'lesson': f"⚠️ WARNING: {warning}",
                    'source': doc['file_path'],
                    'type': 'warning',
                    'priority': 'critical'
                }

                if category:
                    categorized_lessons[category].append(warning_entry)
                else:
                    categorized_lessons['warnings'].append(warning_entry)

        # Process pattern-based lessons
        for pattern in patterns:
            if pattern.get('success_score', 0) > 0.8:  # High success patterns become lessons
                lesson_text = f"Pattern: {pattern['approach']} works well for {pattern['request'][:50]}"
                category = self._categorize_text(pattern['request'])

                pattern_entry = {
                    'lesson': lesson_text,
                    'source': 'auto-learned',
                    'type': 'pattern',
                    'priority': 'medium',
                    'success_score': pattern['success_score']
                }

                if category:
                    categorized_lessons[category].append(pattern_entry)
                else:
                    uncategorized_lessons.append(pattern_entry)

        # Create category files
        self._create_category_files(categorized_lessons, uncategorized_lessons, project_name)

        # Create the main CLAUDE.md with intelligent references
        self._create_intelligent_index(categorized_lessons, project_name)

        return categorized_lessons

    def _categorize_text(self, text: str) -> Optional[str]:
        """Determine which category a text belongs to"""
        text_lower = text.lower()

        # Score each category based on keyword matches
        category_scores = {}

        for category, keywords in self.CATEGORIES.items():
            score = sum(1 for keyword in keywords if keyword in text_lower)
            if score > 0:
                category_scores[category] = score

        # Return category with highest score
        if category_scores:
            return max(category_scores, key=category_scores.get)

        return None

    def _create_category_files(self, categorized_lessons: Dict, uncategorized: List, project_name: str):
        """Create separate files for each category of lessons"""

        for category, lessons in categorized_lessons.items():
            if not lessons:
                continue

            # Sort lessons by priority
            priority_order = {'critical': 0, 'high': 1, 'medium': 2, 'low': 3}
            lessons.sort(key=lambda x: priority_order.get(x['priority'], 3))

            # Check if we need multiple files (more than 40 lessons per category)
            if len(lessons) > 40:
                self._create_split_category_files(category, lessons, project_name)
            else:
                self._create_single_category_file(category, lessons, project_name)

        # Create uncategorized file if needed
        if uncategorized:
            self._create_uncategorized_file(uncategorized, project_name)

    def _create_single_category_file(self, category: str, lessons: List, project_name: str):
        """Create a single file for a category"""
        file_path = self.lessons_dir / f"{category}_lessons.md"

        content_lines = [
                f"# {category.title()} Lessons - {project_name}",
                f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}*",
                "",
                f"Total lessons: {len(lessons)}",
                ""
            ]

        # Group by priority
        for priority in ['critical', 'high', 'medium', 'low']:
            priority_lessons = [l for l in lessons if l['priority'] == priority]

            if priority_lessons:
                if priority == 'critical':
                    content_lines.append("## 🔴 Critical Issues")
                elif priority == 'high':
                    content_lines.append("## 🟡 Important Lessons")
                else:
                    content_lines.append(f"## {priority.title()} Priority")

                content_lines.append("")

                # Show limited lessons per priority, with overflow handling
                displayed = 0
                for lesson in priority_lessons:
                    if displayed >= self.MAX_LESSONS_PER_PRIORITY:
                        remaining = len(priority_lessons) - displayed
                        content_lines.append(f"\n*... and {remaining} more {priority} priority lessons*")
                        content_lines.append("")
                        break

                    lesson_text = lesson['lesson'][:self.LESSON_PREVIEW_LENGTH]
                    if len(lesson['lesson']) > self.LESSON_PREVIEW_LENGTH:
                        lesson_text += "..."

                    content_lines.append(f"- {lesson_text}")
                    if lesson['source'] != 'auto-learned':
                        content_lines.append(f"  *Source: {lesson['source']}*")
                    content_lines.append("")
                    displayed += 1

        with open(file_path, 'w') as f:
            f.write('\n'.join(content_lines))

    def _create_split_category_files(self, category: str, lessons: List, project_name: str):
        """Create multiple files when a category has too many lessons"""
        # Split lessons into chunks of 40
        chunk_size = 40
        chunks = [lessons[i:i + chunk_size] for i in range(0, len(lessons), chunk_size)]

        for i, chunk in enumerate(chunks, 1):
            if i == 1:
                file_path = self.lessons_dir / f"{category}_lessons.md"
                title = f"# {category.title()} Lessons - {project_name}"
            else:
                file_path = self.lessons_dir / f"{category}_lessons_part{i}.md"
                title = f"# {category.title()} Lessons (Part {i}) - {project_name}"

            content_lines = [
                title,
                f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}*",
                "",
                f"Part {i} of {len(chunks)} - {len(chunk)} lessons in this file",
                ""
            ]

            # Add navigation links
            if i > 1:
                prev_file = f"{category}_lessons.md" if i == 2 else f"{category}_lessons_part{i-1}.md"
                content_lines.append(f"[← Previous Part](./{prev_file})")
            if i < len(chunks):
                next_file = f"{category}_lessons_part{i+1}.md"
                content_lines.append(f"[Next Part →](./{next_file})")
            content_lines.append("")

            # Group by priority for this chunk
            for priority in ['critical', 'high', 'medium', 'low']:
                priority_lessons = [l for l in chunk if l['priority'] == priority]

                if priority_lessons:
                    if priority == 'critical':
                        content_lines.append("## 🔴 Critical Issues")
                    elif priority == 'high':
                        content_lines.append("## 🟡 Important Lessons")
                    else:
                        content_lines.append(f"## {priority.title()} Priority")

                    content_lines.append("")

                    for lesson in priority_lessons:
                        lesson_text = lesson['lesson'][:self.LESSON_PREVIEW_LENGTH]
                        if len(lesson['lesson']) > self.LESSON_PREVIEW_LENGTH:
                            lesson_text += "..."

                        content_lines.append(f"- {lesson_text}")
                        if lesson['source'] != 'auto-learned':
                            content_lines.append(f"  *Source: {lesson['source']}*")
                        content_lines.append("")

            with open(file_path, 'w') as f:
                f.write('\n'.join(content_lines))

    def _create_uncategorized_file(self, lessons: List, project_name: str):
        """Create file for uncategorized lessons"""
        file_path = self.lessons_dir / "general_lessons.md"

        content_lines = [
            f"# General Lessons - {project_name}",
            "",
            "Lessons that don't fit specific categories:",
            ""
        ]

        for lesson in lessons[:30]:
            content_lines.append(f"- {lesson['lesson'][:300]}")
            content_lines.append("")

        with open(file_path, 'w') as f:
            f.write('\n'.join(content_lines))

    def _create_intelligent_index(self, categorized_lessons: Dict, project_name: str):
        """Create main CLAUDE.md with intelligent references to category files"""
        claude_md_path = self.claude_dir / 'CLAUDE.md'

        # Check if CLAUDE.md exists and has user content
        user_content = self._preserve_user_content(claude_md_path)

        # Count total lessons
        total_lessons = sum(len(lessons) for lessons in categorized_lessons.values())

        content_lines = [
            f"# Claude Code Knowledge Base - {project_name}",
            "",
            f"📚 **{total_lessons} lessons organized across {len(categorized_lessons)} categories**",
            "",
            "## 🎯 Quick Access Instructions",
            "",
            "When working on specific areas, check the relevant lesson files:",
            ""
        ]

        # Add category index with smart descriptions
        if categorized_lessons:
            content_lines.append("## 📁 Lesson Categories")
            content_lines.append("")

            # Sort categories by lesson count (most lessons first)
            sorted_categories = sorted(categorized_lessons.items(),
                                      key=lambda x: len(x[1]), reverse=True)

            for category, lessons in sorted_categories[:self.MAX_CATEGORIES_IN_INDEX]:
                critical_count = sum(1 for l in lessons if l['priority'] == 'critical')
                high_count = sum(1 for l in lessons if l['priority'] == 'high')

                # Create smart summary
                if critical_count > 0:
                    priority_note = f" - **{critical_count} CRITICAL**"
                elif high_count > 0:
                    priority_note = f" - {high_count} important"
                else:
                    priority_note = ""

                content_lines.append(
                    f"- **{category.title()}** ({len(lessons)} lessons{priority_note}): "
                    f"`.claude/lessons/{category}_lessons.md`"
                )

                # Add top lesson preview
                if lessons and lessons[0]['priority'] in ['critical', 'high']:
                    preview = lessons[0]['lesson'][:80]
                    content_lines.append(f"  > {preview}...")

            content_lines.append("")

        # Add most critical warnings at the top
        critical_warnings = []
        for lessons in categorized_lessons.values():
            critical_warnings.extend([l for l in lessons if l['priority'] == 'critical'])

        if critical_warnings:
            content_lines.extend([
                "## ⚠️ CRITICAL WARNINGS - READ FIRST",
                "",
                "*These are the most important lessons from your documentation:*",
                ""
            ])

            for warning in critical_warnings[:self.MAX_CRITICAL_IN_INDEX]:
                content_lines.append(f"1. {warning['lesson'][:200]}")

            content_lines.extend([
                "",
                f"*See `.claude/lessons/` for all {len(critical_warnings)} critical items*",
                ""
            ])

        # Add smart search instructions for Claude
        content_lines.extend([
            "## 🤖 Claude Instructions",
            "",
            "When the user asks about a specific topic:",
            "1. Check the relevant category file in `.claude/lessons/`",
            "2. For authentication issues → `.claude/lessons/authentication_lessons.md`",
            "3. For database problems → `.claude/lessons/database_lessons.md`",
            "4. For performance optimization → `.claude/lessons/performance_lessons.md`",
            "5. Always check warnings first if they exist",
            "",
            "## 📊 Knowledge Statistics",
            "",
            f"- Total Lessons: {total_lessons}",
            f"- Categories: {', '.join(sorted(categorized_lessons.keys())[:8])}",
            f"- Last Updated: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            "",
            "## 🔄 Auto-Learning Active",
            "",
            "This knowledge base updates every 30 seconds with new patterns.",
            "Tell Claude 'Perfect!' or 'That worked!' to save successful approaches.",
            ""
        ])

        # Add section for user content
        content_lines.extend([
            "## 📝 User Notes",
            "",
            "<!-- USER_CONTENT_START -->",
            "<!-- Add your own notes and documentation here. This section will be preserved during updates. -->",
            ""
        ])

        # If we found existing user content, add it back
        if user_content:
            content_lines.append(user_content)
            content_lines.append("")

        content_lines.append("<!-- USER_CONTENT_END -->")

        # Keep file under 30KB for quick reading
        content = '\n'.join(content_lines)
        if len(content) > 30000:
            # Truncate but preserve user content
            auto_content = content.split("<!-- USER_CONTENT_START -->")[0]
            user_section = "<!-- USER_CONTENT_START -->" + content.split("<!-- USER_CONTENT_START -->")[1] if "<!-- USER_CONTENT_START -->" in content else ""

            truncated = auto_content[:25000] + "\n\n*[Index truncated - see category files for full details]*\n\n"
            content = truncated + user_section

        with open(claude_md_path, 'w') as f:
            f.write(content)

    def _preserve_user_content(self, file_path: Path) -> Optional[str]:
        """Extract and preserve user-added content from existing CLAUDE.md"""
        if not file_path.exists():
            return None

        try:
            with open(file_path, 'r') as f:
                content = f.read()

            # Look for user content between markers
            if "<!-- USER_CONTENT_START -->" in content and "<!-- USER_CONTENT_END -->" in content:
                start = content.find("<!-- USER_CONTENT_START -->") + len("<!-- USER_CONTENT_START -->")
                end = content.find("<!-- USER_CONTENT_END -->")
                user_content = content[start:end].strip()

                # Don't return the default placeholder
                if "Add your own notes and documentation here" not in user_content:
                    return user_content

            # Also check for content after a specific marker that indicates user additions
            if "---\n## Custom Documentation" in content:
                user_content = content.split("---\n## Custom Documentation")[1]
                return "## Custom Documentation" + user_content

        except:
            pass

        return None

    def get_relevant_lessons_for_query(self, query: str, project_name: str) -> List[Dict]:
        """Get most relevant lessons for a specific query"""
        # Categorize the query
        category = self._categorize_text(query)

        if category:
            # Load lessons from that category file
            category_file = self.lessons_dir / f"{category}_lessons.md"
            if category_file.exists():
                # Return path for Claude to read
                return [{
                    'instruction': f"Check {category_file} for relevant lessons",
                    'category': category,
                    'file_path': str(category_file)
                }]

        return []