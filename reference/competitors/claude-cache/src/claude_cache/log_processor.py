"""Process Claude Code log entries and extract meaningful data"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
from rich.console import Console
from .log_state import LogStateTracker
from .error_pattern_learner import ErrorPatternLearner
from .differential_learner import DifferentialLearner
from .cross_project_intelligence import CrossProjectIntelligence
from .dual_path_detector import DualPathDetector
from .pattern_factory import PatternDetectorFactory

console = Console()


class LogEntry:
    """Represents a single log entry"""

    def __init__(self, data: Dict[str, Any], source_file: str):
        self.data = data
        self.source_file = source_file
        self.type = data.get('type', 'unknown')
        self.timestamp = data.get('timestamp', datetime.now().isoformat())
        self.content = data.get('content', '')
        # Extract cwd from log data - this is the ACTUAL project directory
        self.cwd = data.get('cwd', '')
        # Extract message content properly
        self.message = data.get('message', {})

    @property
    def project_name(self) -> str:
        """Extract project name from cwd field - simple and direct"""
        # Use the cwd field from the log data (most reliable)
        if self.cwd:
            cwd_path = Path(self.cwd)
            project = cwd_path.name

            # Skip common subdirectory names
            if project in ['src', 'lib', 'app', 'client', 'server', 'frontend', 'backend', 'test', 'tests']:
                project = cwd_path.parent.name

            # Simple cleanup
            return self._clean_project_name(project)

        # Fallback for old logs
        path = Path(self.source_file)
        if path.parent.name == 'projects':
            return 'unknown'

        return self._clean_project_name(path.parent.name)

    def _clean_project_name(self, project: str) -> str:
        """Simple project name cleanup - no complex consolidation"""
        import re

        project = project.lower()

        # Remove version numbers (v1.0, v2, etc)
        project = re.sub(r'-v?\d+(\.\d+)*$', '', project)

        # Remove dates (2024-01-01)
        project = re.sub(r'-\d{4}-\d{2}-\d{2}$', '', project)

        # Remove common branch suffixes
        for suffix in ['-main', '-master', '-dev', '-prod', '-test']:
            if project.endswith(suffix):
                return project[:-len(suffix)]

        return project

    def is_user_message(self) -> bool:
        return self.type == 'user_message'

    def is_tool_call(self) -> bool:
        return self.type == 'tool_call'

    def is_assistant_message(self) -> bool:
        return self.type == 'assistant_message'


class SessionTracker:
    """Track and organize log entries by session"""

    def __init__(self):
        self.sessions = {}
        self.current_sessions = {}

    def add_entry(self, entry: LogEntry):
        """Add an entry to the appropriate session"""
        project = entry.project_name

        if project not in self.current_sessions:
            self.current_sessions[project] = {
                'entries': [],
                'start_time': entry.timestamp,
                'user_requests': [],
                'tool_calls': [],
                'file_operations': []
            }

        session = self.current_sessions[project]
        session['entries'].append(entry)

        if entry.is_user_message():
            session['user_requests'].append(entry)
        elif entry.is_tool_call():
            session['tool_calls'].append(entry)
            if entry.data.get('tool') in ['Read', 'Edit', 'Write']:
                session['file_operations'].append(entry)

    def get_current_session(self, project: str) -> Optional[Dict]:
        """Get the current session for a project"""
        return self.current_sessions.get(project)

    def finalize_session(self, project: str):
        """Mark a session as complete"""
        if project in self.current_sessions:
            session = self.current_sessions[project]
            session['end_time'] = datetime.now().isoformat()

            if project not in self.sessions:
                self.sessions[project] = []

            self.sessions[project].append(session)
            del self.current_sessions[project]


class LogProcessor:
    """Process Claude Code log files"""

    def __init__(self, knowledge_base=None):
        self.kb = knowledge_base
        self.session_tracker = SessionTracker()
        self.state_tracker = LogStateTracker()
        self.processed_lines = {}  # Deprecated, using state_tracker now

        # Initialize new intelligent systems
        self.error_learner = ErrorPatternLearner(self.kb) if self.kb else None
        self.differential_learner = DifferentialLearner(self.kb) if self.kb else None
        self.cross_project_intel = CrossProjectIntelligence(self.kb) if self.kb else None
        self.dual_path_detector = DualPathDetector(self.kb) if self.kb else None
        self.session_start_times = {}  # Track session timing
        self.session_entries = {}  # Track entries per session for journey analysis

    def process_file(self, file_path: str):
        """Process a single JSONL log file with incremental processing"""
        if not Path(file_path).exists():
            return  # Silently skip non-existent files

        # Check if file needs processing
        if not self.state_tracker.should_process_file(file_path):
            return  # File hasn't changed since last processing

        start_position = self.state_tracker.get_position(file_path)
        entries_processed = 0
        current_position = 0

        try:
            with open(file_path, 'r') as f:
                # Skip to last processed position
                if start_position > 0:
                    f.seek(start_position)

                for line in f:

                    line = line.strip()
                    if not line:
                        continue

                    try:
                        data = json.loads(line)
                        entry = LogEntry(data, file_path)
                        self.process_entry(entry)
                        entries_processed += 1
                    except json.JSONDecodeError as e:
                        # Silently skip malformed entries to avoid spam
                        pass
                    except Exception as e:
                        # Handle any other parsing errors gracefully
                        if entries_processed == 0:  # Only show error if no entries processed yet
                            console.print(f"[yellow]Warning: Error processing entry: {str(e)[:50]}[/yellow]")

                # Save position after processing
                current_position = f.tell()
                self.state_tracker.update_position(file_path, current_position)

            if entries_processed > 0:
                # Extract project name from file path
                project_name = self._extract_project_name(file_path)
                # Only show messages if we're not in monitoring mode
                if not getattr(self, 'silent_mode', False):
                    console.print(f"[green]✓ Processed {entries_processed} new entries from {project_name}[/green]")
                # Ensure state is saved after successful processing
                self.state_tracker.save_state()

        except FileNotFoundError:
            # Silently skip - file may have been deleted between scanning and processing
            pass
        except PermissionError:
            console.print(f"[yellow]Permission denied reading: {Path(file_path).name}[/yellow]")
            console.print("[dim]Check file permissions or run with appropriate access[/dim]")
        except Exception as e:
            console.print(f"[red]Unexpected error processing {Path(file_path).name}: {str(e)[:100]}[/red]")
            # Continue processing other files even if one fails

    def process_entry(self, entry: LogEntry):
        """Process a single log entry"""
        self.session_tracker.add_entry(entry)

        # Track session timing for differential learning
        project = entry.project_name
        if project not in self.session_start_times:
            self.session_start_times[project] = datetime.now()

        # Collect entries for journey analysis
        session_id = entry.data.get('sessionId', 'unknown')
        if session_id not in self.session_entries:
            self.session_entries[session_id] = []

        # Add entry data for journey tracking
        self.session_entries[session_id].append({
            'type': entry.type,
            'content': entry.content,
            'message': entry.message,
            'timestamp': entry.timestamp,
            'project': entry.project_name,
            'cwd': entry.cwd,
            'session_id': session_id
        })

        if entry.is_user_message():
            self.handle_user_request(entry)
        elif entry.is_tool_call():
            self.handle_tool_call(entry)
        elif entry.is_assistant_message():
            self.handle_assistant_response(entry)

        # Check for errors and learn from them
        if self.error_learner and 'error' in str(entry.content).lower():
            self._process_error_pattern(entry)

        # Analyze journey patterns periodically (every 10 entries)
        if len(self.session_entries[session_id]) % 10 == 0 and self.dual_path_detector:
            self._analyze_journey_patterns(session_id)

    def handle_user_request(self, entry: LogEntry):
        """Extract and classify user intents"""
        # Extract actual content from message structure
        if isinstance(entry.message, dict):
            content = entry.message.get('content', entry.content)
        else:
            content = entry.content

        # Convert content to string if it's not already
        if not isinstance(content, str):
            content = str(content)

        request_type = self.classify_request(content)

        request_data = {
            'content': content,
            'type': request_type,
            'timestamp': entry.timestamp,
            'project': entry.project_name,
            'source': entry.source_file,
            'cwd': entry.cwd  # Include the actual working directory
        }

        if self.kb:
            self.kb.store_request(request_data)

        # Check for relevant global patterns
        if self.cross_project_intel:
            global_patterns = self.cross_project_intel.find_relevant_global_patterns(
                entry.project_name, content
            )
            if global_patterns:
                console.print(f"[cyan]Found {len(global_patterns)} relevant cross-project patterns[/cyan]")

    def handle_tool_call(self, entry: LogEntry):
        """Process tool usage patterns"""
        tool_data = {
            'tool': entry.data.get('tool'),
            'args': entry.data.get('args', {}),
            'success': entry.data.get('success', True),
            'timestamp': entry.timestamp,
            'project': entry.project_name
        }

        if self.kb:
            self.kb.store_tool_usage(tool_data)

    def handle_assistant_response(self, entry: LogEntry):
        """Process assistant responses and extract tool calls"""
        # Check if message content is an array (contains tool calls)
        if isinstance(entry.message, dict):
            message_content = entry.message.get('content', [])
        else:
            message_content = entry.content

        # Process tool calls from assistant messages
        tool_calls_found = []
        text_content = []

        if isinstance(message_content, list):
            for item in message_content:
                if isinstance(item, dict):
                    if item.get('type') == 'tool_use':
                        # Extract tool call information
                        tool_call = {
                            'tool': item.get('name'),
                            'args': item.get('input', {}),
                            'id': item.get('id'),
                            'timestamp': entry.timestamp,
                            'project': entry.project_name
                        }
                        tool_calls_found.append(tool_call)

                        # Store tool usage
                        if self.kb:
                            self.kb.store_tool_usage(tool_call)

                    elif item.get('type') == 'text':
                        text_content.append(item.get('text', ''))
                else:
                    text_content.append(str(item))
        else:
            text_content = [str(message_content)]

        # Combine text content
        combined_content = '\n'.join(text_content)

        response_data = {
            'content': combined_content,
            'reasoning': entry.data.get('reasoning', ''),
            'timestamp': entry.timestamp,
            'project': entry.project_name,
            'tool_calls': tool_calls_found
        }

        if self.kb:
            self.kb.store_response(response_data)

    def _extract_project_name(self, file_path: str) -> str:
        """Extract clean project name from file path"""
        path = Path(file_path)
        # Get the parent directory name (project folder)
        project_dir = path.parent.name

        # Clean up directory-based project names
        if project_dir.startswith('-Users-'):
            # Extract just the actual project name
            parts = project_dir.split('-')
            # Find where "Development" or similar folder ends
            for i, part in enumerate(parts):
                if part in ['Development', 'Documents', 'Projects', 'Code', 'Work']:
                    # Return everything after the common folder
                    if i + 1 < len(parts):
                        return '-'.join(parts[i+1:])
            # If no common folder found, take last meaningful part
            meaningful_parts = [p for p in parts if p and p not in ['Users', '']]
            if meaningful_parts:
                return meaningful_parts[-1]

        return project_dir

    def classify_request(self, content: str) -> str:
        """Classify the type of user request"""
        content_lower = content.lower()

        if any(word in content_lower for word in ['fix', 'bug', 'error', 'broken', 'issue']):
            return 'debugging'
        elif any(word in content_lower for word in ['add', 'create', 'implement', 'build', 'new feature']):
            return 'feature_development'
        elif any(word in content_lower for word in ['test', 'spec', 'validate', 'check']):
            return 'testing'
        elif any(word in content_lower for word in ['refactor', 'clean', 'optimize', 'improve']):
            return 'refactoring'
        elif any(word in content_lower for word in ['explain', 'how', 'what', 'why', 'understand']):
            return 'explanation'
        elif any(word in content_lower for word in ['document', 'readme', 'comment']):
            return 'documentation'
        else:
            return 'other'

    def _process_error_pattern(self, entry: LogEntry):
        """Process potential error patterns"""
        # Get recent entries for context
        session = self.session_tracker.get_current_session(entry.project_name)
        if session and 'entries' in session:
            recent_entries = session['entries'][-10:]  # Last 10 entries

            # Analyze for error patterns
            patterns = self.error_learner.analyze_error_sequence(recent_entries)
            for pattern in patterns:
                self.error_learner.store_error_pattern(pattern)
                console.print(f"[yellow]Learned from error: {pattern.error_type}[/yellow]")

    def _track_pattern_efficiency(self, project: str, pattern_id: str, was_successful: bool):
        """Track efficiency metrics for patterns"""
        if not self.differential_learner or project not in self.session_start_times:
            return

        session_data = {
            'start_time': self.session_start_times[project].isoformat(),
            'end_time': datetime.now().isoformat(),
            'pattern_id': pattern_id,
            'successful': was_successful,
            'entries': self.session_tracker.get_current_session(project).get('entries', [])
        }

        metrics = self.differential_learner.track_session_metrics(session_data)
        console.print(f"[blue]Pattern efficiency: {metrics.time_to_solution.seconds}s[/blue]")

    def _analyze_journey_patterns(self, session_id: str):
        """Analyze session entries to extract journey patterns"""
        if not self.dual_path_detector or session_id not in self.session_entries:
            return

        try:
            entries = self.session_entries[session_id]
            if len(entries) < 3:  # Need at least a few entries for a pattern
                return

            # Analyze the journey
            pattern = self.dual_path_detector.analyze_session_journey(entries)

            if pattern:
                # Store the pattern in the knowledge base
                self.dual_path_detector.store_pattern(pattern)

                # Log based on pattern type
                if pattern.pattern_type.value == 'gold':
                    console.print(f"[gold1]✨ Gold pattern captured: {pattern.key_learning[:50]}[/gold1]")
                elif pattern.pattern_type.value == 'anti':
                    console.print(f"[red]⚠️ Anti-pattern learned: {pattern.anti_patterns[0] if pattern.anti_patterns else 'Avoid this approach'}[/red]")
                elif pattern.pattern_type.value == 'journey':
                    console.print(f"[cyan]🗺️ Journey pattern recorded: {len(pattern.attempts)} attempts to solution[/cyan]")

        except Exception as e:
            # Don't disrupt processing for pattern analysis errors
            if not getattr(self, 'silent_mode', False):
                console.print(f"[dim]Pattern analysis error: {str(e)[:50]}[/dim]")
            pass

    def get_session_summary(self, project: str) -> Optional[Dict]:
        """Get a summary of the current session"""
        session = self.session_tracker.get_current_session(project)

        if not session:
            return None

        return {
            'project': project,
            'start_time': session['start_time'],
            'total_entries': len(session['entries']),
            'user_requests': len(session['user_requests']),
            'tool_calls': len(session['tool_calls']),
            'files_touched': len(session['file_operations'])
        }