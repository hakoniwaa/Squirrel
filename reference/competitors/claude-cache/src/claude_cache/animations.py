"""
Animations and visual feedback for Claude Cache
Makes the terminal feel alive and thinking
"""

import asyncio
import time
import sys
import select
import termios
import tty
from typing import List, Optional, Dict, Any
from datetime import datetime
from rich.console import Console
from rich.live import Live
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.panel import Panel
from rich.layout import Layout
from rich.text import Text
from rich.align import Align
from rich.columns import Columns
import random

console = Console()


class KeyboardHandler:
    """Handle keyboard input for interactive monitoring"""

    def __init__(self):
        self.is_posix = hasattr(sys, 'stdin') and hasattr(sys.stdin, 'fileno')

    def get_key_non_blocking(self) -> Optional[str]:
        """Get a single keypress without blocking (Unix/macOS only)"""
        if not self.is_posix:
            return None

        try:
            if select.select([sys.stdin], [], [], 0) == ([sys.stdin], [], []):
                return sys.stdin.read(1)
        except:
            pass
        return None

    def setup_raw_mode(self):
        """Setup terminal for raw input (Unix/macOS only)"""
        if not self.is_posix:
            return None

        try:
            fd = sys.stdin.fileno()
            old_settings = termios.tcgetattr(fd)
            tty.setraw(sys.stdin.fileno())
            return old_settings
        except:
            return None

    def restore_terminal(self, old_settings):
        """Restore terminal settings"""
        if not self.is_posix or not old_settings:
            return

        try:
            termios.tcsetattr(sys.stdin.fileno(), termios.TCSADRAIN, old_settings)
        except:
            pass


