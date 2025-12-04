"""Daemon mode for running Claude Cache in the background"""

import os
import sys
import time
import signal
import atexit
from pathlib import Path
from typing import Optional
from rich.console import Console

console = Console()


class CacheDaemon:
    """Run Claude Cache as a background daemon process"""

    def __init__(self, pidfile: Optional[str] = None):
        if pidfile is None:
            cache_dir = Path.home() / '.claude' / 'knowledge'
            cache_dir.mkdir(parents=True, exist_ok=True)
            pidfile = str(cache_dir / 'cache.pid')

        self.pidfile = pidfile
        self.agent = None

    def daemonize(self):
        """Create a daemon process using double-fork technique"""
        try:
            # First fork
            pid = os.fork()
            if pid > 0:
                # Exit parent process
                sys.exit(0)
        except OSError as e:
            console.print(f"[red]Fork #1 failed: {e}[/red]")
            sys.exit(1)

        # Decouple from parent environment
        os.chdir("/")
        os.setsid()
        os.umask(0)

        try:
            # Second fork
            pid = os.fork()
            if pid > 0:
                # Exit second parent
                sys.exit(0)
        except OSError as e:
            console.print(f"[red]Fork #2 failed: {e}[/red]")
            sys.exit(1)

        # Redirect standard file descriptors
        sys.stdout.flush()
        sys.stderr.flush()

        # Close file descriptors
        null = open(os.devnull, 'w')
        sys.stdout = null
        sys.stderr = null

        # Write pidfile
        atexit.register(self.delete_pidfile)
        pid = str(os.getpid())
        with open(self.pidfile, 'w') as f:
            f.write(pid)

    def delete_pidfile(self):
        """Remove pidfile on exit"""
        if os.path.exists(self.pidfile):
            os.remove(self.pidfile)

    def start(self):
        """Start the daemon"""
        # Check for existing pidfile
        if os.path.exists(self.pidfile):
            with open(self.pidfile, 'r') as f:
                pid = int(f.read().strip())

            # Check if process is running
            try:
                os.kill(pid, 0)
                console.print(f"[yellow]Claude Cache is already running (PID: {pid})[/yellow]")
                console.print("[cyan]Use 'cache stop' to stop it[/cyan]")
                sys.exit(1)
            except OSError:
                # Process not running, remove stale pidfile
                os.remove(self.pidfile)

        console.print("[green]Starting Claude Cache daemon...[/green]")

        # Daemonize
        self.daemonize()

        # Run the agent
        self.run()

    def stop(self):
        """Stop the daemon"""
        if not os.path.exists(self.pidfile):
            console.print("[yellow]Claude Cache daemon is not running[/yellow]")
            return

        with open(self.pidfile, 'r') as f:
            pid = int(f.read().strip())

        try:
            # Send SIGTERM
            os.kill(pid, signal.SIGTERM)
            console.print(f"[green]✓ Stopped Claude Cache daemon (PID: {pid})[/green]")

            # Remove pidfile
            if os.path.exists(self.pidfile):
                os.remove(self.pidfile)

        except OSError as e:
            if e.errno == 3:  # No such process
                console.print("[yellow]Process not found, removing stale pidfile[/yellow]")
                if os.path.exists(self.pidfile):
                    os.remove(self.pidfile)
            else:
                console.print(f"[red]Error stopping daemon: {e}[/red]")

    def restart(self):
        """Restart the daemon"""
        self.stop()
        time.sleep(1)
        self.start()

    def status(self):
        """Check daemon status"""
        if not os.path.exists(self.pidfile):
            console.print("[yellow]Claude Cache daemon is not running[/yellow]")
            return False

        with open(self.pidfile, 'r') as f:
            pid = int(f.read().strip())

        try:
            os.kill(pid, 0)
            console.print(f"[green]✓ Claude Cache daemon is running (PID: {pid})[/green]")
            return True
        except OSError:
            console.print("[yellow]Claude Cache daemon is not running (stale pidfile)[/yellow]")
            return False

    def run(self):
        """Run the cache agent in daemon mode"""
        from .agent import CacheAgent

        # Set up signal handlers
        signal.signal(signal.SIGTERM, self.handle_sigterm)
        signal.signal(signal.SIGINT, self.handle_sigterm)

        # Create and run agent
        self.agent = CacheAgent()

        # Run with monitoring
        try:
            self.agent.start(watch=True)
        except Exception as e:
            # Log errors to a file since we're daemonized
            log_file = Path.home() / '.claude' / 'knowledge' / 'daemon.log'
            with open(log_file, 'a') as f:
                f.write(f"Daemon error: {e}\n")

    def handle_sigterm(self, signum, frame):
        """Handle termination signal"""
        if self.agent:
            self.agent.watcher.stop()
        self.delete_pidfile()
        sys.exit(0)


def run_as_service():
    """Run Claude Cache as a background service"""
    daemon = CacheDaemon()

    # Parse simple commands
    if len(sys.argv) >= 2:
        command = sys.argv[1]

        if command == 'start':
            daemon.start()
        elif command == 'stop':
            daemon.stop()
        elif command == 'restart':
            daemon.restart()
        elif command == 'status':
            daemon.status()
        else:
            console.print(f"[red]Unknown command: {command}[/red]")
            console.print("[cyan]Usage: cache daemon [start|stop|restart|status][/cyan]")
            sys.exit(1)
    else:
        # Default to start
        daemon.start()


if __name__ == '__main__':
    run_as_service()