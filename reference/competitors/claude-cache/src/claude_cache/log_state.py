"""Track log processing state for incremental updates"""

import json
from pathlib import Path
from typing import Dict, Optional
from datetime import datetime

class LogStateTracker:
    """Track which log entries have been processed to enable incremental processing"""

    def __init__(self, state_file: Optional[Path] = None):
        if state_file is None:
            cache_dir = Path.home() / '.claude' / 'knowledge'
            cache_dir.mkdir(parents=True, exist_ok=True)
            state_file = cache_dir / 'processing_state.json'

        self.state_file = state_file
        self.state = self._load_state()
        self.pending_updates = {}

    def _load_state(self) -> Dict:
        """Load processing state from disk"""
        if self.state_file.exists():
            try:
                with open(self.state_file, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                return {}
        return {}

    def save_state(self):
        """Save current processing state to disk"""
        try:
            # Merge pending updates into state
            for file_path, position in self.pending_updates.items():
                # Ensure consistent format
                if isinstance(position, dict):
                    self.state[file_path] = position
                else:
                    self.state[file_path] = position

            with open(self.state_file, 'w') as f:
                json.dump(self.state, f, indent=2, default=str)

            self.pending_updates.clear()
        except IOError as e:
            # Continue even if state can't be saved
            pass

    def get_position(self, file_path: str) -> int:
        """Get the last processed position for a file"""
        file_state = self.state.get(file_path, 0)
        # Handle both old format (int) and new format (dict)
        if isinstance(file_state, dict):
            return file_state.get('position', 0)
        return file_state if isinstance(file_state, int) else 0

    def update_position(self, file_path: str, position: int):
        """Update the processed position for a file"""
        self.pending_updates[file_path] = {
            'position': position,
            'last_processed': datetime.now().isoformat()
        }

        # Auto-save every 10 updates to avoid data loss
        if len(self.pending_updates) >= 10:
            self.save_state()

    def mark_file_complete(self, file_path: str, size: int):
        """Mark a file as fully processed"""
        self.update_position(file_path, size)

    def should_process_file(self, file_path: str) -> bool:
        """Check if a file needs processing"""
        path = Path(file_path)
        if not path.exists():
            return False

        current_size = path.stat().st_size
        last_position = self.get_position(file_path)

        return current_size > last_position

    def get_incremental_lines(self, file_path: str) -> tuple[int, int]:
        """Get the line range to process incrementally"""
        last_position = self.get_position(file_path)
        return last_position, -1  # Process from last position to end

    def cleanup_old_entries(self, days: int = 30):
        """Remove state entries for files that no longer exist or are old"""
        cleaned = 0
        for file_path in list(self.state.keys()):
            path = Path(file_path)
            if not path.exists():
                del self.state[file_path]
                cleaned += 1

        if cleaned > 0:
            self.save_state()

        return cleaned