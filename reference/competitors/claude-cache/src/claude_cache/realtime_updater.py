"""Real-time context updates for Claude Cache"""

import threading
import time
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime
from rich.console import Console

console = Console()


class RealtimeContextUpdater:
    """Automatically update context files when new patterns are detected"""

    def __init__(self, knowledge_base, context_injector, silent=False):
        self.kb = knowledge_base
        self.injector = context_injector
        self.update_thread = None
        self.stop_event = threading.Event()
        self.last_update_times = {}
        self.update_interval = 30  # Update every 30 seconds if changes detected
        self.silent = silent

    def start(self):
        """Start real-time context updates in background thread"""
        if self.update_thread and self.update_thread.is_alive():
            return

        self.stop_event.clear()
        self.update_thread = threading.Thread(target=self._update_loop, daemon=True)
        self.update_thread.start()
        if not self.silent:
            console.print("[green]✓ Real-time context updates enabled[/green]")

    def stop(self):
        """Stop real-time updates"""
        self.stop_event.set()
        if self.update_thread:
            self.update_thread.join(timeout=5)

    def _update_loop(self):
        """Main update loop running in background"""
        while not self.stop_event.is_set():
            try:
                self._check_and_update_contexts()
            except Exception as e:
                # Log errors but keep running
                pass

            # Sleep with interruptible wait
            self.stop_event.wait(self.update_interval)

    def _check_and_update_contexts(self):
        """Check for changes and update context files if needed"""
        projects = self._get_active_projects()

        for project in projects:
            if self._has_new_patterns(project):
                self._update_project_context(project)

    def _get_active_projects(self) -> list:
        """Get list of projects with recent activity"""
        # Get projects from the last 24 hours
        import sqlite3
        conn = sqlite3.connect(self.kb.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT DISTINCT project_name
            FROM success_patterns
            WHERE datetime(created_at) > datetime('now', '-1 day')
        """)

        projects = [row[0] for row in cursor.fetchall()]
        conn.close()

        return projects

    def _has_new_patterns(self, project: str) -> bool:
        """Check if project has new patterns since last update"""
        import sqlite3
        conn = sqlite3.connect(self.kb.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT MAX(created_at)
            FROM success_patterns
            WHERE project_name = ?
        """, (project,))

        result = cursor.fetchone()
        conn.close()

        if not result or not result[0]:
            return False

        last_pattern_time = datetime.fromisoformat(result[0])
        last_update = self.last_update_times.get(project)

        if not last_update or last_pattern_time > last_update:
            return True

        return False

    def _update_project_context(self, project: str):
        """Update context files for a project"""
        try:
            # Generate new context
            self.injector.generate_all_commands(project)
            self.injector.export_commands_to_claude_md(project)

            # Record update time
            self.last_update_times[project] = datetime.now()

            # Show notification (subtle, not spammy)
            if not self.silent:
                console.print(f"[dim cyan]↻ Updated context for {project}[/dim cyan]")

        except Exception as e:
            pass  # Silently fail to avoid disrupting main flow

    def notify_pattern_found(self, project: str, pattern: Dict[str, Any]):
        """Called when a new successful pattern is detected"""
        # Trigger immediate update for high-value patterns
        if pattern.get('success_score', 0) > 0.9:
            threading.Thread(
                target=self._update_project_context,
                args=(project,),
                daemon=True
            ).start()

            # Celebratory message for great patterns
            if not self.silent:
                console.print(f"[bold green]🎉 Excellent pattern detected in {project}![/bold green]")


class HotReloadWatcher:
    """Watch for config changes and hot-reload settings"""

    def __init__(self, config_path: Path = None):
        if config_path is None:
            config_path = Path("config.yaml")

        self.config_path = config_path
        self.last_modified = None
        self.watch_thread = None
        self.stop_event = threading.Event()

    def start(self):
        """Start watching config file for changes"""
        if not self.config_path.exists():
            return

        self.last_modified = self.config_path.stat().st_mtime
        self.stop_event.clear()

        self.watch_thread = threading.Thread(target=self._watch_loop, daemon=True)
        self.watch_thread.start()

    def stop(self):
        """Stop watching"""
        self.stop_event.set()
        if self.watch_thread:
            self.watch_thread.join(timeout=5)

    def _watch_loop(self):
        """Watch for config file changes"""
        while not self.stop_event.is_set():
            try:
                if self.config_path.exists():
                    current_mtime = self.config_path.stat().st_mtime

                    if current_mtime != self.last_modified:
                        self.last_modified = current_mtime
                        self._reload_config()

            except Exception:
                pass

            self.stop_event.wait(2)  # Check every 2 seconds

    def _reload_config(self):
        """Reload configuration"""
        console.print("[yellow]⚙ Config changed, reloading settings...[/yellow]")

        # Import and reload config module
        try:
            import importlib
            from . import config

            importlib.reload(config)
            console.print("[green]✓ Config reloaded successfully[/green]")

        except Exception as e:
            console.print(f"[red]✗ Config reload failed: {e}[/red]")