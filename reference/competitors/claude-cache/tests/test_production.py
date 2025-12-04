#!/usr/bin/env python3
"""Production test for unified search across all content types"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from claude_cache.knowledge_base import KnowledgeBase
from claude_cache.vector_search import VectorSearchEngine
from rich.console import Console
from rich.table import Table
import json
import tempfile
import shutil

console = Console()

def test_production_unified_search():
    """Test that unified search works across all content types"""

    console.print("\n[bold cyan]Production Test: Unified Search[/bold cyan]\n")

    # Create temporary database for testing
    temp_dir = tempfile.mkdtemp()
    test_db = os.path.join(temp_dir, "test_cache.db")

    try:
        # Initialize with test database
        kb = KnowledgeBase(db_path=test_db)

        # Check vector search mode
        caps = kb.vector_search.get_capabilities()
        console.print(f"Search Mode: [bold]{caps['mode']}[/bold]")
        console.print(f"Model: {caps['model']}\n")

        # 1. Add documentation
        console.print("[yellow]1. Adding documentation...[/yellow]")
        docs = [
            {
                "project": "auth-service",
                "file": "README.md",
                "type": "readme",
                "content": json.dumps({
                    "lessons": [
                        "Use JWT tokens for stateless authentication",
                        "Implement refresh token rotation for security"
                    ],
                    "warnings": [
                        "Never store passwords in plain text",
                        "Always validate JWT signatures"
                    ]
                })
            },
            {
                "project": "database-layer",
                "file": "docs/pooling.md",
                "type": "technical",
                "content": json.dumps({
                    "lessons": [
                        "Use connection pooling for PostgreSQL",
                        "Set pool size based on CPU cores"
                    ],
                    "best_practices": [
                        "Monitor connection pool health",
                        "Implement connection timeout handling"
                    ]
                })
            }
        ]

        for doc in docs:
            kb.store_documentation(
                project_name=doc["project"],
                file_path=doc["file"],
                doc_type=doc["type"],
                content=doc["content"],
                extracted_at="2025-01-21 12:00:00"
            )
            console.print(f"  ✓ Added {doc['project']}/{doc['file']}")

        # 2. Add patterns
        console.print("\n[yellow]2. Adding patterns...[/yellow]")
        patterns = [
            {
                "pattern": {
                    "user_request": "Fix authentication bug with JWT validation",
                    "approach": "Fixed authentication bug by implementing proper JWT validation with signature verification",
                    "request_type": "bug-fix",
                    "files_involved": ["auth.js", "jwt-validator.js"],
                    "solution_steps": ["Added JWT signature validation", "Implemented token expiry check"],
                    "tags": ["auth", "security", "jwt"]
                },
                "project": "auth-service"
            },
            {
                "pattern": {
                    "user_request": "Optimize database performance",
                    "approach": "Optimized database queries with connection pooling to reduce overhead",
                    "request_type": "performance",
                    "files_involved": ["db-config.js", "pool.js"],
                    "solution_steps": ["Configured connection pool", "Set optimal pool size"],
                    "tags": ["database", "performance", "pooling"]
                },
                "project": "database-layer"
            },
            {
                "pattern": {
                    "user_request": "Add network timeout handling",
                    "approach": "Added comprehensive error handling for network timeouts",
                    "request_type": "reliability",
                    "files_involved": ["network.js", "error-handler.js"],
                    "solution_steps": ["Added timeout detection", "Implemented retry logic"],
                    "tags": ["error-handling", "network", "reliability"]
                },
                "project": "api-gateway"
            }
        ]

        for item in patterns:
            kb.store_success_pattern(
                pattern=item["pattern"],
                project_name=item["project"],
                success_score=0.9
            )
            console.print(f"  ✓ Added pattern for {item['project']}")

        # 3. Test unified search
        console.print("\n[yellow]3. Testing unified search...[/yellow]\n")

        test_queries = [
            ("authentication", "Should find both docs and patterns about auth"),
            ("database pooling", "Should find pooling documentation and patterns"),
            ("JWT tokens", "Should find JWT-related content"),
            ("error handling", "Should find error handling patterns"),
            ("connection timeout", "Should find timeout-related content")
        ]

        for query, description in test_queries:
            console.print(f"[cyan]Query: '{query}'[/cyan]")
            console.print(f"[dim]{description}[/dim]")

            results = kb.unified_search(query, limit=5)

            if results:
                # Create result table
                table = Table(show_header=False, box=None, padding=(0, 2))
                table.add_column("", style="green", width=3)
                table.add_column("Type", style="yellow", width=12)
                table.add_column("Content", style="white", width=50)
                table.add_column("Score", style="cyan", width=8)

                for i, result in enumerate(results[:3], 1):
                    content_type = result.get('type', 'unknown')
                    content = result.get('content', '')[:60] + "..."
                    score = result.get('similarity', result.get('confidence', 0))

                    # Format type with emoji
                    if content_type == 'documentation':
                        type_str = "📚 doc"
                    elif content_type == 'pattern':
                        type_str = "🧠 pattern"
                    else:
                        type_str = content_type

                    table.add_row(
                        f"{i}.",
                        type_str,
                        content,
                        f"{score:.3f}"
                    )

                console.print(table)
            else:
                console.print("  [red]No results found[/red]")

            console.print()

        # 4. Verify both content types are searchable
        console.print("[yellow]4. Verifying content type coverage...[/yellow]")

        # Search for something that should return both types
        mixed_results = kb.unified_search("authentication security", limit=10)

        has_docs = any(r.get('type') == 'documentation' for r in mixed_results)
        has_patterns = any(r.get('type') == 'pattern' for r in mixed_results)

        if has_docs and has_patterns:
            console.print("[green]✓ Both documentation and patterns are searchable[/green]")
        else:
            if not has_docs:
                console.print("[red]✗ Documentation not found in search[/red]")
            if not has_patterns:
                console.print("[red]✗ Patterns not found in search[/red]")

        # 5. Test project filtering
        console.print("\n[yellow]5. Testing project filtering...[/yellow]")

        auth_results = kb.unified_search("security", project_name="auth-service", limit=5)
        console.print(f"Results for 'auth-service': {len(auth_results)} items")

        db_results = kb.unified_search("pool", project_name="database-layer", limit=5)
        console.print(f"Results for 'database-layer': {len(db_results)} items")

        # Summary
        console.print("\n[bold green]Production Test Summary:[/bold green]")
        console.print(f"  • Search mode: {caps['mode']}")
        console.print(f"  • Documentation indexed: {len(docs)}")
        console.print(f"  • Patterns indexed: {len(patterns)}")
        console.print(f"  • Content types searchable: {'✓' if has_docs and has_patterns else '✗'}")
        console.print(f"  • Project filtering: {'✓' if auth_results and db_results else '✗'}")

        # Performance note
        if caps['mode'] == 'semantic':
            console.print("\n[green]✨ Using semantic search for best results[/green]")
        else:
            console.print("\n[yellow]💡 Using TF-IDF search. Install sentence-transformers for semantic search:[/yellow]")
            console.print("  [cyan]pip install sentence-transformers[/cyan]")

    finally:
        # Cleanup
        shutil.rmtree(temp_dir, ignore_errors=True)
        console.print("\n[dim]Test database cleaned up[/dim]")

if __name__ == "__main__":
    test_production_unified_search()