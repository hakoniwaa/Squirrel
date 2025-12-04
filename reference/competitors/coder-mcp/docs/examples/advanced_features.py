"""
Advanced features examples for coder-mcp
"""

import asyncio

from coder_mcp import ModularMCPServer


async def main():
    # Initialize with custom configuration
    server = ModularMCPServer()
    await server.initialize()

    # Example 1: Context-aware search
    await server.handle_tool_call("initialize_context", {"force_refresh": True})

    await server.handle_tool_call(
        "search_context",
        {"query": "functions that handle file operations", "search_type": "semantic"},
    )

    # Example 2: Code scaffolding
    await server.handle_tool_call(
        "scaffold_feature",
        {
            "feature_type": "api_endpoint",
            "name": "UserAuth",
            "options": {"include_tests": True, "framework": "fastapi"},
        },
    )

    # Example 3: Project-wide analysis
    await server.handle_tool_call(
        "analyze_project", {"include_dependencies": True, "generate_report": True}
    )

    # Example 4: Smart code improvements
    await server.handle_tool_call(
        "generate_improvement_roadmap",
        {"focus_areas": ["performance", "security"], "time_frame": "short_term"},
    )


if __name__ == "__main__":
    asyncio.run(main())
