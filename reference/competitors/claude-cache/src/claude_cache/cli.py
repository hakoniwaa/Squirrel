"""Command-line interface for Claude Cache"""

import click
import sys
from pathlib import Path
from rich.console import Console
from datetime import datetime

from . import __version__
from .agent import CacheAgent
from .daemon import CacheDaemon

console = Console()

ASCII_ART = """                              claude
 ██████╗ █████╗  ██████╗██╗  ██╗███████╗
██╔════╝██╔══██╗██╔════╝██║  ██║██╔════╝
██║     ███████║██║     ███████║█████╗      v0.9.1
██║     ██╔══██║██║     ██╔══██║██╔══╝   🤖 Intelligent
╚██████╗██║  ██║╚██████╗██║  ██║███████╗    Detection
 ╚═════╝╚═╝  ╚═╝ ╚═════╝╚═╝  ╚═╝╚══════╝"""


@click.group()
@click.version_option(version=__version__, prog_name="cache")
def cli():
    """Claude Cache - Give your AI coding assistant perfect recall

    Quick Start: cache run  (starts background learning + terminal interface)
    For Claude Code: cache-mcp  (run separately for MCP integration)
    """
    pass


@cli.command()
@click.option('--watch/--no-watch', default=True, help='Enable real-time monitoring')
@click.option('--daemon', is_flag=True, help='Run as background daemon')
@click.option('--db', type=click.Path(), help='Custom database path')
def start(watch, daemon, db):
    """Start processing Claude Code logs"""
    if daemon:
        # Run as daemon
        d = CacheDaemon()
        d.start()
    else:
        # Run in foreground
        try:
            agent = CacheAgent(db)
            agent.start(watch=watch)
        except KeyboardInterrupt:
            console.print("\n[yellow]Stopped by user[/yellow]")
            sys.exit(0)
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")
            sys.exit(1)


@cli.command()
@click.option('--db', type=click.Path(), help='Custom database path')
def process(db):
    """Process existing logs without monitoring"""
    try:
        agent = CacheAgent(db)
        agent.process_existing_logs()
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


@cli.command()
@click.argument('query')
@click.option('--project', '-p', help='Filter by project name')
@click.option('--code', is_flag=True, help='Show full code snippets')
@click.option('--preview', is_flag=True, help='Show code preview (first 5 lines)')
@click.option('--gold', is_flag=True, help='Only show gold patterns')
@click.option('--anti', is_flag=True, help='Only show anti-patterns')
@click.option('--journey', is_flag=True, help='Only show journey patterns')
@click.option('--limit', '-n', type=int, default=10, help='Number of results (default: 10)')
@click.option('--db', type=click.Path(), help='Custom database path')
def query(query, project, code, preview, gold, anti, journey, limit, db):
    """Query patterns from the knowledge base with advanced filtering"""
    try:
        agent = CacheAgent(db)

        # Build filter flags
        filters = {
            'show_code': code,
            'show_preview': preview,
            'only_gold': gold,
            'only_anti': anti,
            'only_journey': journey,
            'limit': limit
        }

        agent.query_patterns(query, project, filters)
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


@cli.command()
@click.option('--session-file', type=click.Path(exists=True), help='Analyze specific session file')
@click.option('--recent', is_flag=True, help='Analyze most recent session')
@click.option('--project', '-p', help='Analyze sessions from specific project')
@click.option('--db', type=click.Path(), help='Custom database path')
def analyze(session_file, recent, project, db):
    """Analyze conversation sessions using intelligent detection"""
    try:
        from .intelligent_detector import IntelligentDetector
        from .log_processor import LogProcessor
        import json
        from rich.panel import Panel
        from rich.columns import Columns

        agent = CacheAgent(db)
        detector = IntelligentDetector()
        processor = LogProcessor(agent.kb)

        # Find sessions to analyze
        sessions_to_analyze = []

        if session_file:
            sessions_to_analyze = [Path(session_file)]
        elif recent:
            # Find most recent session
            log_dir = Path.home() / ".claude" / "logs"
            if log_dir.exists():
                sessions = sorted(log_dir.glob("*.jsonl"), key=lambda x: x.stat().st_mtime, reverse=True)
                if sessions:
                    sessions_to_analyze = [sessions[0]]
        elif project:
            # Find sessions for specific project
            log_dir = Path.home() / ".claude" / "logs"
            if log_dir.exists():
                sessions = list(log_dir.glob("*.jsonl"))
                # Filter by project name in filename or content - simplified approach
                sessions_to_analyze = [s for s in sessions if project.lower() in s.name.lower()][:5]
        else:
            # Default: analyze last 3 sessions
            log_dir = Path.home() / ".claude" / "logs"
            if log_dir.exists():
                sessions = sorted(log_dir.glob("*.jsonl"), key=lambda x: x.stat().st_mtime, reverse=True)
                sessions_to_analyze = sessions[:3]

        if not sessions_to_analyze:
            console.print("[yellow]No sessions found to analyze[/yellow]")
            return

        console.print(f"[cyan]📊 Analyzing {len(sessions_to_analyze)} session(s)...[/cyan]\n")

        for session_path in sessions_to_analyze:
            console.print(f"[dim]Session: {session_path.name}[/dim]")

            # Extract session entries
            entries = processor._extract_session_entries(str(session_path))

            if not entries:
                console.print("[dim]  No conversation data found[/dim]\n")
                continue

            # Analyze with intelligent detector
            result = detector.detect(entries)

            # Create analysis panel
            analysis_content = []

            # Success detection
            success_icon = "✅" if result.is_success else "⏳"
            confidence_color = {
                "certain": "bright_green",
                "high": "green",
                "medium": "yellow",
                "low": "orange",
                "uncertain": "red"
            }.get(result.confidence.value, "white")

            analysis_content.append(f"{success_icon} **Success**: {result.is_success} ({result.success_probability:.0%})")
            analysis_content.append(f"🎯 **Confidence**: [{confidence_color}]{result.confidence.value}[/{confidence_color}]")

            if result.problem:
                analysis_content.append(f"🔍 **Problem**: {result.problem[:80]}{'...' if len(result.problem) > 80 else ''}")

            if result.solution and result.is_success:
                analysis_content.append(f"💡 **Solution**: {result.solution[:80]}{'...' if len(result.solution) > 80 else ''}")

            # Pattern quality
            quality_icons = {"gold": "🏆", "silver": "✨", "bronze": "🥉", "anti": "⚠️"}
            quality_icon = quality_icons.get(result.pattern_quality, "📝")
            analysis_content.append(f"{quality_icon} **Quality**: {result.pattern_quality}")

            # Key insights
            if result.key_insights:
                analysis_content.append(f"🔍 **Insights**: {len(result.key_insights)} detected")
                for insight in result.key_insights[:3]:
                    analysis_content.append(f"   • {insight[:60]}{'...' if len(insight) > 60 else ''}")

            # Evidence summary
            evidence = result.evidence
            if evidence:
                conv_score = evidence.get('conversation_analysis', {}).get('score', 0)
                exec_score = evidence.get('execution_results', {}).get('score', 0)
                intent_conf = evidence.get('user_intent', {}).get('confidence', 0)
                behavior_score = evidence.get('behavioral_patterns', {}).get('score', 0)

                analysis_content.append(f"📈 **Signal Strength**:")
                analysis_content.append(f"   • Conversation: {conv_score:.0%}")
                analysis_content.append(f"   • Execution: {exec_score:.0%}")
                analysis_content.append(f"   • User Intent: {intent_conf:.0%}")
                analysis_content.append(f"   • Behavior: {behavior_score:.0%}")

            # Recommendation
            analysis_content.append(f"💭 **Recommendation**: {result.recommendation}")

            panel_content = "\n".join(analysis_content)
            panel = Panel(panel_content, title=f"🤖 Intelligent Analysis", border_style="bright_blue")
            console.print(panel)
            console.print()

    except ImportError:
        console.print("[red]Intelligent detector not available. Install with enhanced features:[/red]")
        console.print("[dim]pip install claude-cache[enhanced][/dim]")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]Analysis error: {e}[/red]")
        sys.exit(1)