class HelpSystem:
    """Interactive help system for Claude Cache"""

    @staticmethod
    def get_help_content() -> str:
        """Generate comprehensive help content"""
        return """
🆘 [bold cyan]Claude Cache Help System[/bold cyan]

[bold yellow]📖 What is Claude Cache?[/bold yellow]
Claude Cache gives Claude Code perfect memory by automatically learning from your coding sessions.
It captures patterns, solutions, and mistakes to make you faster and smarter.

[bold yellow]🚀 Getting Started[/bold yellow]
1. Choose your mode:
   • [cyan]cache start --watch[/cyan] - Real-time background learning (recommended)
   • [cyan]cache start[/cyan] - One-time processing (exits after learning)
2. [cyan]cache monitor[/cyan] - Open this interactive dashboard
3. Code normally in Claude Code - it automatically learns
4. [cyan]cache query "problem"[/cyan] - Find solutions to similar problems
5. [cyan]cache stats[/cyan] - See what you've learned

[bold yellow]⌨️ Interactive Commands[/bold yellow]
• [cyan]q[/cyan] - Query patterns (search your knowledge)
• [cyan]s[/cyan] - Show statistics
• [cyan]p[/cyan] - Switch projects
• [cyan]w[/cyan] - Mark current work as successful (win)
• [cyan]f[/cyan] - Mark current approach as failed (learn from failure)
• [cyan]t[/cyan] - Tutorial mode (guided tour)
• [cyan]h[/cyan] - Show this help
• [cyan]ESC[/cyan] - Exit monitoring

[bold yellow]🎯 Key Concepts[/bold yellow]
• [green]Gold Patterns[/green] - Proven solutions that work consistently
• [yellow]Silver Patterns[/yellow] - Good solutions with minor issues
• [red]Anti-Patterns[/red] - Confirmed failures to avoid
• [blue]Journey Patterns[/blue] - Complete problem→solution sequences

[bold yellow]💡 Pro Tips[/bold yellow]
• Let it run in background while coding - it learns automatically
• Use [cyan]cache query[/cyan] before solving new problems
• Mark wins/fails to improve pattern quality
• Check stats regularly to see your progress

[dim]Press any key to return to monitoring...[/dim]
"""

    @staticmethod
    def get_tutorial_content() -> List[str]:
        """Get step-by-step tutorial content"""
        return [
            "🎓 [bold cyan]Claude Cache Tutorial - Step 1/5[/bold cyan]\n\nClaude Cache automatically learns from your Claude Code sessions.\nIt watches your conversations and extracts useful patterns.\n\n[green]What it learns:[/green]\n• Code solutions that work\n• Debugging approaches\n• Architecture decisions\n• Error fixes\n\n[dim]Press 'n' for next, 'q' to quit tutorial[/dim]",

            "🎓 [bold cyan]Claude Cache Tutorial - Step 2/5[/bold cyan]\n\nPatterns are classified by quality:\n\n🥇 [green]Gold[/green] - Proven solutions that work consistently\n🥈 [yellow]Silver[/yellow] - Good solutions with minor issues\n🥉 [blue]Bronze[/blue] - Partial solutions or drafts\n⚠️  [red]Anti-patterns[/red] - Confirmed failures to avoid\n🛤️  [cyan]Journey[/cyan] - Complete problem→solution paths\n\n[dim]Press 'n' for next, 'p' for previous, 'q' to quit[/dim]",

            "🎓 [bold cyan]Claude Cache Tutorial - Step 3/5[/bold cyan]\n\nSearching your knowledge:\n\n[cyan]cache query \"authentication\"[/cyan] - Find auth patterns\n[cyan]cache query \"database error\" --gold[/cyan] - Only gold patterns\n[cyan]cache recent[/cyan] - See what you learned today\n\nThe search understands context and meaning, not just keywords!\n\n[dim]Press 'n' for next, 'p' for previous, 'q' to quit[/dim]",

            "🎓 [bold cyan]Claude Cache Tutorial - Step 4/5[/bold cyan]\n\nActive learning commands:\n\n[cyan]cache win[/cyan] - Mark current work as successful\n[cyan]cache fail \"didn't work because...\"[/cyan] - Learn from failures\n[cyan]cache learn \"solution here\" --tags api,auth[/cyan] - Manual learning\n\nThis improves pattern quality and helps others on your team!\n\n[dim]Press 'n' for next, 'p' for previous, 'q' to quit[/dim]",

            "🎓 [bold cyan]Claude Cache Tutorial - Step 5/5[/bold cyan]\n\n🎉 [green]You're ready to go![/green]\n\nBest practices:\n• Always run [cyan]cache start --watch[/cyan] in background while coding\n• Use [cyan]cache monitor[/cyan] to see real-time learning\n• Query before solving new problems\n• Mark successes and failures\n• Check [cyan]cache stats[/cyan] regularly\n\nClaude Cache learns continuously, making you faster over time!\n\n[dim]Press 'q' to finish tutorial[/dim]"
        ]


class ThinkingSpinner:
    """Contextual spinner that shows what's being analyzed"""

    THINKING_STATES = [
        "🔍 Scanning patterns...",
        "🧠 Analyzing complexity...",
        "⚡ Detecting anti-patterns...",
        "🔗 Correlating solutions...",
        "📊 Building knowledge graph...",
        "✨ Finding insights...",
        "🎯 Matching patterns...",
        "💡 Learning from failures...",
    ]

    def __init__(self):
        self.current_state = 0

    def get_next_state(self) -> str:
        """Get next thinking state message"""
        state = self.THINKING_STATES[self.current_state % len(self.THINKING_STATES)]
        self.current_state += 1
        return state

    async def run(self, duration: float = 3.0):
        """Run thinking animation for specified duration"""
        with Progress(
            SpinnerColumn(),
            TextColumn("[cyan]{task.description}"),
            transient=True,
            console=console
        ) as progress:
            task = progress.add_task(self.get_next_state(), total=None)

            start_time = time.time()
            while time.time() - start_time < duration:
                await asyncio.sleep(0.5)
                progress.update(task, description=self.get_next_state())


