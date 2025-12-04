# tests/unit/test_file_discovery.py
import tempfile
from pathlib import Path

from coder_mcp.utils.file_discovery import FileDiscovery


def test_file_discovery_respects_mcpignore():
    """Test that file discovery properly ignores patterns"""

    # Create a mock workspace with .venv
    with tempfile.TemporaryDirectory() as tmpdir:
        workspace = Path(tmpdir)

        # Create test structure
        (workspace / "src").mkdir(parents=True)
        (workspace / "src" / "main.py").write_text("# main file")

        (workspace / ".venv" / "lib").mkdir(parents=True)
        (workspace / ".venv" / "lib" / "test.py").write_text("# venv file")

        (workspace / "tests").mkdir(parents=True)
        (workspace / "tests" / "test_main.py").write_text("# test file")

        # Create .mcpignore
        (workspace / ".mcpignore").write_text(".venv/\n")

        discovery = FileDiscovery(workspace)
        files = discovery.get_project_files()

        # Should not include .venv files or .mcpignore
        assert not any(".venv" in str(f) for f in files)
        python_files = [f for f in files if f.suffix == ".py"]
        assert len(python_files) == 2  # Only src/main.py and tests/test_main.py
