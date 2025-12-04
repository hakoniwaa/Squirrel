"""
Coder MCP Server - Enhanced MCP implementation with Redis vector search
"""

# Load .env.mcp file early to ensure environment variables are available
# This allows MCP_WORKSPACE_ROOT and other config to work as expected
from pathlib import Path

try:
    from dotenv import load_dotenv

    env_file = Path.cwd() / ".env.mcp"
    if env_file.exists():
        load_dotenv(env_file, override=True)
except ImportError:
    # dotenv is optional - gracefully handle if not installed
    pass

__version__ = "4.0.0"
__author__ = "Enhanced MCP Team"

from .code_analyzer import CodeAnalyzer
from .core import ConfigurationManager

# Make key components importable
from .server import ModularMCPServer, main
from .template_manager import TemplateManager

__all__ = ["ModularMCPServer", "ConfigurationManager", "CodeAnalyzer", "TemplateManager", "main"]
