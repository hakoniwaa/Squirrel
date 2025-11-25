# Development Setup

Cross-platform setup guide for Windows, macOS, and Linux.

## Prerequisites

### 1. Rust (via rustup)

**All platforms:**
```bash
# Install rustup (Rust toolchain manager)
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh

# Windows: download and run rustup-init.exe from https://rustup.rs

# Verify installation
rustup --version
cargo --version
```

Required version: **1.83.0+**

```bash
# Update to latest stable
rustup update stable
```

### 2. Python (via uv)

**All platforms:**
```bash
# Install uv (fast Python package manager)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows PowerShell:
# powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"

# Verify installation
uv --version
```

uv will automatically manage Python versions.

### 3. SQLite

Usually pre-installed. Verify:
```bash
sqlite3 --version
```

If missing:
- **macOS**: `brew install sqlite`
- **Linux**: `sudo apt install sqlite3` or `sudo dnf install sqlite`
- **Windows**: Download from https://sqlite.org/download.html

## Project Setup

### Clone and Enter

```bash
git clone https://github.com/kaminoguo/Squirrel.git
cd Squirrel
```

### Rust Agent

```bash
cd agent
cargo build
cargo test
```

### Python Memory Service

```bash
cd memory_service

# Create virtual environment and install dependencies
uv venv
uv pip install -e ".[dev]"

# Activate virtual environment
# Linux/macOS:
source .venv/bin/activate
# Windows:
.venv\Scripts\activate

# Run tests
pytest
```

## Development Workflow

### Daily Routine

```bash
# Pull latest changes
git checkout main
git pull origin main

# Create feature branch
git checkout -b yourname/feat-description

# Work on changes...

# Run tests before commit
cd agent && cargo test
cd ../memory_service && pytest

# Commit and push
git add .
git commit -m "feat(scope): description"
git push origin yourname/feat-description

# Create PR on GitHub
```

### Running the Daemon (Development)

```bash
cd agent
cargo run -- daemon start
```

### Running the Python Service (Standalone)

```bash
cd memory_service
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
python -m squirrel_memory.server --port 8734
```

## Testing

### Rust

```bash
cd agent

# Run all tests
cargo test

# Run specific test
cargo test test_name

# Run with output
cargo test -- --nocapture
```

### Python

```bash
cd memory_service
source .venv/bin/activate

# Run all tests
pytest

# Run specific test file
pytest tests/test_extractor.py

# Run with coverage
pytest --cov=squirrel_memory
```

## Linting & Formatting

### Rust

```bash
cd agent

# Check formatting
cargo fmt --check

# Auto-format
cargo fmt

# Lint
cargo clippy
```

### Python

```bash
cd memory_service

# Check
ruff check .
ruff format --check .

# Auto-fix
ruff check --fix .
ruff format .
```

## IDE Setup

### VS Code / Cursor

Recommended extensions:
- `rust-analyzer` - Rust language support
- `ms-python.python` - Python support
- `charliermarsh.ruff` - Python linting
- `tamasfe.even-better-toml` - TOML support

Create `.vscode/settings.json`:
```json
{
  "rust-analyzer.cargo.features": "all",
  "python.defaultInterpreterPath": "${workspaceFolder}/memory_service/.venv/bin/python",
  "[python]": {
    "editor.defaultFormatter": "charliermarsh.ruff",
    "editor.formatOnSave": true
  },
  "[rust]": {
    "editor.defaultFormatter": "rust-lang.rust-analyzer",
    "editor.formatOnSave": true
  }
}
```

## Environment Variables

Create `~/.sqrl/config.toml` for API keys:

```toml
[user]
id = "your-name"

[llm]
openai_api_key = "sk-..."
anthropic_api_key = "sk-ant-..."
default_model = "gpt-4"
```

Or set environment variables:
```bash
export OPENAI_API_KEY="sk-..."
export ANTHROPIC_API_KEY="sk-ant-..."
```

## Troubleshooting

### Windows: Long Path Issues

Enable long paths in Git:
```bash
git config --global core.longpaths true
```

### Windows: Line Endings

Configure Git to handle line endings:
```bash
git config --global core.autocrlf input
```

Add `.gitattributes` (already in repo):
```
* text=auto eol=lf
```

### macOS: Xcode Command Line Tools

If Rust compilation fails:
```bash
xcode-select --install
```

### Linux: Build Dependencies

If Rust compilation fails:
```bash
# Ubuntu/Debian
sudo apt install build-essential pkg-config libssl-dev

# Fedora
sudo dnf install gcc pkg-config openssl-devel
```

### Python: Virtual Environment Issues

```bash
cd memory_service
rm -rf .venv  # delete existing
uv venv       # recreate
uv pip install -e ".[dev]"
```

### SQLite: Database Locked

If you see "database is locked" errors:
- Ensure only one daemon instance is running
- Check for zombie processes: `ps aux | grep sqrl`

## Version Reference

See `.tool-versions` for pinned versions:
- Rust: 1.83.0
- Python: 3.11.11

## Additional Resources

- [ARCHITECTURE.md](ARCHITECTURE.md) - Full technical design
- [DEVELOPMENT_PLAN.md](DEVELOPMENT_PLAN.md) - Implementation roadmap
- [EXAMPLE.md](EXAMPLE.md) - Detailed walkthrough
- [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md) - Directory layout
- [CONTRIBUTING.md](../CONTRIBUTING.md) - Contribution guide
