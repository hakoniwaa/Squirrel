"""Monitor Claude Code log files for changes"""

import os
import json
import time
from pathlib import Path
from typing import Optional, Callable, Dict, Any
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileModifiedEvent
from rich.console import Console

console = Console()


class LogFileHandler(FileSystemEventHandler):
    """Handle file system events for Claude Code logs"""

    def __init__(self, processor_callback: Callable[[str], None]):
        self.processor_callback = processor_callback
        self.processed_files = set()
        self.file_positions = {}

    def on_modified(self, event: FileModifiedEvent):
        """Handle file modification events"""
        if event.is_directory:
            return

        file_path = Path(event.src_path)

        if file_path.suffix == '.jsonl':
            self._process_file_update(str(file_path))

    def on_created(self, event):
        """Handle new file creation"""
        if event.is_directory:
            return

        file_path = Path(event.src_path)

        if file_path.suffix == '.jsonl':
            console.print(f"[green]New log file detected: {file_path.name}[/green]")
            self._process_file_update(str(file_path))

    def _process_file_update(self, file_path: str):
        """Process updates to a file"""
        try:
            current_position = self.file_positions.get(file_path, 0)

            with open(file_path, 'r') as f:
                f.seek(current_position)
                new_content = f.read()

                if new_content:
                    self.processor_callback(file_path)
                    self.file_positions[file_path] = f.tell()

        except Exception as e:
            console.print(f"[red]Error processing {file_path}: {e}[/red]")


class LogWatcher:
    """Watch and monitor Claude Code log files"""

    def __init__(self, log_processor, silent=False):
        self.log_processor = log_processor
        self.observer = None
        self.claude_projects_dir = Path.home() / '.claude' / 'projects'
        self.silent = silent

    def start(self):
        """Start monitoring log files"""
        if not self.claude_projects_dir.exists():
            if not getattr(self, 'silent', False):
                console.print(f"[yellow]Creating Claude projects directory: {self.claude_projects_dir}[/yellow]")
            self.claude_projects_dir.mkdir(parents=True, exist_ok=True)

        handler = LogFileHandler(self.log_processor.process_file)

        self.observer = Observer()
        self.observer.schedule(
            handler,
            str(self.claude_projects_dir),
            recursive=True
        )

        self.observer.start()
        if not getattr(self, 'silent', False):
            console.print(f"[green]✓ Monitoring Claude Code logs in {self.claude_projects_dir}[/green]")

        return self.observer

    def stop(self):
        """Stop monitoring"""
        if self.observer:
            self.observer.stop()
            self.observer.join()
            if not getattr(self, 'silent', False):
                console.print("[yellow]Log monitoring stopped[/yellow]")

    def _clean_project_name(self, raw_name: str) -> str:
        """Clean up project directory names"""
        if raw_name.startswith('-Users-'):
            parts = raw_name.split('-')
            for i, part in enumerate(parts):
                if part in ['Development', 'Documents', 'Projects', 'Code', 'Work']:
                    if i + 1 < len(parts):
                        return '-'.join(parts[i+1:])
            meaningful_parts = [p for p in parts if p and p not in ['Users', '']]
            if meaningful_parts:
                return meaningful_parts[-1]
        return raw_name

    def process_existing_logs(self):
        """Process all existing log files"""
        if not self.claude_projects_dir.exists():
            if not getattr(self, 'silent', False):
                console.print(f"[yellow]Claude projects directory not found at {self.claude_projects_dir}[/yellow]")
                console.print("[yellow]Creating directory for future logs...[/yellow]")
            self.claude_projects_dir.mkdir(parents=True, exist_ok=True)
            return

        log_files = list(self.claude_projects_dir.glob('**/*.jsonl'))

        if not log_files:
            if not getattr(self, 'silent', False):
                console.print(f"[yellow]No existing log files found in {self.claude_projects_dir}[/yellow]")
                console.print("[dim]Logs will be created when you use Claude Code[/dim]")
            return

        # In silent mode, process files without any output
        if getattr(self, 'silent', False):
            # Just process files silently - LogProcessor handles incremental updates
            for log_file in log_files:
                self.log_processor.process_file(str(log_file))
        else:
            # Verbose mode - show progress
            console.print(f"[blue]Processing {len(log_files)} existing log files...[/blue]")

            processed_count = 0
            for log_file in log_files:
                project_name = self._clean_project_name(log_file.parent.name)
                console.print(f"  Processing: {project_name}/{log_file.name}")

                # Process the file - this will handle incremental processing
                self.log_processor.process_file(str(log_file))
                processed_count += 1

            console.print(f"[green]✓ Finished processing {processed_count} log files[/green]")