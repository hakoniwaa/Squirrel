{ pkgs, lib, config, inputs, ... }:

{
  # Project metadata
  name = "squirrel";

  # Environment variables
  env = {
    SQUIRREL_DEV = "1";
    PYTHONPATH = "./src";
  };

  # Packages available in the development shell
  packages = with pkgs; [
    # Build tools
    git
    gnumake

    # SQLite with extensions
    sqlite

    # Documentation
    mdbook

    # Utilities
    jq
    ripgrep
    fd
  ];

  # Rust toolchain (basic - channel requires rust-overlay)
  languages.rust = {
    enable = true;
  };

  # Python with packages
  languages.python = {
    enable = true;
    # Use default Python version (no nixpkgs-python needed)

    venv = {
      enable = true;
      requirements = ''
        # Core dependencies
        litellm>=1.0.0
        pydantic>=2.0.0
        pydantic-ai>=0.1.0
        numpy>=1.24.0

        # HTTP client
        httpx

        # Dev dependencies
        pytest>=8.0.0
        pytest-asyncio>=0.23.0
        ruff>=0.1.0

        # Install sqrl in editable mode
        -e .
      '';
    };
  };

  # Git hooks
  git-hooks.hooks = {
    # Rust
    rustfmt.enable = true;

    # Python
    ruff.enable = true;
  };

  # Shell scripts available in the environment
  scripts = {
    # Run all tests
    test-all.exec = ''
      echo "Running Python tests..."
      pytest tests/ -v
      if [ -d "daemon" ]; then
        echo "Running Rust tests..."
        cargo test
      fi
    '';

    # Run Python tests only
    test-py.exec = ''
      pytest tests/ -v
    '';

    # Start daemon in development mode
    dev-daemon.exec = ''
      cargo run --bin sqrl-daemon -- --dev
    '';

    # Format all code
    fmt.exec = ''
      ruff format src/ tests/
      if [ -d "daemon" ]; then
        cargo fmt
      fi
    '';

    # Lint all code
    lint.exec = ''
      ruff check src/ tests/
      if [ -d "daemon" ]; then
        cargo clippy -- -D warnings
      fi
    '';
  };

  # Processes (long-running services for development)
  processes = {
    # daemon.exec = "cargo watch -x 'run --bin sqrl-daemon'";
  };

  # Services (databases, etc.)
  # services.sqlite.enable = true;

  # Enter shell message
  enterShell = ''
    echo "Squirrel development environment"
    echo ""
    echo "Available commands:"
    echo "  test-all    - Run all tests"
    echo "  test-py     - Run Python tests only"
    echo "  fmt         - Format all code"
    echo "  lint        - Lint all code"
    echo ""
    echo "Python package: sqrl (src/sqrl/)"
    echo "See specs/ for project specifications"
  '';

  # Ensure minimum devenv version
  devenv.flakesIntegration = true;
}
