#!/usr/bin/env python3
"""
Run the MCP server with dynamic project-specific configuration
"""

import asyncio
import hashlib
import logging
import os
import sys
from pathlib import Path

from coder_mcp.server import main

# Add the current directory to the path so we can import the coder_mcp package
sys.path.insert(0, os.path.abspath("."))


def get_project_identifier(workspace_path: str) -> tuple[str, str]:
    """
    Generate a unique identifier for the project based on its path.
    Returns: (short_name, hash_id)
    """
    path = Path(workspace_path)

    # Get the project name from the last directory
    project_name = path.name.lower()

    # Clean the project name (remove special chars, limit length)
    clean_name = "".join(c if c.isalnum() or c in "-_" else "_" for c in project_name)[:20]

    # Generate a short hash of the full path for uniqueness
    path_hash = hashlib.md5(str(path).encode(), usedforsecurity=False).hexdigest()[:8]

    return clean_name, path_hash


def setup_dynamic_redis_config():
    """
    Dynamically configure Redis isolation based on the project workspace.
    """
    # Get workspace root from environment or current directory
    workspace_root = os.getenv("MCP_WORKSPACE_ROOT", str(Path.cwd()))

    # Generate project-specific identifiers
    project_name, project_hash = get_project_identifier(workspace_root)

    # Create unique Redis namespace
    # Format: projectname_hash:doc:
    vector_prefix = f"{project_name}_{project_hash}:doc:"
    vector_index = f"{project_name}_{project_hash}_vectors"

    # Set environment variables for coder-mcp to use
    os.environ["VECTOR_PREFIX"] = vector_prefix
    os.environ["REDIS_VECTOR_INDEX"] = vector_index

    # Log configuration (to stderr to not interfere with MCP protocol)
    print("=== Dynamic Redis Configuration ===", file=sys.stderr)
    print(f"Project: {workspace_root}", file=sys.stderr)
    print(f"Project Name: {project_name}", file=sys.stderr)
    print(f"Project Hash: {project_hash}", file=sys.stderr)
    print(f"Vector Prefix: {vector_prefix}", file=sys.stderr)
    print(f"Vector Index: {vector_index}", file=sys.stderr)
    print("==================================", file=sys.stderr)

    return project_name, project_hash


if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    try:
        # Set up dynamic Redis configuration for project-specific vector storage
        setup_dynamic_redis_config()

        # Run the server
        asyncio.run(main())

    except KeyboardInterrupt:
        # Silent shutdown
        pass
    except Exception as e:
        print(f"Fatal error: {e}", file=sys.stderr)
        sys.exit(1)
