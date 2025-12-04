"""Main agent that coordinates all components"""

import time
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any
from rich.console import Console
from rich.live import Live
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn
from rich.text import Text

from .log_watcher import LogWatcher
from .log_processor import LogProcessor
from .enhanced_detector import EnhancedSuccessDetector
from .knowledge_base import KnowledgeBase
from .context_injector import ContextInjector
from .realtime_updater import RealtimeContextUpdater, HotReloadWatcher

console = Console()


class CacheAgent:
    """Main agent that caches successful patterns from Claude Code"""

    def __init__(self, db_path: Optional[str] = None, kb: Optional[KnowledgeBase] = None):
        self.kb = kb if kb is not None else KnowledgeBase(db_path)
        self.processor = LogProcessor(self.kb)
        self.detector = EnhancedSuccessDetector()  # Using enhanced detector for better stack awareness
        self.injector = None  # Will be initialized based on mode
        self.watcher = None  # Will be initialized based on mode
        self.realtime_updater = None  # Will be initialized based on mode
        self.config_watcher = HotReloadWatcher()

        self.processor.detector = self.detector
        self.first_run_check_done = False

    def start(self, watch: bool = True):
        """Start the agent"""
        # Display beautiful ASCII banner
        self._show_banner()

        console.print(Panel.fit(
            "[bold cyan]Claude Cache[/bold cyan]\n"
            "[italic]Building memory from your AI coding sessions[/italic]",
            padding=(1, 2),
            border_style="cyan"
        ))

        # Check vector search capabilities
        self._check_vector_capabilities()

        # Check for first run and offer to scan existing documentation
        if not self.first_run_check_done:
            self._check_first_run()

        if watch:
            # For monitoring mode, create watcher in silent mode
            self.watcher = LogWatcher(self.processor, silent=True)
            self.injector = ContextInjector(self.kb, silent=True)
            self.realtime_updater = RealtimeContextUpdater(self.kb, self.injector, silent=True)
            self.processor.silent_mode = True
            self.watcher.process_existing_logs()
            console.print("[blue]Starting real-time monitoring...[/blue]")
            self.start_monitoring()
        else:
            # Full processing for non-watch mode - verbose
            self.watcher = LogWatcher(self.processor, silent=False)
            self.injector = ContextInjector(self.kb, silent=False)
            self.realtime_updater = RealtimeContextUpdater(self.kb, self.injector)
            console.print("[blue]Processing existing logs...[/blue]")
            self.process_existing_logs()

    def process_existing_logs(self):
        """Process all existing log files with progress tracking"""
        try:
            # Initialize watcher if not already done
            if self.watcher is None:
                self.watcher = LogWatcher(self.processor, silent=False)
                self.injector = ContextInjector(self.kb, silent=False)
                self.realtime_updater = RealtimeContextUpdater(self.kb, self.injector)

            # First, count how many logs we have
            projects_dir = Path.home() / '.claude' / 'projects'
            log_count = len(list(projects_dir.glob('**/*.jsonl'))) if projects_dir.exists() else 0

            if log_count == 0:
                console.print("[yellow]No Claude Code conversation logs found yet.[/yellow]")
                console.print("[dim]Logs are created when you use Claude Code in Cursor/VS Code[/dim]")
                console.print("[dim]They are stored in: ~/.claude/projects/[/dim]\n")
                return

            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
                TimeElapsedColumn(),
                console=console
            ) as progress:

                # Process existing logs
                task = progress.add_task(f"[cyan]Processing {log_count} log files...", total=100)
                self.watcher.process_existing_logs()
                progress.update(task, advance=30)

                projects = self.get_projects()
                if projects:
                    per_project = 70 // len(projects)

                    for project in projects:
                        progress.update(task, description=f"[cyan]Analyzing {project}...")
                        self.analyze_project_sessions(project)
                        progress.update(task, advance=per_project//3)

                        self.injector.generate_all_commands(project)
                        progress.update(task, advance=per_project//3)

                        self.injector.export_commands_to_claude_md(project)
                        progress.update(task, advance=per_project//3)

                progress.update(task, completed=100, description="[green]✓ Processing complete!")

            self.show_statistics()
        except Exception as e:
            import traceback
            console.print(f"[red]Error during log processing: {e}[/red]")
            console.print(f"[dim]Traceback:\n{traceback.format_exc()}[/dim]")
            raise

    def start_monitoring(self):
        """Start real-time log monitoring with context updates"""
        # Enable silent mode for log processor to suppress messages
        self.processor.silent_mode = True

        # Start real-time context updates
        self.realtime_updater.start()

        # Start config hot-reload
        self.config_watcher.start()

        # Start log monitoring
        observer = self.watcher.start()

        try:
            # Clear console for clean display
            console.clear()

            with Live(self.generate_status_table(), refresh_per_second=0.033, auto_refresh=False) as live:
                while True:
                    time.sleep(30)
                    live.update(self.generate_status_table())
                    live.refresh()

        except KeyboardInterrupt:
            console.print("\n[yellow]Stopping monitoring...[/yellow]")
            self.realtime_updater.stop()
            self.config_watcher.stop()
            self.watcher.stop()

    def analyze_project_sessions(self, project_name: str):
        """Analyze sessions for a project and extract patterns"""
        sessions = self.processor.session_tracker.sessions.get(project_name, [])

        patterns_found = 0
        for session in sessions:
            result = self.detector.analyze_session_success(session['entries'])

            if result['success']:
                pattern = result['pattern']
                self.kb.store_success_pattern(pattern, project_name, result['score'])
                patterns_found += 1

                self.detect_and_store_conventions(session, project_name)

        if patterns_found > 0:
            console.print(f"[green]✓ Found {patterns_found} successful patterns in {project_name}[/green]")

    def detect_and_store_conventions(self, session: dict, project_name: str):
        """Detect and store project conventions from sessions"""
        file_operations = session.get('file_operations', [])

        for op in file_operations:
            # Handle both object and dict formats
            if hasattr(op, 'data'):
                data = op.data
            else:
                data = op if isinstance(op, dict) else {}

            if data.get('tool') == 'Edit':
                args = data.get('args', {})
                old_str = args.get('old_string', '')
                new_str = args.get('new_string', '')

                if 'import' in old_str or 'import' in new_str:
                    self.kb.store_convention(
                        project_name,
                        'import_pattern',
                        new_str[:100] if new_str else old_str[:100],
                        'Import convention'
                    )

    def get_projects(self):
        """Get list of all projects"""
        projects_dir = Path.home() / '.claude' / 'projects'
        if not projects_dir.exists():
            return []

        return [d.name for d in projects_dir.iterdir() if d.is_dir()]

    def show_statistics(self):
        """Display enhanced knowledge base statistics including documentation"""
        stats = self.kb.get_statistics()

        # Get documentation statistics
        doc_stats = self._get_documentation_statistics()

        # Create a beautiful statistics display
        table = Table(
            title="✨ Claude Cache Knowledge Base ✨",
            show_header=True,
            header_style="bold magenta",
            border_style="cyan",
            title_style="bold cyan"
        )
        table.add_column("Category", style="cyan", width=25)
        table.add_column("Count", style="green", width=15)
        table.add_column("Details", style="yellow", width=30)

        patterns = stats.get('total_patterns', 0)
        projects = stats.get('total_projects', 0)  # Fixed: use total_projects not projects
        requests = stats.get('total_requests', 0)

        # Documentation metrics
        total_docs = doc_stats.get('total_docs', 0)
        total_lessons = doc_stats.get('total_lessons', 0)
        total_warnings = doc_stats.get('total_warnings', 0)
        doc_projects = doc_stats.get('projects_with_docs', 0)

        # Calculate insights
        patterns_per_project = patterns / projects if projects > 0 else 0
        lessons_per_project = total_lessons / doc_projects if doc_projects > 0 else 0
        success_rate = (patterns / requests * 100) if requests > 0 else 0

        # Documentation section
        if total_docs > 0:
            table.add_row(
                "📚 Documentation Files",
                str(total_docs),
                f"From {doc_projects} projects"
            )
            table.add_row(
                "💡 Lessons Learned",
                str(total_lessons),
                f"~{lessons_per_project:.0f} per project"
            )
            if total_warnings > 0:
                table.add_row(
                    "⚠️  Critical Warnings",
                    str(total_warnings),
                    "Important gotchas to avoid"
                )
            table.add_section()

        # Auto-learned patterns section
        table.add_row(
            "🧠 Success Patterns",
            str(patterns),
            self._get_trend_indicator(patterns)
        )
        table.add_row(
            "📁 Active Projects",
            str(projects),
            f"~{patterns_per_project:.1f} patterns each"
        )
        table.add_row(
            "💬 Total Requests",
            str(requests),
            f"{success_rate:.1f}% success rate"
        )

        # Add insights section
        if patterns > 0:
            table.add_section()
            table.add_row(
                "🎯 Most Active",
                self._get_most_active_project() or "N/A",
                "Keep it up! 🚀"
            )
            table.add_row(
                "⭐ Best Success Rate",
                f"{success_rate:.1f}%",
                self._get_performance_emoji(success_rate)
            )

        console.print(table)

        # Add motivational message based on stats
        if patterns == 0:
            console.print("\n[yellow]💡 Start using Claude Code to build your knowledge base![/yellow]")
        elif patterns < 10:
            console.print("\n[cyan]🌱 Your knowledge garden is growing![/cyan]")
        elif patterns < 50:
            console.print("\n[green]🌳 Great progress! Your cache is building nicely![/green]")
        else:
            console.print("\n[bold green]🏆 Excellent! You have a rich knowledge base![/bold green]")

    def _get_documentation_statistics(self) -> Dict[str, int]:
        """Get statistics about imported documentation"""
        import sqlite3
        import json

        conn = sqlite3.connect(self.kb.db_path)
        cursor = conn.cursor()

        # Count total documentation files
        cursor.execute("SELECT COUNT(*) FROM documentation")
        total_docs = cursor.fetchone()[0]

        # Count projects with documentation
        cursor.execute("SELECT COUNT(DISTINCT project_name) FROM documentation")
        projects_with_docs = cursor.fetchone()[0]

        # Count lessons, warnings, and best practices
        cursor.execute("SELECT content FROM documentation")
        docs = cursor.fetchall()

        total_lessons = 0
        total_warnings = 0
        total_practices = 0

        for (content,) in docs:
            try:
                doc_data = json.loads(content)
                total_lessons += len(doc_data.get('lessons_learned', []))
                total_warnings += len(doc_data.get('warnings', []))
                total_practices += len(doc_data.get('best_practices', []))
            except:
                continue

        conn.close()

        return {
            'total_docs': total_docs,
            'projects_with_docs': projects_with_docs,
            'total_lessons': total_lessons,
            'total_warnings': total_warnings,
            'total_practices': total_practices
        }

    def _get_trend_indicator(self, value: int) -> str:
        """Get trend indicator based on value"""
        if value == 0:
            return "📊 Getting started"
        elif value < 10:
            return "📈 Building up"
        elif value < 50:
            return "⚡ Accelerating"
        else:
            return "🚀 Thriving!"

    def _get_performance_emoji(self, percentage: float) -> str:
        """Get performance emoji based on percentage"""
        if percentage >= 90:
            return "🌟 Outstanding!"
        elif percentage >= 70:
            return "✨ Excellent!"
        elif percentage >= 50:
            return "👍 Good!"
        else:
            return "📈 Improving"

    def _get_most_active_project(self) -> Optional[str]:
        """Get the most active project name"""
        import sqlite3
        try:
            conn = sqlite3.connect(self.kb.db_path)
            cursor = conn.cursor()
            cursor.execute("""
                SELECT project_name, COUNT(*) as count
                FROM success_patterns
                GROUP BY project_name
                ORDER BY count DESC
                LIMIT 1
            """)
            result = cursor.fetchone()
            conn.close()
            return result[0] if result else None
        except:
            return None

    def _get_recent_pattern_count(self) -> int:
        """Get count of patterns from last 24 hours"""
        import sqlite3
        from datetime import datetime, timedelta
        try:
            conn = sqlite3.connect(self.kb.db_path)
            cursor = conn.cursor()
            yesterday = (datetime.now() - timedelta(days=1)).isoformat()
            cursor.execute("""
                SELECT COUNT(*)
                FROM success_patterns
                WHERE created_at > ?
            """, (yesterday,))
            result = cursor.fetchone()
            conn.close()
            return result[0] if result else 0
        except:
            return 0

    def generate_status_table(self):
        """Generate a status table for live display"""
        stats = self.kb.get_statistics()
        patterns = stats.get('total_patterns', 0)
        projects_data = stats.get('projects', [])

        # Handle both old (number) and new (list) format for backward compatibility
        if isinstance(projects_data, list):
            project_count = len(projects_data)
            # Generate clean project summary
            if projects_data:
                current_project = projects_data[0]['name'] if projects_data else "None"
                project_summary = f"{current_project} + {project_count-1} others" if project_count > 1 else current_project
            else:
                project_summary = "None yet"
        else:
            project_count = projects_data
            project_summary = f"{project_count} projects"

        # Get most active project
        most_active = self._get_most_active_project()

        # Get recent activity count (patterns from last 24h)
        recent_patterns = self._get_recent_pattern_count()

        table = Table(title="🧠 Claude Cache - Live Monitoring", show_header=True, border_style="blue")
        table.add_column("Metric", style="cyan", width=22)
        table.add_column("Value", style="green", width=50)
        table.add_column("Status", style="yellow", width=35)

        table.add_row("Patterns Learned", str(patterns), self._get_pattern_status(patterns))
        table.add_row("Projects Tracked", project_summary, f"Monitoring ~/.claude/projects/")
        table.add_row("Most Active", most_active or "None yet", "Current session leader")
        table.add_row("Recent Activity", f"{recent_patterns} today", "New patterns detected")
        table.add_row("Status", "[green]● Watching[/green]", f"Updated {datetime.now().strftime('%H:%M:%S')}")

        return table

    def _get_pattern_status(self, count: int) -> str:
        """Get encouraging status message based on pattern count"""
        if count == 0:
            return "Keep using Claude Code!"
        elif count < 10:
            return "Building knowledge... 🌱"
        elif count < 50:
            return "Growing nicely! 🌳"
        else:
            return "Rich knowledge base! 🏆"

    def query_patterns(self, query: str, project: Optional[str] = None, filters: Optional[Dict] = None):
        """Query all indexed content using unified search with advanced filtering"""
        if filters is None:
            filters = {}

        # Apply pattern type filters to query
        type_filter = ""
        if filters.get('only_gold'):
            type_filter = " AND success_score >= 0.9"
        elif filters.get('only_anti'):
            query = f"anti-pattern {query}"
        elif filters.get('only_journey'):
            query = f"journey {query}"

        # Get results
        limit = filters.get('limit', 10)
        results = self.kb.unified_search(query, project, limit=limit)

        if not results:
            console.print("[yellow]No results found[/yellow]")
            return

        # Display results with optional code preview
        from rich.table import Table
        from rich.syntax import Syntax
        from rich.panel import Panel

        if filters.get('show_code') or filters.get('show_preview'):
            # Detailed view with code
            console.print(f"\n[bold cyan]🔍 Search Results for: '{query}'[/bold cyan]\n")

            for i, result in enumerate(results, 1):
                # Determine pattern type and quality
                content_type = result.get('type', 'pattern')
                score = result.get('success_score', result.get('similarity', 0))

                # Format type with color based on quality
                if score >= 0.9:
                    type_emoji = "🥇"
                    type_color = "green"
                elif score >= 0.7:
                    type_emoji = "🥈"
                    type_color = "yellow"
                else:
                    type_emoji = "🥉"
                    type_color = "dim"

                # Get full pattern data if available
                pattern_data = result.get('pattern_data', {})
                approach = pattern_data.get('approach', result.get('content', ''))
                solution_steps = pattern_data.get('solution_steps', [])
                files = pattern_data.get('files_involved', [])

                # Build content display
                content_parts = []

                # Title
                title = f"{i}. {type_emoji} "
                if content_type == 'documentation':
                    title += f"📚 Documentation"
                elif content_type == 'anti-pattern':
                    title += f"⚠️ Anti-pattern"
                elif content_type == 'journey':
                    title += f"🛤️ Journey Pattern"
                else:
                    title += f"Pattern"

                # Add project info if available
                if result.get('project'):
                    title += f" [{result['project']}]"

                # Description
                description = approach[:200] + "..." if len(approach) > 200 else approach

                # Code snippet
                code_content = None
                if solution_steps and (filters.get('show_code') or filters.get('show_preview')):
                    # Extract code from solution steps
                    code_lines = []
                    for step in solution_steps:
                        if isinstance(step, str) and any(kw in step.lower() for kw in ['def ', 'class ', 'import ', 'function', '{', '}', '(', ')']):
                            code_lines.append(step)

                    if code_lines:
                        if filters.get('show_preview'):
                            code_content = '\n'.join(code_lines[:5])
                            if len(code_lines) > 5:
                                code_content += f"\n... ({len(code_lines) - 5} more lines)"
                        else:
                            code_content = '\n'.join(code_lines)

                # Build panel content
                panel_content = f"[{type_color}]{description}[/{type_color}]"

                if files:
                    panel_content += f"\n\n[dim]Files: {', '.join(files[:3])}[/dim]"

                if code_content:
                    # Try to detect language
                    lang = "python"  # default
                    if any(ext in str(files) for ext in ['.js', '.jsx', '.ts', '.tsx']):
                        lang = "javascript"
                    elif any(ext in str(files) for ext in ['.rs']):
                        lang = "rust"
                    elif any(ext in str(files) for ext in ['.go']):
                        lang = "go"

                    syntax = Syntax(code_content, lang, theme="monokai", line_numbers=True)
                    panel_content += "\n\n"
                    console.print(Panel(
                        panel_content,
                        title=title,
                        border_style=type_color,
                        expand=False
                    ))
                    console.print(syntax)
                else:
                    console.print(Panel(
                        panel_content,
                        title=title,
                        border_style=type_color,
                        expand=False
                    ))

                # Show similarity score
                console.print(f"[dim]Match: {result['similarity']:.1%}[/dim]\n")

        else:
            # Compact table view (original)
            table = Table(title=f"Search Results for: '{query}'", show_lines=True)
            table.add_column("#", style="cyan", width=4)
            table.add_column("Type", style="yellow", width=12)
            table.add_column("Content", style="white", width=70)
            table.add_column("Match", style="green", width=8)

            for i, result in enumerate(results, 1):
                # Format type with emoji
                content_type = result['type']
                score = result.get('success_score', result.get('similarity', 0))

                if score >= 0.9:
                    type_display = "🥇 gold"
                elif score >= 0.7:
                    type_display = "🥈 silver"
                elif content_type == 'documentation':
                    type_display = f"📚 {result.get('doc_type', 'doc')}"
                elif content_type == 'anti-pattern':
                    type_display = "⚠️ anti"
                elif content_type == 'journey':
                    type_display = "🛤️ journey"
                else:
                    type_display = "🥉 bronze"

                # Format content preview
                content = result['content'][:100] + "..." if len(result['content']) > 100 else result['content']

                # Format similarity
                similarity = f"{result['similarity']:.1%}"

                table.add_row(str(i), type_display, content, similarity)

            console.print(table)

        # Show search mode and tips
        if results:
            search_mode = results[0].get('search_mode', 'unknown')
            console.print(f"\n[dim]💡 Tips:[/dim]")
            console.print(f"[dim]  • Use --code to see full code snippets[/dim]")
            console.print(f"[dim]  • Use --preview for 5-line preview[/dim]")
            console.print(f"[dim]  • Use --gold/--anti/--journey to filter types[/dim]")

            if search_mode == 'semantic':
                console.print(f"[dim]  ✨ Using semantic search - understanding context[/dim]")
            else:
                console.print(f"[dim]  📊 Using TF-IDF search - matching keywords[/dim]")

    def export_knowledge(self, output_file: str, project: Optional[str] = None):
        """Export knowledge base to file"""
        import json

        data = self.kb.export_patterns(project)

        with open(output_file, 'w') as f:
            json.dump(data, f, indent=2)

        console.print(f"[green]✓ Exported to {output_file}[/green]")

    def import_knowledge(self, input_file: str):
        """Import knowledge from file"""
        import json

        with open(input_file, 'r') as f:
            data = json.load(f)

        self.kb.import_patterns(data)

    def rebuild_index(self):
        """Rebuild the entire knowledge base from scratch"""
        console.print("[yellow]Rebuilding knowledge base...[/yellow]")

        import sqlite3
        conn = sqlite3.connect(self.kb.db_path)
        cursor = conn.cursor()

        tables = ['success_patterns', 'project_conventions', 'user_requests', 'tool_usage', 'responses']
        for table in tables:
            cursor.execute(f'DELETE FROM {table}')

        conn.commit()
        conn.close()

        self.process_existing_logs()
        console.print("[green]✓ Knowledge base rebuilt[/green]")

    def _check_first_run(self):
        """Check if this is first run and offer to scan existing documentation"""
        # Check for first-run flag file
        first_run_flag = Path.home() / '.claude' / '.first_run_complete'
        if first_run_flag.exists():
            self.first_run_check_done = True
            return

        # Check if knowledge base is completely empty
        stats = self.kb.get_statistics()
        doc_stats = self._get_documentation_statistics()

        # Check if we have any data at all (patterns, requests, or documentation)
        has_patterns = stats.get('total_patterns', 0) > 0
        has_requests = stats.get('total_requests', 0) > 0
        has_docs = doc_stats['total_docs'] > 0

        # If we have any data, don't show first-run prompt
        # But still allow log processing to continue
        if has_patterns or has_requests or has_docs:
            # Create flag file to skip future first-run checks
            first_run_flag.touch()
            self.first_run_check_done = True
            return

        if not has_patterns and not has_requests and not has_docs:
            console.print("\n[bold yellow]🎉 Welcome to Claude Cache![/bold yellow]")
            console.print("\nFirst time setup detected. Let's import your existing documentation!")
            console.print("\nWould you like to scan for existing documentation?")
            console.print("1. Scan all Claude Code projects (from logs)")
            console.print("2. Scan your Development folder")
            console.print("3. Scan a custom directory")
            console.print("4. Skip for now\n")

            from rich.prompt import Prompt

            choice = Prompt.ask("Choose an option", choices=["1", "2", "3", "4"], default="2")

            if choice == "1":
                self._batch_scan_all_projects()
            elif choice == "2":
                self._scan_development_folder()
            elif choice == "3":
                custom_path = Prompt.ask("Enter the path to scan")
                if Path(custom_path).exists():
                    self._scan_custom_directory(custom_path)
                else:
                    console.print("[red]Path not found[/red]")
            else:
                console.print("[dim]Skipping documentation scan. You can run 'cache scan-docs' later.[/dim]")

            # Mark first run as complete after any choice
            first_run_flag = Path.home() / '.claude' / '.first_run_complete'
            first_run_flag.touch()

        self.first_run_check_done = True

    def _batch_scan_all_projects(self):
        """Scan all Claude Code projects for existing documentation"""
        from .doc_scanner import DocumentationScanner

        console.print("\n[cyan]Scanning all projects for documentation...[/cyan]")

        # Find all project directories
        claude_projects_dir = Path.home() / '.claude' / 'projects'
        if not claude_projects_dir.exists():
            console.print("[yellow]No Claude Code projects found yet[/yellow]")
            return

        project_dirs = [d for d in claude_projects_dir.iterdir() if d.is_dir()]

        if not project_dirs:
            console.print("[yellow]No projects found[/yellow]")
            return

        scanner = DocumentationScanner(self.kb)
        total_docs = 0

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            console=console
        ) as progress:

            task = progress.add_task(f"Scanning {len(project_dirs)} projects...",
                                    total=len(project_dirs))

            for project_dir in project_dirs:
                project_name = project_dir.name
                progress.update(task, description=f"Scanning {project_name}...")

                # Try to find the actual project path from logs
                actual_path = self._find_project_path(project_name)

                if actual_path and Path(actual_path).exists():
                    docs = scanner.scan_repository(actual_path, project_name)
                    total_docs += len(docs)

                progress.advance(task)

        console.print(f"\n[green]✓ Imported {total_docs} documentation files![/green]")
        console.print("[dim]Documentation will be included in context generation[/dim]\n")

    def _find_project_path(self, project_name: str) -> Optional[str]:
        """Try to find the actual filesystem path for a project from its logs"""
        project_log_dir = Path.home() / '.claude' / 'projects' / project_name

        # Look for the most recent log file
        log_files = sorted(project_log_dir.glob('*.jsonl'),
                          key=lambda p: p.stat().st_mtime, reverse=True)

        if not log_files:
            return None

        # Parse first few lines to find working directory
        import json
        try:
            with open(log_files[0], 'r') as f:
                for line in f:
                    try:
                        entry = json.loads(line)
                        # Look for working directory in various places
                        if 'workingDirectory' in entry:
                            return entry['workingDirectory']
                        if 'cwd' in entry:
                            return entry['cwd']
                        if entry.get('type') == 'tool_call':
                            if 'workingDirectory' in entry.get('args', {}):
                                return entry['args']['workingDirectory']
                    except:
                        continue
        except:
            pass

        # Fallback: try common development directories
        common_paths = [
            Path.home() / 'Development' / project_name,
            Path.home() / 'Projects' / project_name,
            Path.home() / 'Code' / project_name,
            Path.home() / 'dev' / project_name,
            Path.home() / project_name,
        ]

        for path in common_paths:
            if path.exists():
                return str(path)

        return None

    def _scan_development_folder(self):
        """Scan the user's Development folder for all projects with documentation"""
        from .doc_scanner import DocumentationScanner

        # Common development folder locations
        dev_paths = [
            Path.home() / 'Development',
            Path.home() / 'Projects',
            Path.home() / 'dev',
            Path.home() / 'Code',
            Path.home() / 'Documents' / 'Development',
            Path.home() / 'workspace'
        ]

        # Find which one exists
        dev_folder = None
        for path in dev_paths:
            if path.exists():
                dev_folder = path
                break

        if not dev_folder:
            # Ask user for their development folder
            from rich.prompt import Prompt
            custom = Prompt.ask("Enter your development folder path", default=str(Path.home() / 'Development'))
            dev_folder = Path(custom)

            if not dev_folder.exists():
                console.print("[red]Development folder not found[/red]")
                return

        console.print(f"\n[cyan]Scanning {dev_folder} for project documentation...[/cyan]")
        console.print("[dim]This may take a few moments for large folders...[/dim]\n")

        scanner = DocumentationScanner(self.kb)
        total_docs = 0
        scanned_projects = []

        # Find all potential project directories (has .git or package.json or README)
        project_dirs = []

        # First level subdirectories only (don't go too deep)
        for item in dev_folder.iterdir():
            if item.is_dir() and not item.name.startswith('.'):
                # Check if it looks like a project
                if (item / '.git').exists() or \
                   (item / 'package.json').exists() or \
                   (item / 'README.md').exists() or \
                   (item / 'setup.py').exists() or \
                   (item / 'Cargo.toml').exists():
                    project_dirs.append(item)

        if not project_dirs:
            console.print("[yellow]No projects found in development folder[/yellow]")
            return

        console.print(f"[green]Found {len(project_dirs)} projects to scan[/green]\n")

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            console=console
        ) as progress:

            task = progress.add_task(f"Scanning {len(project_dirs)} projects...",
                                    total=len(project_dirs))

            for project_path in project_dirs:
                project_name = project_path.name
                progress.update(task, description=f"Scanning {project_name}...")

                try:
                    docs = scanner.scan_repository(str(project_path), project_name)
                    if docs:
                        total_docs += len(docs)
                        scanned_projects.append(project_name)
                except Exception as e:
                    console.print(f"[yellow]Warning: Could not scan {project_name}: {e}[/yellow]")

                progress.advance(task)

        console.print(f"\n[bold green]✓ Successfully imported {total_docs} documentation files![/bold green]")
        if scanned_projects:
            console.print(f"[green]Projects scanned: {', '.join(scanned_projects[:10])}")
            if len(scanned_projects) > 10:
                console.print(f"[dim]... and {len(scanned_projects) - 10} more[/dim]")

        # Show immediate statistics after scan
        console.print("\n" + "="*60)
        console.print("[bold cyan]📊 Your Knowledge Base Starting Point:[/bold cyan]\n")

        # Get detailed stats
        doc_stats = self._get_documentation_statistics()

        if doc_stats['total_lessons'] > 0:
            console.print(f"  💡 [green]{doc_stats['total_lessons']}[/green] lessons learned imported")
        if doc_stats['total_warnings'] > 0:
            console.print(f"  ⚠️  [yellow]{doc_stats['total_warnings']}[/yellow] critical warnings found")
        if doc_stats['total_practices'] > 0:
            console.print(f"  ✅ [cyan]{doc_stats['total_practices']}[/cyan] best practices documented")

        console.print(f"\n  📁 Knowledge organized across [bold]{len(scanned_projects)}[/bold] projects")
        console.print(f"  📚 Ready to learn from your coding sessions!\n")

        console.print("="*60 + "\n")
        console.print("[dim]Claude will now automatically use this knowledge![/dim]")
        console.print("[dim]Say 'Perfect!' or 'Thanks!' when things work to save new patterns.[/dim]\n")

    def _scan_custom_directory(self, directory_path: str):
        """Scan a custom directory for projects and documentation"""
        from .doc_scanner import DocumentationScanner

        dir_path = Path(directory_path)
        console.print(f"\n[cyan]Scanning {dir_path} for documentation...[/cyan]")

        scanner = DocumentationScanner(self.kb)

        # Determine if this is a single project or multiple projects
        is_single_project = (dir_path / '.git').exists() or \
                           (dir_path / 'package.json').exists() or \
                           (dir_path / 'README.md').exists()

        if is_single_project:
            # Scan as single project
            project_name = dir_path.name
            docs = scanner.scan_repository(str(dir_path), project_name)
            console.print(f"\n[green]✓ Imported {len(docs)} documentation files from {project_name}![/green]")
        else:
            # Scan subdirectories as separate projects
            total_docs = 0
            for item in dir_path.iterdir():
                if item.is_dir() and not item.name.startswith('.'):
                    try:
                        docs = scanner.scan_repository(str(item), item.name)
                        total_docs += len(docs)
                    except Exception as e:
                        console.print(f"[yellow]Warning: Could not scan {item.name}: {e}[/yellow]")

            console.print(f"\n[green]✓ Imported {total_docs} documentation files![/green]")

        console.print("[dim]Documentation will be included in context generation[/dim]\n")

    def _show_banner(self):
        """Display ASCII art banner"""
        banner = """
    ╔═══════════════════════════════════════════╗
    ║                                           ║
    ║              claude                       ║
    ║                                           ║
    ║    ___    _    ____ _   _ _____           ║
    ║   / __\\  / \\  / ___| | | | ____|          ║
    ║  | |    / _ \\ | |   | |_| |  _|           ║
    ║  | |__ / ___ \\| |___|  _  | |___          ║
    ║   \\___/_/   \\_\\\\____|_| |_|_____|         ║
    ║                                           ║
    ║                v0.9.1                     ║
    ╚═══════════════════════════════════════════╝
        """

        console.print(Text(banner, style="bold cyan"))

    def _check_vector_capabilities(self):
        """Check and display vector search capabilities"""
        if self.kb.vector_search:
            capabilities = self.kb.vector_search.get_capabilities()

            if capabilities['mode'] == 'semantic':
                console.print("[green]✨ Semantic search enabled - 2x better pattern matching![/green]")
                console.print("[green]🧠 Understanding context and meaning, not just keywords[/green]\n")
            else:
                console.print("[yellow]📊 Using TF-IDF search (keyword matching)[/yellow]")
                console.print("[yellow]💡 Tip: For semantic understanding, install:[/yellow]")
                console.print("    [cyan]pip install claude-cache[enhanced][/cyan]")
                console.print("    [dim]This enables context-aware pattern matching[/dim]\n")