@cli.command()
@click.option('--today', is_flag=True, help='Show patterns from today only')
@click.option('--week', is_flag=True, help='Show patterns from last 7 days')
@click.option('--watch', is_flag=True, help='Live monitor new patterns')
@click.option('--project', '-p', help='Filter by project')
@click.option('--db', type=click.Path(), help='Custom database path')
def recent(today, week, watch, project, db):
    """Show recently learned patterns (last 24 hours by default)"""
    try:
        from datetime import datetime, timedelta
        import sqlite3
        from rich.table import Table
        from rich.live import Live
        import time

        agent = CacheAgent(db)
        conn = sqlite3.connect(agent.kb.db_path)
        cursor = conn.cursor()

        # Determine time range
        if today:
            cutoff = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            time_label = "Today"
        elif week:
            cutoff = datetime.now() - timedelta(days=7)
            time_label = "Last 7 Days"
        else:
            cutoff = datetime.now() - timedelta(days=1)
            time_label = "Last 24 Hours"

        if watch:
            # Live monitoring mode
            console.print(f"[bold cyan]🔄 Live Monitoring Patterns[/bold cyan]")
            console.print("[dim]Press Ctrl+C to stop[/dim]\n")

            def generate_table():
                # Query recent patterns
                query = '''
                    SELECT project_name, approach, success_score, created_at
                    FROM success_patterns
                    WHERE created_at > ?
                '''
                params = [cutoff.isoformat()]

                if project:
                    query += ' AND project_name = ?'
                    params.append(project)

                query += ' ORDER BY created_at DESC LIMIT 20'

                cursor.execute(query, params)
                patterns = cursor.fetchall()

                table = Table(title=f"Recent Patterns - {time_label}", show_header=True)
                table.add_column("Time", style="dim", width=15)
                table.add_column("Project", style="cyan", width=20)
                table.add_column("Pattern", style="white", width=60)
                table.add_column("Quality", style="green", width=10)

                for row in patterns:
                    # Format time
                    created_at = datetime.fromisoformat(row[3])
                    time_diff = datetime.now() - created_at
                    if time_diff.total_seconds() < 60:
                        time_str = "just now"
                    elif time_diff.total_seconds() < 3600:
                        time_str = f"{int(time_diff.total_seconds() / 60)}m ago"
                    elif time_diff.total_seconds() < 86400:
                        time_str = f"{int(time_diff.total_seconds() / 3600)}h ago"
                    else:
                        time_str = created_at.strftime("%H:%M")

                    # Format quality
                    score = row[2]
                    if score >= 0.9:
                        quality = "🥇 Gold"
                    elif score >= 0.7:
                        quality = "🥈 Silver"
                    else:
                        quality = "🥉 Bronze"

                    # Format pattern
                    pattern = row[1][:60] + "..." if len(row[1]) > 60 else row[1]

                    table.add_row(time_str, row[0][:20], pattern, quality)

                return table

            with Live(generate_table(), refresh_per_second=1, console=console) as live:
                try:
                    while True:
                        time.sleep(5)
                        live.update(generate_table())
                except KeyboardInterrupt:
                    console.print("\n[yellow]Monitoring stopped[/yellow]")

        else:
            # Static view
            query = '''
                SELECT project_name, approach, success_score, created_at, files_involved
                FROM success_patterns
                WHERE created_at > ?
            '''
            params = [cutoff.isoformat()]

            if project:
                query += ' AND project_name = ?'
                params.append(project)

            query += ' ORDER BY created_at DESC'

            cursor.execute(query, params)
            patterns = cursor.fetchall()

            if not patterns:
                console.print(f"[yellow]No patterns found for {time_label.lower()}[/yellow]")
                return

            console.print(f"\n[bold cyan]📅 Recent Patterns - {time_label}[/bold cyan]")
            console.print(f"[dim]Found {len(patterns)} patterns[/dim]\n")

            # Group by project
            by_project = {}
            for row in patterns:
                proj = row[0]
                if proj not in by_project:
                    by_project[proj] = []
                by_project[proj].append(row)

            for proj_name, proj_patterns in by_project.items():
                console.print(f"\n[bold]{proj_name}[/bold] ({len(proj_patterns)} patterns)")

                for pattern in proj_patterns[:5]:  # Show first 5 per project
                    created_at = datetime.fromisoformat(pattern[3])
                    time_str = created_at.strftime("%H:%M")

                    # Quality indicator
                    score = pattern[2]
                    if score >= 0.9:
                        quality = "🥇"
                    elif score >= 0.7:
                        quality = "🥈"
                    else:
                        quality = "🥉"

                    # Pattern preview
                    approach = pattern[1][:100] + "..." if len(pattern[1]) > 100 else pattern[1]

                    console.print(f"  {quality} {time_str} - {approach}")

                if len(proj_patterns) > 5:
                    console.print(f"  [dim]... and {len(proj_patterns) - 5} more[/dim]")

            # Summary stats
            console.print(f"\n[bold]Summary:[/bold]")
            gold_count = sum(1 for p in patterns if p[2] >= 0.9)
            silver_count = sum(1 for p in patterns if 0.7 <= p[2] < 0.9)
            bronze_count = sum(1 for p in patterns if p[2] < 0.7)

            console.print(f"  🥇 Gold: {gold_count} | 🥈 Silver: {silver_count} | 🥉 Bronze: {bronze_count}")

        conn.close()

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        import traceback
        console.print(f"[dim]{traceback.format_exc()}[/dim]")
        sys.exit(1)