class PatternDiscoveryFeed:
    """Live streaming feed of pattern discoveries"""

    def __init__(self):
        self.patterns = []
        self.max_visible = 5

    def add_pattern(self, pattern_type: str, description: str, project: str):
        """Add a new pattern to the feed"""
        timestamp = datetime.now().strftime("%H:%M:%S")

        # Choose emoji based on type
        if pattern_type == "gold":
            emoji = "🥇"
            color = "green"
        elif pattern_type == "silver":
            emoji = "🥈"
            color = "yellow"
        elif pattern_type == "bronze":
            emoji = "🥉"
            color = "dim"
        elif pattern_type == "anti":
            emoji = "⚠️"
            color = "red"
        elif pattern_type == "journey":
            emoji = "🛤️"
            color = "blue"
        else:
            emoji = "📝"
            color = "white"

        self.patterns.append({
            "timestamp": timestamp,
            "emoji": emoji,
            "color": color,
            "description": description[:60] + "..." if len(description) > 60 else description,
            "project": project,
            "age": 0
        })

        # Keep only recent patterns
        if len(self.patterns) > self.max_visible:
            self.patterns = self.patterns[-self.max_visible:]

    def render(self) -> Panel:
        """Render the pattern feed as a panel"""
        lines = []

        for pattern in self.patterns:
            # Create fading effect based on age
            opacity = max(0.3, 1.0 - (pattern["age"] * 0.2))

            if opacity > 0.7:
                style = f"bold {pattern['color']}"
            elif opacity > 0.4:
                style = pattern["color"]
            else:
                style = "dim"

            line = Text()
            line.append(f"[{pattern['timestamp']}] ", style="dim")
            line.append(f"{pattern['emoji']} ", style=style)
            line.append(pattern["description"], style=style)
            line.append(f" [{pattern['project']}]", style="dim cyan")

            lines.append(line)

            # Age patterns for fading effect
            pattern["age"] += 1

        # Add empty lines if needed
        while len(lines) < self.max_visible:
            lines.insert(0, Text(""))

        content = "\n".join(str(line) for line in lines)

        return Panel(
            content,
            title="🔄 Pattern Discovery Feed",
            border_style="cyan",
            height=self.max_visible + 2
        )

    async def animate(self, patterns_to_add: List[Dict], delay: float = 0.5):
        """Animate pattern discoveries with delays"""
        with Live(self.render(), refresh_per_second=4, console=console) as live:
            for pattern in patterns_to_add:
                self.add_pattern(
                    pattern["type"],
                    pattern["description"],
                    pattern["project"]
                )
                live.update(self.render())
                await asyncio.sleep(delay)

            # Keep showing for a bit then fade
            for _ in range(5):
                await asyncio.sleep(0.5)
                live.update(self.render())


class NotificationToast:
    """Pop-up style notifications that appear and fade"""

    @staticmethod
    async def show(message: str, type: str = "info", duration: float = 3.0):
        """Show a notification toast"""

        # Choose style based on type
        if type == "success":
            icon = "✅"
            border_style = "green"
        elif type == "warning":
            icon = "⚠️"
            border_style = "yellow"
        elif type == "error":
            icon = "❌"
            border_style = "red"
        elif type == "discovery":
            icon = "✨"
            border_style = "cyan"
        else:
            icon = "ℹ️"
            border_style = "blue"

        # Create notification panel
        notification = Panel(
            Align.center(f"{icon} {message}"),
            border_style=border_style,
            expand=False,
            padding=(0, 2)
        )

        # Show with fade effect
        with Live(notification, refresh_per_second=4, console=console, transient=True) as live:
            await asyncio.sleep(duration)


