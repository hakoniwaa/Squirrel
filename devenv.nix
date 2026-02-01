{ pkgs, lib, config, inputs, ... }:

{
  # Project metadata
  name = "squirrel";

  # Environment variables
  env = {
    SQUIRREL_DEV = "1";
  };

  # Packages available in the development shell
  packages = with pkgs; [
    # Build tools
    git
    gnumake

    # SQLite with extensions
    sqlite

    # Utilities
    jq
    ripgrep
    fd
  ];

  # Rust toolchain
  languages.rust = {
    enable = true;
  };

  # Git hooks
  git-hooks.hooks = {
    # Rust
    rustfmt.enable = true;
  };

  # Shell scripts available in the environment
  scripts = {
    # Run all tests
    test-all.exec = ''
      echo "Running Rust tests..."
      cargo test --manifest-path daemon/Cargo.toml
    '';

    # Run Rust daemon CLI
    sqrl.exec = ''
      cargo run --manifest-path daemon/Cargo.toml -- "$@"
    '';

    # Format all code
    fmt.exec = ''
      cargo fmt --manifest-path daemon/Cargo.toml
    '';

    # Lint all code
    lint.exec = ''
      cargo clippy --manifest-path daemon/Cargo.toml -- -D warnings
    '';
  };

  # Enter shell message
  enterShell = ''
    echo "Squirrel development environment"
    echo ""
    echo "Available commands:"
    echo "  test-all    - Run all tests"
    echo "  sqrl        - Run Squirrel CLI"
    echo "  fmt         - Format code"
    echo "  lint        - Lint code"
    echo ""
    echo "See specs/ for project specifications"
  '';

  # Ensure minimum devenv version
  devenv.flakesIntegration = true;
}