@cli.command()
@click.argument('action', required=False)
@click.argument('project_name', required=False)
@click.option('--db', type=click.Path(), help='Custom database path')
def project(action, project_name, db):
    """Manage project context (set/show/list projects)"""
    try:
        from pathlib import Path
        import json
        import sqlite3

        agent = CacheAgent(db)
        config_file = Path.home() / '.claude' / 'cache_config.json'

        # Ensure config directory exists
        config_file.parent.mkdir(exist_ok=True)

        # Load existing config
        config = {}
        if config_file.exists():
            with open(config_file, 'r') as f:
                config = json.load(f)

        if action == 'set':
            # Set default project
            if not project_name:
                console.print("[red]Please specify a project name[/red]")
                console.print("Usage: cache project set PROJECT_NAME")
                return

            config['default_project'] = project_name
            with open(config_file, 'w') as f:
                json.dump(config, f, indent=2)

            console.print(f"✅ Default project set to: [cyan]{project_name}[/cyan]")
            console.print(f"[dim]All commands will now use this project by default[/dim]")

        elif action == 'list':
            # List all projects with pattern counts
            conn = sqlite3.connect(agent.kb.db_path)
            cursor = conn.cursor()

            cursor.execute('''
                SELECT
                    project_name,
                    COUNT(*) as pattern_count,
                    MAX(created_at) as last_activity
                FROM success_patterns
                GROUP BY project_name
                ORDER BY pattern_count DESC
            ''')

            projects = cursor.fetchall()
            conn.close()

            if not projects:
                console.print("[yellow]No projects found[/yellow]")
                return

            current_default = config.get('default_project')
            current_dir = Path.cwd().name

            console.print("\n[bold cyan]📁 Available Projects[/bold cyan]\n")

            from rich.table import Table
            table = Table(show_header=True, header_style="bold magenta")
            table.add_column("Project", style="cyan")
            table.add_column("Patterns", justify="right")
            table.add_column("Last Activity", style="dim")
            table.add_column("Status", style="green")

            for proj_name, count, last_activity in projects:
                # Format status
                status = ""
                if proj_name == current_default:
                    status = "⭐ Default"
                if proj_name == current_dir:
                    status = (status + " 📍 Current" if status else "📍 Current")

                # Format last activity
                if last_activity:
                    from datetime import datetime
                    dt = datetime.fromisoformat(last_activity)
                    days_ago = (datetime.now() - dt).days
                    if days_ago == 0:
                        activity = "Today"
                    elif days_ago == 1:
                        activity = "Yesterday"
                    else:
                        activity = f"{days_ago}d ago"
                else:
                    activity = "Unknown"

                table.add_row(proj_name, str(count), activity, status)

            console.print(table)

            if current_default:
                console.print(f"\n[dim]Default project: {current_default}[/dim]")
            console.print(f"[dim]Current directory: {current_dir}[/dim]")

        else:
            # Show current project
            current_default = config.get('default_project')
            current_dir = Path.cwd().name

            console.print("\n[bold]Project Context[/bold]")
            console.print(f"  Current directory: [cyan]{current_dir}[/cyan]")

            if current_default:
                console.print(f"  Default project: [green]{current_default}[/green]")
                console.print(f"\n[dim]Commands will use '{current_default}' unless -p is specified[/dim]")
            else:
                console.print(f"  Default project: [yellow]Not set[/yellow]")
                console.print(f"\n[dim]Set a default with: cache project set PROJECT_NAME[/dim]")

            # Show quick stats for current directory project
            stats = agent.kb.get_statistics(current_dir)
            if stats.get('patterns', 0) > 0:
                console.print(f"\n[bold]Current Directory Stats ({current_dir})[/bold]")
                console.print(f"  Patterns: {stats.get('patterns', 0)}")
                console.print(f"  Requests: {stats.get('requests', 0)}")

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


