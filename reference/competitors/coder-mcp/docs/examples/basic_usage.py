"""
Basic usage examples for coder-mcp
"""

import asyncio

from coder_mcp import ModularMCPServer


async def main():
    # Initialize the server
    server = ModularMCPServer()
    await server.initialize()

    # Example 1: Read a file
    result = await server.handle_tool_call("read_file", {"path": "README.md"})
    print(f"File content length: {len(result['data']['content'])}")

    # Example 2: Search for code
    search_results = await server.handle_tool_call(
        "search_files", {"pattern": "async def", "file_pattern": "*.py"}
    )
    print(f"Found {len(search_results['data']['matches'])} async functions")

    # Example 3: Analyze code
    analysis = await server.handle_tool_call("analyze_code", {"path": "coder_mcp/server.py"})
    print(f"Code metrics: {analysis['data']['metrics']}")


if __name__ == "__main__":
    asyncio.run(main())