class SparklineDashboard:
    """Live dashboard with enhanced project visualization and UX"""

    def __init__(self, kb=None):
        self.kb = kb
        self.pattern_history = []
        self.quality_history = []
        self.max_history = 20
        self.activity_feed = []
        self.max_activity = 5

    def add_data_point(self, patterns_count: int, quality: str):
        """Add a new data point"""
        self.pattern_history.append(patterns_count)
        if len(self.pattern_history) > self.max_history:
            self.pattern_history.pop(0)

        quality_map = {"gold": 3, "silver": 2, "bronze": 1}
        self.quality_history.append(quality_map.get(quality, 0))
        if len(self.quality_history) > self.max_history:
            self.quality_history.pop(0)

    def add_activity(self, activity_type: str, description: str):
        """Add real-time activity to the feed"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.activity_feed.append({
            "time": timestamp,
            "type": activity_type,
            "description": description
        })

        if len(self.activity_feed) > self.max_activity:
            self.activity_feed.pop(0)

    def get_active_project(self) -> str:
        """Detect current active project from working directory"""
        import os
        from pathlib import Path
        current_dir = Path.cwd().name
        return current_dir

    def get_project_summary_cards(self) -> List[str]:
        """Generate clean project summary cards"""
        if not self.kb:
            return ["📁 No knowledge base connection"]

        current_project = self.get_active_project()
        cards = []

        try:
            # Get current project stats
            current_stats = self.kb.get_statistics(current_project)
            total = current_stats.get('patterns', 0)
            gold = current_stats.get('gold', 0)
            silver = current_stats.get('silver', 0)
            bronze = current_stats.get('bronze', 0)

            # Get overall stats
            overall_stats = self.kb.get_statistics()
            total_projects = overall_stats.get('projects', 0)
            total_patterns = overall_stats.get('total_patterns', 0)

            # Current project card (always active)
            if total > 0:
                cards.append(f"📁 {current_project} (ACTIVE)    🥇 {gold} gold  📊 {total} total  🕐 active")

            # Add summary of all projects if there are multiple
            if total_projects > 1:
                other_patterns = total_patterns - total
                other_projects = total_projects - 1
                if other_patterns > 0:
                    cards.append(f"📂 {other_projects} other projects    📊 {other_patterns} patterns  🕐 various times")

            # If no patterns yet, show encouragement
            if not cards:
                cards.append(f"📁 {current_project} (ACTIVE)    🚀 Ready to learn patterns!")

        except Exception as e:
            # Fallback if anything goes wrong
            cards = [f"📁 {current_project} (ACTIVE)    📊 Monitoring for patterns..."]

        return cards

    def get_live_activity_stream(self) -> List[str]:
        """Generate live activity stream"""
        if not self.activity_feed:
            return [
                "🔍 Scanning: ~/.claude/projects/",
                "✨ Ready to discover patterns...",
                "📝 Monitoring for new sessions..."
            ]

        stream = []
        for activity in self.activity_feed:
            icon = {
                "scan": "🔍",
                "pattern": "✨",
                "classify": "📝",
                "error": "⚠️"
            }.get(activity["type"], "📋")

            stream.append(f"[{activity['time']}] {icon} {activity['description']}")

        return stream

    def get_quick_actions(self) -> str:
        """Generate enhanced quick actions panel"""
        return """🎯 [bold]Interactive Commands[/bold]
[cyan]q[/cyan] Query patterns       [cyan]s[/cyan] Show statistics      [cyan]h[/cyan] Help system
[cyan]w[/cyan] Mark as win         [cyan]f[/cyan] Mark as fail         [cyan]t[/cyan] Tutorial
[cyan]p[/cyan] Switch projects     [cyan]ESC[/cyan] Exit monitoring