@cli.command()
@click.option('--project', '-p', help='Generate for specific project')
@click.option('--db', type=click.Path(), help='Custom database path')
def generate(project, db):
    """Generate slash commands for Claude Code"""
    try:
        agent = CacheAgent(db)

        if project:
            projects = [project]
        else:
            projects = agent.get_projects()

        if not projects:
            console.print("[yellow]No projects found[/yellow]")
            return

        for proj in projects:
            console.print(f"[blue]Generating commands for {proj}...[/blue]")
            agent.injector.generate_all_commands(proj)
            agent.injector.export_commands_to_claude_md(proj)

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


@cli.command()
@click.option('--project', '-p', help='Filter by project')
@click.option('--db', type=click.Path(), help='Custom database path')
def stats(project, db):
    """Show knowledge base statistics"""
    try:
        from rich.table import Table
        from rich.panel import Panel
        from datetime import datetime

        agent = CacheAgent(db)

        if project:
            # Single project detailed stats
            stats = agent.kb.get_statistics(project)
            console.print(f"\n[bold cyan]📊 Statistics for {project}[/bold cyan]\n")

            # Main metrics
            console.print(Panel(
                f"[bold green]{stats.get('patterns', 0)}[/bold green] Patterns | "
                f"[bold yellow]{stats.get('requests', 0)}[/bold yellow] Requests | "
                f"[bold blue]{stats.get('conventions', 0)}[/bold blue] Conventions",
                title="[bold]Overview[/bold]",
                border_style="cyan"
            ))

            # Pattern types breakdown
            if 'pattern_types' in stats:
                pt = stats['pattern_types']
                console.print("\n[bold]Pattern Quality Distribution:[/bold]")
                console.print(f"  🥇 Gold (first-try): [green]{pt['gold']}[/green]")
                console.print(f"  🥈 Silver (2-3 tries): [yellow]{pt['silver']}[/yellow]")
                console.print(f"  🥉 Bronze (eventually): [dim]{pt['bronze']}[/dim]")

            # Special patterns
            console.print(f"\n[bold]Learning Patterns:[/bold]")
            console.print(f"  ⚠️  Anti-patterns (failures): [red]{stats.get('anti_patterns', 0)}[/red]")
            console.print(f"  🛤️  Journey patterns (paths): [blue]{stats.get('journey_patterns', 0)}[/blue]")

        else:
            # Overall stats with project breakdown
            stats = agent.kb.get_statistics()

            # Header with totals
            console.print("\n[bold cyan]🎯 Claude Cache Knowledge Base Analytics[/bold cyan]\n")

            # Summary panel
            console.print(Panel(
                f"[bold green]{stats.get('total_patterns', 0)}[/bold green] Total Patterns across "
                f"[bold cyan]{stats.get('total_projects', 0)}[/bold cyan] Projects\n"
                f"[bold yellow]{stats.get('total_requests', 0)}[/bold yellow] Total Requests | "
                f"[bold red]{stats.get('total_anti_patterns', 0)}[/bold red] Anti-patterns | "
                f"[bold blue]{stats.get('total_journey_patterns', 0)}[/bold blue] Journeys",
                title="[bold]Global Overview[/bold]",
                border_style="cyan"
            ))

            # Pattern type totals
            if 'pattern_types_total' in stats:
                pt = stats['pattern_types_total']
                console.print("\n[bold]Global Pattern Quality:[/bold]")
                total = pt['gold'] + pt['silver'] + pt['bronze']
                if total > 0:
                    console.print(f"  🥇 Gold: {pt['gold']} ({pt['gold']*100//total}%)")
                    console.print(f"  🥈 Silver: {pt['silver']} ({pt['silver']*100//total}%)")
                    console.print(f"  🥉 Bronze: {pt['bronze']} ({pt['bronze']*100//total}%)")

            # Project breakdown table
            if 'projects' in stats and stats['projects']:
                console.print("\n[bold]📁 Projects Breakdown:[/bold]\n")

                table = Table(show_header=True, header_style="bold magenta")
                table.add_column("Project", style="cyan", no_wrap=True)
                table.add_column("Patterns", justify="right")
                table.add_column("🥇", justify="center", style="green")
                table.add_column("🥈", justify="center", style="yellow")
                table.add_column("🥉", justify="center", style="dim")
                table.add_column("⚠️", justify="center", style="red")
                table.add_column("🛤️", justify="center", style="blue")
                table.add_column("Avg Score", justify="right")
                table.add_column("Last Activity", style="dim")

                for proj in stats['projects']:
                    # Format last activity
                    last_activity = "Unknown"
                    if proj.get('last_activity'):
                        try:
                            dt = datetime.fromisoformat(proj['last_activity'])
                            days_ago = (datetime.now() - dt).days
                            if days_ago == 0:
                                last_activity = "Today"
                            elif days_ago == 1:
                                last_activity = "Yesterday"
                            else:
                                last_activity = f"{days_ago}d ago"
                        except:
                            last_activity = proj['last_activity'][:10]

                    table.add_row(
                        proj['name'][:30],
                        str(proj['patterns']),
                        str(proj.get('gold', 0)),
                        str(proj.get('silver', 0)),
                        str(proj.get('bronze', 0)),
                        str(proj.get('anti_patterns', 0)),
                        str(proj.get('journey_patterns', 0)),
                        f"{proj.get('avg_success_score', 0):.2f}",
                        last_activity
                    )

                console.print(table)
            else:
                console.print("\n[yellow]No projects found. Start using Claude Cache to build your knowledge base![/yellow]")

            # Tips
            console.print("\n[dim]💡 Tips:[/dim]")
            console.print("[dim]  • Use 'cache stats -p PROJECT_NAME' for detailed project stats[/dim]")
            console.print("[dim]  • Use 'cache query \"pattern type:gold\" -p PROJECT' to filter patterns[/dim]")

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        import traceback
        console.print(f"[dim]{traceback.format_exc()}[/dim]")
        sys.exit(1)