[dim]💡 Tip: Press keys while monitoring to interact[/dim]"""

    def get_cross_project_insights(self) -> List[str]:
        """Generate smart cross-project insights"""
        if not self.kb:
            return ["💭 Connect knowledge base for insights"]

        try:
            overall_stats = self.kb.get_statistics()
            current_project = self.get_active_project()
            current_stats = self.kb.get_statistics(current_project)

            insights = []

            # Pattern count insights
            total_patterns = overall_stats.get('total_patterns', 0)
            total_projects = overall_stats.get('projects', 0)
            current_patterns = current_stats.get('patterns', 0)

            if total_patterns > 0:
                if total_projects > 1:
                    avg_patterns = total_patterns / max(total_projects, 1)
                    insights.append(f"• {total_patterns} patterns across {total_projects} projects (avg: {avg_patterns:.1f})")
                else:
                    insights.append(f"• {total_patterns} patterns learned from {current_project}")

            # Current project insights
            if current_patterns > 0:
                gold_count = current_stats.get('gold', 0)
                if gold_count > 0:
                    insights.append(f"• {current_project} has {gold_count} gold-quality patterns")

            # Activity insights
            if total_patterns > 10:
                insights.append("• Knowledge base is growing rapidly! 🚀")
            elif total_patterns > 0:
                insights.append("• Building knowledge from your coding sessions")
            else:
                insights.append("• Ready to learn from your first coding session")

            # Learning status
            insights.append("• Auto-learning from Claude Code telemetry")

            if not insights:
                insights = ["💭 Start coding to see intelligent insights!"]

        except Exception as e:
            insights = ["💭 Knowledge base connected and ready"]

        return insights

    def create_sparkline(self, data: List[int]) -> str:
        """Create a sparkline from data"""
        if not data:
            return ""

        spark_chars = "▁▂▃▄▅▆▇█"
        max_val = max(data) if max(data) > 0 else 1
        min_val = min(data)

        sparkline = ""
        for val in data:
            normalized = (val - min_val) / (max_val - min_val) if max_val != min_val else 0
            index = int(normalized * (len(spark_chars) - 1))
            sparkline += spark_chars[index]

        return sparkline

    def render(self) -> Table:
        """Render the enhanced dashboard as a clean table"""
        from rich.table import Table
        from rich.text import Text
        from rich.panel import Panel
        import os

        # Create main table
        table = Table(show_header=True, header_style="bold magenta", box=None, expand=True)
        table.add_column("Metric", style="cyan", width=25)
        table.add_column("Value", style="green", width=50)
        table.add_column("Status", style="yellow", width=40)

        # Active project and summary
        current_project = self.get_active_project()
        project_cards = self.get_project_summary_cards()

        # Show active project prominently
        table.add_row(
            "🎯 Currently Working On",
            f"[bold green]{current_project}[/bold green]",
            "✨ Learning from your code"
        )

        # Project breakdown
        if len(project_cards) > 1:
            projects_display = "\n".join(project_cards[:3])  # Show top 3
            table.add_row(
                "📊 All Projects",
                projects_display,
                f"Growing nicely! 🌱\nMonitoring ~/.claude/projects/"
            )
        else:
            table.add_row(
                "📊 Project Stats",
                project_cards[0] if project_cards else "No patterns yet",
                "Ready to learn! 🚀"
            )

        return table

    def render_with_panels(self) -> Layout:
        """Render as multi-panel layout with all UX improvements"""

        # Create layout with sections
        layout = Layout()

        # Main dashboard table
        main_table = self.render()

        # Live activity stream
        activity_lines = self.get_live_activity_stream()
        activity_content = "\n".join(activity_lines)
        activity_panel = Panel(
            activity_content,
            title="🔄 Live Activity",
            border_style="blue",
            height=8
        )

        # Quick actions
        actions_content = self.get_quick_actions()
        actions_panel = Panel(
            actions_content,
            title="⚡ Quick Actions",
            border_style="green",
            height=6
        )

        # Cross-project insights
        insights = self.get_cross_project_insights()
        insights_content = "\n".join(insights)
        insights_panel = Panel(
            insights_content,
            title="🌟 Smart Insights",
            border_style="yellow",
            height=6
        )

        # Arrange layout
        layout.split_column(
            Layout(main_table, size=8),
            Layout().split_row(
                Layout(activity_panel),
                Layout().split_column(
                    Layout(actions_panel),
                    Layout(insights_panel)
                )
            )
        )

        return layout


class ProgressAnimation:
    """Smooth progress animations for batch operations"""

    @staticmethod
    async def scan_animation(total_items: int, operation: str = "Scanning"):
        """Animated progress bar for scanning operations"""

        with Progress(
            TextColumn("[bold blue]{task.description}"),
            BarColumn(bar_width=30),
            TaskProgressColumn(),
            TextColumn("[cyan]{task.fields[status]}"),
            console=console,
            transient=True
        ) as progress:

            task = progress.add_task(
                f"{operation}...",
                total=total_items,
                status="Initializing..."
            )

            statuses = [
                "Finding patterns...",
                "Analyzing complexity...",
                "Detecting anti-patterns...",
                "Building connections...",
                "Learning insights..."
            ]

            for i in range(total_items):
                # Update with random status
                status = random.choice(statuses)
                progress.update(task, advance=1, status=status)

                # Simulate work with small delay
                await asyncio.sleep(random.uniform(0.05, 0.15))

            progress.update(task, status="✅ Complete!")
            await asyncio.sleep(0.5)


class InteractiveMonitor:
    """Interactive monitoring dashboard with hotkey support"""

    def __init__(self, kb=None):
        self.feed = PatternDiscoveryFeed()
        self.dashboard = SparklineDashboard(kb=kb)
        self.kb = kb
        self.keyboard = KeyboardHandler()
        self.help_system = HelpSystem()
        self.current_mode = "monitoring"  # monitoring, help, tutorial
        self.tutorial_step = 0

    async def handle_keypress(self, key: str) -> bool:
        """Handle keyboard input. Returns True to continue, False to exit"""

        if self.current_mode == "help":
            # Any key exits help
            self.current_mode = "monitoring"
            return True

        elif self.current_mode == "tutorial":
            if key.lower() == 'q':
                self.current_mode = "monitoring"
                return True
            elif key.lower() == 'n' and self.tutorial_step < 4:
                self.tutorial_step += 1
                return True
            elif key.lower() == 'p' and self.tutorial_step > 0:
                self.tutorial_step -= 1
                return True
            return True

        # Main monitoring mode
        if key == '\x1b':  # ESC key
            return False
        elif key.lower() == 'h':
            self.current_mode = "help"
            return True
        elif key.lower() == 't':
            self.current_mode = "tutorial"
            self.tutorial_step = 0
            return True
        elif key.lower() == 'q':
            await self._handle_query()
            return True
        elif key.lower() == 's':
            await self._handle_stats()
            return True
        elif key.lower() == 'w':
            await self._handle_win()
            return True
        elif key.lower() == 'f':
            await self._handle_fail()
            return True
        elif key.lower() == 'p':
            await self._handle_project_switch()
            return True

        return True

    async def _handle_query(self):
        """Handle query hotkey"""
        self.dashboard.add_activity("pattern", "💭 Press 'cache query \"your search\"' in another terminal")

    async def _handle_stats(self):
        """Handle stats hotkey"""
        if self.kb:
            stats = self.kb.get_statistics()
            patterns = stats.get('total_patterns', 0)
            projects = stats.get('projects', 0)
            self.dashboard.add_activity("pattern", f"📊 {patterns} patterns across {projects} projects")

    async def _handle_win(self):
        """Handle win hotkey"""
        self.dashboard.add_activity("pattern", "🎉 Use 'cache win' in terminal to mark current work as successful")

    async def _handle_fail(self):
        """Handle fail hotkey"""
        self.dashboard.add_activity("pattern", "📝 Use 'cache fail \"reason\"' in terminal to learn from failures")

    async def _handle_project_switch(self):
        """Handle project switch hotkey"""
        self.dashboard.add_activity("pattern", "🔄 Use 'cache project switch' to change active project")

    def render_current_view(self):
        """Render the appropriate view based on current mode"""

        if self.current_mode == "help":
            help_content = self.help_system.get_help_content()
            return Panel(
                help_content,
                title="🆘 Claude Cache Help",
                border_style="cyan",
                expand=True
            )

        elif self.current_mode == "tutorial":
            tutorial_content = self.help_system.get_tutorial_content()
            step_content = tutorial_content[self.tutorial_step]
            return Panel(
                step_content,
                title=f"🎓 Tutorial ({self.tutorial_step + 1}/5)",
                border_style="yellow",
                expand=True
            )

        else:
            # Normal monitoring view
            return self.dashboard.render_with_panels()

    async def monitor(self, duration: float = 30.0):
        """Run interactive monitoring with keyboard support"""

        # Initialize with current data from knowledge base
        if self.kb:
            overall_stats = self.kb.get_statistics()
            self.dashboard.add_activity("scan", f"Connected to knowledge base with {overall_stats.get('total_patterns', 0)} patterns")

        # Setup terminal for raw input
        old_settings = self.keyboard.setup_raw_mode()

        try:
            with Live(self.render_current_view(), refresh_per_second=2, console=console) as live:
                start_time = time.time()
                last_pattern_count = 0

                while time.time() - start_time < duration:
                    # Check for keyboard input
                    key = self.keyboard.get_key_non_blocking()
                    if key:
                        should_continue = await self.handle_keypress(key)
                        if not should_continue:
                            break

                    # Only update monitoring data in monitoring mode
                    if self.current_mode == "monitoring":
                        # Check for real pattern updates
                        if self.kb:
                            current_stats = self.kb.get_statistics()
                            current_pattern_count = current_stats.get('total_patterns', 0)

                            # Detect new patterns
                            if current_pattern_count > last_pattern_count:
                                new_patterns = current_pattern_count - last_pattern_count
                                self.dashboard.add_activity("pattern", f"Discovered {new_patterns} new pattern(s)")
                                last_pattern_count = current_pattern_count

                        # Simulate occasional scanning activity to show it's alive
                        if random.random() > 0.85:
                            activities = [
                                ("scan", "Scanning recent Claude Code sessions"),
                                ("scan", "Monitoring session logs for patterns"),
                                ("classify", "Analyzing code quality patterns"),
                                ("scan", "Processing telemetry data")
                            ]
                            activity_type, description = random.choice(activities)
                            self.dashboard.add_activity(activity_type, description)

                    # Update the display
                    live.update(self.render_current_view())
                    await asyncio.sleep(0.1)  # Faster refresh for responsiveness

        finally:
            # Restore terminal settings
            self.keyboard.restore_terminal(old_settings)


# Keep the old class for backward compatibility
class LivePatternMonitor(InteractiveMonitor):
    """Alias for backward compatibility"""
    pass


# Convenience functions for CLI integration
async def show_thinking(message: str = None, duration: float = 2.0):
    """Show thinking animation"""
    spinner = ThinkingSpinner()
    if message:
        console.print(f"[cyan]{message}[/cyan]")
    await spinner.run(duration)


async def show_discovery_feed(patterns: List[Dict]):
    """Show pattern discovery feed"""
    feed = PatternDiscoveryFeed()
    await feed.animate(patterns)


async def show_toast(message: str, type: str = "info"):
    """Show notification toast"""
    await NotificationToast.show(message, type)


async def show_progress(total: int, operation: str = "Processing"):
    """Show progress animation"""
    await ProgressAnimation.scan_animation(total, operation)


async def start_live_monitor(duration: float = 30.0, kb=None):
    """Start live monitoring display with knowledge base connection"""
    monitor = LivePatternMonitor(kb=kb)
    await monitor.monitor(duration)