@cli.command()
@click.argument('output_file', type=click.Path())
@click.option('--project', '-p', help='Export specific project')
@click.option('--db', type=click.Path(), help='Custom database path')
def export(output_file, project, db):
    """Export knowledge base to JSON file"""
    try:
        agent = CacheAgent(db)
        agent.export_knowledge(output_file, project)
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


@cli.command(name='import')
@click.argument('input_file', type=click.Path(exists=True))
@click.option('--db', type=click.Path(), help='Custom database path')
def import_kb(input_file, db):
    """Import patterns from JSON file"""
    try:
        agent = CacheAgent(db)
        agent.import_knowledge(input_file)
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


@cli.command()
@click.option('--duration', '-d', type=int, default=30, help='Duration in seconds (default: 30)')
@click.option('--db', type=click.Path(), help='Custom database path')
def monitor(duration, db):
    """Interactive monitoring dashboard with hotkeys and help system"""
    try:
        import asyncio
        from .animations import start_live_monitor
        from .agent import CacheAgent

        console.print("[bold cyan]🧠 Claude Cache - Interactive Monitoring[/bold cyan]")
        console.print("[dim]Press keys to interact: [cyan]h[/cyan]=help [cyan]t[/cyan]=tutorial [cyan]q[/cyan]=query [cyan]s[/cyan]=stats [cyan]ESC[/cyan]=exit[/dim]\n")

        # Create agent instance to access knowledge base
        agent = CacheAgent(db)

        # Run enhanced monitor with knowledge base connection
        asyncio.run(start_live_monitor(duration, kb=agent.kb))

    except KeyboardInterrupt:
        console.print("\n[yellow]Monitoring stopped[/yellow]")
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


@cli.command()
@click.option('--confirm', is_flag=True, help='Confirm rebuild without prompt')
@click.option('--db', type=click.Path(), help='Custom database path')
@click.option('--animate', is_flag=True, help='Show animated progress')
def rebuild(confirm, db, animate):
    """Rebuild knowledge base from scratch"""
    try:
        if not confirm:
            if not click.confirm('This will delete all existing patterns. Continue?'):
                console.print("[yellow]Cancelled[/yellow]")
                return

        if animate:
            # Animated rebuild with progress
            import asyncio
            from .animations import show_thinking, show_progress, show_toast

            async def animated_rebuild():
                await show_thinking("Preparing to rebuild knowledge base", 2.0)
                agent = CacheAgent(db)

                # Count existing patterns for progress
                stats = agent.kb.get_statistics()
                total_patterns = stats.get('total_patterns', 0)

                if total_patterns > 0:
                    await show_progress(total_patterns, "Rebuilding patterns")

                agent.rebuild_index()
                await show_toast("✅ Knowledge base rebuilt successfully!", "success")

            asyncio.run(animated_rebuild())
        else:
            agent = CacheAgent(db)
            agent.rebuild_index()
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


@cli.command()
@click.argument('request')
@click.option('--project', '-p', required=True, help='Project name')
@click.option('--db', type=click.Path(), help='Custom database path')
def context(request, project, db):
    """Generate context for a specific request"""
    try:
        agent = CacheAgent(db)
        context = agent.injector.generate_context_for_request(request, project)

        if context:
            console.print(context)
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


@cli.command()
@click.argument('action', default='status', type=click.Choice(['start', 'stop', 'restart', 'status']))
def daemon(action):
    """Manage Claude Cache daemon process"""
    d = CacheDaemon()

    if action == 'start':
        d.start()
    elif action == 'stop':
        d.stop()
    elif action == 'restart':
        d.restart()
    elif action == 'status':
        d.status()


@cli.command()
@click.option('--foreground', '-f', is_flag=True, help='Run in foreground instead of background')
@click.option('--with-mcp', is_flag=True, help='Also start MCP server (usually not needed)')
@click.option('--db', type=click.Path(), help='Custom database path')
def run(foreground, with_mcp, db):
    """Start Claude Cache: background learning + vector search + terminal interface"""
    import subprocess
    import time

    console.print(f"[bold cyan]{ASCII_ART}[/bold cyan]")
    console.print(f"[bold]Starting Claude Cache v{__version__} - Terminal & Learning System[/bold]\n")

    processes = []

    try:
        # Start background learning agent directly (no daemon)
        console.print("🔄 [cyan]Starting background learning system...[/cyan]")
        agent = CacheAgent(db)

        if foreground:
            # Start agent in foreground
            console.print("✅ [green]Background learning active[/green]")
            console.print("\n[dim]Running in foreground mode. Press Ctrl+C to stop.[/dim]")
            agent.start(watch=True)
        else:
            # Start agent as background subprocess
            import subprocess
            import sys

            # Start the agent using cache start command in background
            subprocess.Popen([
                sys.executable, '-c',
                f'from claude_cache.agent import CacheAgent; '
                f'agent = CacheAgent("{db}" if "{db}" != "None" else None); '
                f'agent.start(watch=True)'
            ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

            console.print("✅ [green]Background learning started[/green]")
            time.sleep(1)  # Give agent time to start

        # Start MCP server only if explicitly requested
        if with_mcp:
            console.print("🔗 [cyan]Starting MCP server for Claude Code integration...[/cyan]")
            if foreground:
                console.print("⚠️  [yellow]Cannot run MCP server in foreground mode[/yellow]")
                console.print("    Run 'cache-mcp' separately for Claude Code integration")
            else:
                # Start MCP server as subprocess
                mcp_process = subprocess.Popen(
                    ['cache-mcp'],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
                processes.append(('cache-mcp', mcp_process))
                console.print("✅ [green]MCP server started[/green]")

        if not foreground:
            console.print("\n🎉 [bold green]Claude Cache is now running![/bold green]")
            console.print("\n[bold]What's running:[/bold]")
            console.print("  • 🧠 Background learning agent (monitors Claude Code every 30s)")
            console.print("  • 🔍 Vector search and pattern intelligence")
            console.print("  • 💻 Full terminal interface available")

            console.print("\n[bold]Try these terminal commands:[/bold]")
            console.print("  • [cyan]cache query \"authentication patterns\"[/cyan]")
            console.print("  • [cyan]cache stats[/cyan]")
            console.print("  • [cyan]cache suggest --context \"working on API\"[/cyan]")
            console.print("  • [cyan]cache learn \"solution here\" --tags auth,api[/cyan]")

            if not with_mcp:
                console.print("\n[bold]For Claude Code integration:[/bold]")
                console.print("  • Run [cyan]cache-mcp[/cyan] separately")
                console.print("  • Or use [cyan]cache run --with-mcp[/cyan]")

            console.print("\n[bold]Stop with:[/bold]")
            console.print("  • [cyan]pkill -f 'CacheAgent'[/cyan]")
            if with_mcp:
                console.print("  • [cyan]pkill cache-mcp[/cyan]")

    except KeyboardInterrupt:
        console.print("\n[yellow]Stopping Claude Cache...[/yellow]")
        for name, process in processes:
            try:
                process.terminate()
                console.print(f"✅ Stopped {name}")
            except:
                pass
        sys.exit(0)
    except Exception as e:
        console.print(f"[red]Error starting Claude Cache: {e}[/red]")
        sys.exit(1)


@cli.command()
@click.option('--db', type=click.Path(), help='Custom database path')
def background(db):
    """Start Claude Cache in background using simple subprocess (no daemon)"""
    import subprocess
    import sys

    console.print(f"[bold cyan]{ASCII_ART}[/bold cyan]")
    console.print(f"[bold]Starting Claude Cache v{__version__} in Background[/bold]\n")

    console.print("🔄 [cyan]Starting background process...[/cyan]")

    # Use nohup approach for background execution
    cmd = [
        'nohup', 'cache', 'start', '--watch'
    ]

    if db:
        cmd.extend(['--db', db])

    try:
        # Start in background, redirect output to log file
        subprocess.Popen(
            cmd + ['>', '/tmp/claude-cache.log', '2>&1', '&'],
            shell=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

        console.print("✅ [green]Background process started![/green]")
        console.print("\n[bold]Claude Cache is now running in background![/bold]")
        console.print("\n[bold]What's running:[/bold]")
        console.print("  • 🧠 Background learning (monitors Claude Code)")
        console.print("  • 🔍 Vector search and pattern intelligence")
        console.print("  • 💻 Terminal commands available")

        console.print("\n[bold]Try these commands:[/bold]")
        console.print("  • [cyan]cache query \"patterns\"[/cyan]")
        console.print("  • [cyan]cache stats[/cyan]")
        console.print("  • [cyan]cache suggest[/cyan]")

        console.print("\n[bold]Stop with:[/bold]")
        console.print("  • [cyan]pkill -f 'cache start'[/cyan]")
        console.print("\n[bold]View logs:[/bold]")
        console.print("  • [cyan]tail -f /tmp/claude-cache.log[/cyan]")

    except Exception as e:
        console.print(f"[red]Error starting background process: {e}[/red]")
        sys.exit(1)


@cli.command()
@click.argument('repo_path', type=click.Path(exists=True), default='.')
@click.option('--project', '-p', help='Project name (defaults to directory name)')
@click.option('--db', type=click.Path(), help='Custom database path')
def scan_docs(repo_path, project, db):
    """Scan repository for documentation and lessons learned"""
    try:
        from .doc_scanner import DocumentationScanner

        agent = CacheAgent(db)
        scanner = DocumentationScanner(agent.kb)

        # Use current directory if not specified
        repo_path = Path(repo_path).resolve()

        console.print(f"[cyan]Scanning repository: {repo_path}[/cyan]")
        docs = scanner.scan_repository(str(repo_path), project)

        console.print(f"\n[green]✓ Successfully scanned {len(docs)} documents[/green]")

        # Show summary of what was found
        if docs:
            lessons_count = sum(len(d.lessons_learned) for d in docs)
            warnings_count = sum(len(d.warnings) for d in docs)
            practices_count = sum(len(d.best_practices) for d in docs)

            console.print("\n[bold]Summary:[/bold]")
            console.print(f"  • Lessons learned: {lessons_count}")
            console.print(f"  • Warnings/gotchas: {warnings_count}")
            console.print(f"  • Best practices: {practices_count}")
            console.print(f"  • Code examples: {sum(len(d.code_examples) for d in docs)}")

            console.print("\n[dim]Documentation has been added to your knowledge base.[/dim]")
            console.print("[dim]It will be included in future context generation.[/dim]")

    except Exception as e:
        console.print(f"[red]Error scanning documentation: {e}[/red]")
        sys.exit(1)


@cli.command()
@click.option('--query', '-q', help='Search for specific content')
@click.option('--project', '-p', help='Filter by project name')
@click.option('--type', '-t', help='Filter by document type (lessons, architecture, guide, etc.)')
@click.option('--db', type=click.Path(), help='Custom database path')
def search_docs(query, project, type, db):
    """Search through indexed documentation"""
    try:
        from .doc_scanner import DocumentationScanner
        import json

        agent = CacheAgent(db)
        scanner = DocumentationScanner(agent.kb)

        results = scanner.kb.search_documentation(query, project)

        if not results:
            console.print("[yellow]No documentation found matching your search[/yellow]")
            return

        console.print(f"\n[bold]Found {len(results)} documents:[/bold]\n")

        for result in results[:5]:  # Show top 5
            doc_data = json.loads(result['content'])

            console.print(f"[cyan]{result['file_path']}[/cyan] ({result['doc_type']})")

            if doc_data.get('lessons_learned'):
                console.print("  [bold]Lessons:[/bold]")
                for lesson in doc_data['lessons_learned'][:3]:
                    console.print(f"    • {lesson[:80]}...")

            if doc_data.get('warnings'):
                console.print("  [bold]Warnings:[/bold]")
                for warning in doc_data['warnings'][:2]:
                    console.print(f"    ⚠️  {warning[:80]}...")

            console.print()

    except Exception as e:
        console.print(f"[red]Error searching documentation: {e}[/red]")
        sys.exit(1)


@cli.command()
@click.argument('description')
@click.option('--project', '-p', help='Project name (defaults to current directory)')
@click.option('--db', type=click.Path(), help='Custom database path')
def win(description, project, db):
    """Quick capture of a successful solution (gold pattern)"""
    try:
        agent = CacheAgent(db)

        # Use current directory as project if not specified
        if not project:
            project = Path.cwd().name

        pattern = {
            'request_type': 'quick_win',
            'user_request': 'Quick success',
            'approach': description,
            'solution_steps': [description],
            'tags': ['quick-win'],
            'timestamp': datetime.now().isoformat()
        }

        # Store as gold pattern (high success score)
        agent.kb.store_success_pattern(pattern, project, success_score=1.0)

        console.print(f"✅ [green bold]Win captured![/green bold]")
        console.print(f"🥇 Gold pattern saved to [cyan]{project}[/cyan]")

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


@cli.command()
@click.argument('description')
@click.option('--why', help='Why it failed')
@click.option('--alternative', help='What to do instead')
@click.option('--project', '-p', help='Project name (defaults to current directory)')
@click.option('--db', type=click.Path(), help='Custom database path')
def fail(description, why, alternative, project, db):
    """Quick capture of what didn't work (anti-pattern)"""
    try:
        import sqlite3

        agent = CacheAgent(db)

        # Use current directory as project if not specified
        if not project:
            project = Path.cwd().name

        # Store as anti-pattern
        conn = sqlite3.connect(agent.kb.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO anti_patterns
            (project_name, pattern_type, problem, failed_approach, error_reason, alternative_solution, confidence, timestamp, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            project,
            'quick_fail',
            'Quick failure capture',
            description,
            why or 'Not specified',
            alternative or 'Find alternative approach',
            0.9,
            datetime.now().isoformat(),
            datetime.now().isoformat()
        ))

        conn.commit()
        conn.close()

        console.print(f"⚠️  [red bold]Failure captured![/red bold]")
        console.print(f"📝 Anti-pattern saved to [cyan]{project}[/cyan]")
        if why:
            console.print(f"   Reason: {why}")
        if alternative:
            console.print(f"   Alternative: {alternative}")

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


@cli.command()
@click.argument('solution')
@click.option('--context', '-c', help='Additional context about the solution')
@click.option('--tags', '-t', help='Comma-separated tags for categorization')
@click.option('--project', '-p', help='Project name (defaults to current directory)')
@click.option('--db', type=click.Path(), help='Custom database path')
def learn(solution, context, tags, project, db):
    """Save a successful solution to your knowledge base"""
    try:
        agent = CacheAgent(db)

        # Use current directory as project if not specified
        if not project:
            project = Path.cwd().name

        pattern = {
            'request_type': 'manual_save',
            'user_request': context or '',
            'approach': solution,
            'solution_steps': [solution],
            'tags': tags.split(',') if tags else [],
            'timestamp': datetime.now().isoformat()
        }

        agent.kb.store_success_pattern(pattern, project)

        console.print(f"✅ [green]Pattern saved successfully![/green]")
        console.print(f"🏷️  Tags: {tags or 'none'}")
        console.print(f"📁 Project: {project}")

    except Exception as e:
        console.print(f"[red]Error saving pattern: {e}[/red]")
        sys.exit(1)


@cli.command()
@click.argument('url')
@click.option('--project', '-p', help='Project name (defaults to current directory)')
@click.option('--db', type=click.Path(), help='Custom database path')
def browse(url, project, db):
    """Index documentation from URL or file path"""
    try:
        from .doc_scanner import DocumentationScanner
        import json

        agent = CacheAgent(db)
        scanner = DocumentationScanner(agent.kb)

        # Use current directory as project if not specified
        if not project:
            project = Path.cwd().name

        console.print(f"[cyan]Indexing documentation: {url}[/cyan]")

        # Determine if URL or file path
        if url.startswith(('http://', 'https://', 'file://')):
            # Web documentation
            scraped = scanner.scrape_documentation(url)
            if not scraped:
                console.print(f"[red]❌ Failed to fetch documentation from {url}[/red]")
                sys.exit(1)

            extracted = scanner.extract_lessons(scraped['content'])
            doc_type = 'web'
        else:
            # Local file/directory
            path = Path(url).expanduser().resolve()
            if not path.exists():
                console.print(f"[red]❌ Path not found: {url}[/red]")
                sys.exit(1)

            if path.is_file():
                content = path.read_text()
                doc_type = 'file'
            else:
                # Directory - read README or main docs
                readme = path / 'README.md'
                if readme.exists():
                    content = readme.read_text()
                    doc_type = 'readme'
                else:
                    console.print(f"[red]❌ No documentation found in directory: {url}[/red]")
                    sys.exit(1)

            extracted = scanner.extract_lessons(content)

        # Store in knowledge base
        agent.kb.store_documentation(
            project_name=project,
            file_path=url,
            doc_type=doc_type,
            content=json.dumps(extracted),
            extracted_at=datetime.now().isoformat()
        )

        console.print("✅ [green]Documentation indexed successfully![/green]")
        console.print(f"📊 Extracted Content:")
        console.print(f"  • Lessons: {len(extracted.get('lessons', []))}")
        console.print(f"  • Warnings: {len(extracted.get('warnings', []))}")
        console.print(f"  • Best Practices: {len(extracted.get('best_practices', []))}")
        console.print(f"📁 Project: {project}")

    except Exception as e:
        console.print(f"[red]Error indexing documentation: {e}[/red]")
        sys.exit(1)


@cli.command()
@click.option('--context', '-c', help='Current work context for relevant suggestions')
@click.option('--project', '-p', help='Project name (defaults to current directory)')
@click.option('--db', type=click.Path(), help='Custom database path')
def suggest(context, project, db):
    """Get proactive recommendations based on current context"""
    try:
        agent = CacheAgent(db)

        # Use current directory as project if not specified
        if not project:
            project = Path.cwd().name

        # Get project patterns
        patterns = agent.kb.get_project_patterns(project, limit=3)

        # Search for context-relevant patterns if context provided
        relevant = []
        if context:
            try:
                if hasattr(agent.kb, 'vector_search') and agent.kb.vector_search:
                    relevant = agent.kb.vector_search.search_patterns(context, limit=3)
                else:
                    # Fallback to basic pattern search
                    all_patterns = agent.kb.search_patterns(context, limit=3)
                    relevant = [{'content': p.get('approach', ''), 'similarity': 0.5} for p in all_patterns]
            except Exception:
                # Silent fallback if vector search fails
                pass

        console.print("💡 [bold]Suggestions for your current work:[/bold]\n")

        if patterns:
            console.print(f"[bold]Recent patterns from {project}:[/bold]")
            for i, p in enumerate(patterns, 1):
                approach = p.get('approach', 'No description')[:100]
                console.print(f"{i}. {approach}...")
            console.print()

        if relevant:
            console.print("[bold]Context-relevant patterns:[/bold]")
            for i, r in enumerate(relevant, 1):
                content = r.get('content', '')[:100]
                similarity = r.get('similarity', 0)
                console.print(f"{i}. {content}...")
                console.print(f"   Relevance: {similarity:.2%}")
            console.print()

        if not patterns and not relevant:
            console.print("[yellow]No suggestions available yet.[/yellow]")
            console.print("Save patterns with [cyan]cache learn[/cyan] to build your knowledge base!")

    except Exception as e:
        console.print(f"[red]Error getting suggestions: {e}[/red]")
        sys.exit(1)


@cli.command()
def info():
    """Show information about Claude Cache"""
    console.print(f"[bold cyan]{ASCII_ART}[/bold cyan]")
    console.print(f"[bold cyan]Claude Cache v{__version__}[/bold cyan]")
    console.print("[bold]Give your AI coding assistant perfect recall[/bold]\n")

    console.print("[bold]Overview:[/bold]")
    console.print("Claude Cache automatically learns from every successful solution and provides")
    console.print("instant access to your accumulated knowledge directly within Claude Code.\n")

    console.print("[bold]Features:[/bold]")
    console.print("• 🤖 Intelligent behavioral detection (NEW v0.9.1!)")
    console.print("• 🔄 Never solve the same problem twice")
    console.print("• ⚡ Auto-save patterns without interrupting workflow")
    console.print("• 🔍 Semantic search with AI understanding")
    console.print("• 🏗️ Cross-project pattern recognition")
    console.print("• 📚 Documentation indexing and search\n")

    console.print("[bold]Claude Code Integration:[/bold]")
    console.print("Add to your .claude.json:")
    console.print('[cyan]{"mcpServers": {"cache": {"type": "stdio", "command": "cache-mcp"}}}[/cyan]\n')

    console.print("[bold]CLI Quick Start:[/bold]")
    console.print("1. [cyan]cache analyze --recent[/cyan] (NEW!) Intelligent session analysis")
    console.print("2. [cyan]cache learn[/cyan] \"Fixed CORS issue with middleware\" --tags cors,api")
    console.print("3. [cyan]cache query[/cyan] \"authentication problems\"")
    console.print("4. [cyan]cache suggest[/cyan] (contextual suggestions)")
    console.print("5. [cyan]cache browse[/cyan] https://docs.example.com")
    console.print("6. [cyan]cache stats[/cyan] to see your knowledge base\n")

    console.print("[bold]Storage:[/bold]")
    console.print("All data stored locally in ~/.claude/knowledge/ - completely private\n")

    console.print("[bold]Documentation:[/bold]")
    console.print("https://github.com/ga1ien/claude-cache")


def main():
    """Main entry point"""
    cli()


if __name__ == '__main__':
    main()