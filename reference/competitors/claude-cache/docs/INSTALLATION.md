# 📦 Claude Cache Installation Guide

Complete installation instructions for all platforms, from absolute beginner to power user.

## Quick Links
- [I'm New to Terminal/Python → Start Here](#complete-installation-from-scratch)
- [I Have Python → Quick Install](#quick-install-if-you-have-python)
- [macOS Step-by-Step](#macos-installation)
- [Windows Step-by-Step](#windows-installation)
- [Linux Instructions](#linux-installation)

---

## Quick Install (If You Have Python)

If you already have Python 3.8+ installed:

**Recommended: Using pipx (isolated installation)**
```bash
# Install pipx first (if not already installed)
python3 -m pip install --user pipx
python3 -m pipx ensurepath

# Install Claude Cache with all features
pipx install "claude-cache[mcp]"

# Start background learning
cache start --watch
```

**Alternative: Using pip directly**
```bash
# Basic install
pip install --user claude-cache

# Or with all features
pip install --user "claude-cache[mcp]"

# Start background learning
cache start --watch
```

If the above doesn't work or you're unsure, follow the detailed instructions below.

---

## Complete Installation from Scratch

Choose your operating system:
- [macOS (Mac) Instructions](#macos-installation)
- [Windows Instructions](#windows-installation)
- [Linux Instructions](#linux-installation)

---

## macOS Installation

### Complete Step-by-Step Guide for Mac Users

#### Step 1: Open Terminal

1. Press `Command + Space` to open Spotlight Search
2. Type "Terminal" and press Enter
3. A window with text will open - this is Terminal

#### Step 2: Check if Python is Installed

In Terminal, type this command and press Enter:

```bash
python3 --version
```

**What you should see:**
- ✅ If you see `Python 3.8.x` or higher (like 3.9, 3.10, 3.11, 3.12) - Great! Skip to Step 4
- ❌ If you see "command not found" or Python 3.7 or lower - Continue to Step 3

#### Step 3: Install Python (If Needed)

**Option A: Using Homebrew (Recommended)**

First, check if you have Homebrew:
```bash
brew --version
```

If you see "command not found", install Homebrew:
```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

- It will ask for your password - type it and press Enter (you won't see the characters)
- Follow any additional instructions shown

After Homebrew is installed, install Python:
```bash
brew install python@3.12
```

**Option B: Download from Python.org**

1. Go to https://www.python.org/downloads/
2. Click the big yellow "Download Python 3.12.x" button
3. Open the downloaded file
4. Follow the installer (click Continue, Agree, Install)

After installation, close and reopen Terminal, then verify:
```bash
python3 --version
```

#### Step 4: Install pip (Python Package Manager)

Check if pip is installed:
```bash
pip3 --version
```

If you see a version number, skip to Step 5. If not:

```bash
# Install pip
python3 -m ensurepip --upgrade
```

#### Step 5: Handle "Externally Managed Environment" (macOS 12+)

Modern macOS protects the system Python. We'll use pipx for a clean installation:

```bash
# Install pipx (isolates Claude Cache from other Python packages)
python3 -m pip install --user pipx

# Add pipx to your PATH
python3 -m pipx ensurepath
```

**Important**: After running ensurepath:
1. Close Terminal completely (Command + Q)
2. Open Terminal again

Verify pipx is working:
```bash
pipx --version
```

If "command not found", run:
```bash
# For zsh (default on modern macOS)
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc

# For bash (older macOS)
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bash_profile
source ~/.bash_profile
```

#### Step 6: Install Claude Cache

**Recommended: Using pipx (Clean & Isolated)**
```bash
# Install with all features including MCP integration
pipx install "claude-cache[mcp]"
```

**Alternative: Using pip with --user flag**
```bash
# If pipx doesn't work, try this
pip3 install --user "claude-cache[mcp]"

# Add to PATH if needed
echo 'export PATH="$HOME/Library/Python/3.12/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc
```

#### Step 7: Verify Installation

```bash
# Check if cache command is available
cache --version

# Should show something like:
# Claude Cache version 0.9.0
```

If you see "command not found":
```bash
# Find where cache was installed
find ~ -name cache -type f 2>/dev/null | grep -E "(bin|scripts)"

# Add that directory to PATH (replace /path/to/directory with actual path)
echo 'export PATH="/path/to/directory:$PATH"' >> ~/.zshrc
source ~/.zshrc
```

#### Step 8: First Run

```bash
# Start Claude Cache with real-time learning (recommended)
cache start --watch

# Or start with one-time processing only
cache start

# You should see:
# ✓ Knowledge base initialized at ~/.claude/knowledge/cache.db
# Processing existing log files...
# Starting real-time monitoring... (if using --watch)
```

#### Step 9: Configure Claude Code Integration (Optional)

Create or edit `.claude.json` in your home directory:

```bash
# Create the file
touch ~/.claude.json

# Open in text editor
open -e ~/.claude.json
```

Add this content:
```json
{
  "mcpServers": {
    "cache": {
      "type": "stdio",
      "command": "cache-mcp"
    }
  }
}
```

Save the file and restart Claude Code.

### macOS Troubleshooting

#### "Permission Denied" Error
```bash
# Use pipx instead of pip
pipx install "claude-cache[mcp]"
```

#### "Externally Managed Environment" Error
```bash
# This is expected on modern macOS. Use pipx:
pipx install "claude-cache[mcp]"

# Or use a virtual environment:
python3 -m venv ~/claude-env
source ~/claude-env/bin/activate
pip install "claude-cache[mcp]"
```

#### "Command Not Found" After Installation
```bash
# If using pipx
pipx ensurepath
# Then restart Terminal

# If using pip --user
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc
```

---

## Windows Installation

### Complete Step-by-Step Guide for Windows Users

#### Step 1: Open PowerShell

1. Press `Windows Key + X`
2. Select "Windows PowerShell" or "Terminal"
   - If you see "Terminal", that's perfect
   - If only "Command Prompt", that works too

#### Step 2: Check if Python is Installed

In PowerShell, type:

```powershell
python --version
```

Or try:
```powershell
python3 --version
```

**What you should see:**
- ✅ If you see `Python 3.8.x` or higher - Skip to Step 4
- ❌ If you see "not recognized" or error - Continue to Step 3

#### Step 3: Install Python (If Needed)

1. Go to https://www.python.org/downloads/
2. Click "Download Python 3.12.x" (big yellow button)
3. Run the downloaded installer
4. **CRITICAL**: ✅ Check "Add Python 3.12 to PATH" at the bottom
5. Click "Install Now"
6. Wait for installation
7. Click "Close"

**Verify Installation:**
1. Close PowerShell completely
2. Open PowerShell again
3. Type: `python --version`
4. Should show Python 3.12.x

#### Step 4: Upgrade pip

```powershell
python -m pip install --upgrade pip
```

#### Step 5: Install pipx (Recommended for Clean Installation)

```powershell
# Install pipx
python -m pip install --user pipx

# Add to PATH
python -m pipx ensurepath
```

**Important**: After ensurepath:
1. Close PowerShell
2. Open PowerShell again

#### Step 6: Install Claude Cache

**Option A: Using pipx (Recommended)**
```powershell
pipx install "claude-cache[mcp]"
```

**Option B: Using pip**
```powershell
pip install --user "claude-cache[mcp]"
```

#### Step 7: Verify Installation

```powershell
cache --version
```

If "not recognized":
1. Search for "Environment Variables" in Start Menu
2. Click "Environment Variables" button
3. Under "User variables", find "Path" and click "Edit"
4. Click "New" and add these (replace YOUR_USERNAME):
   - `C:\Users\YOUR_USERNAME\AppData\Local\Programs\Python\Python312\Scripts`
   - `C:\Users\YOUR_USERNAME\AppData\Roaming\Python\Python312\Scripts`
   - `C:\Users\YOUR_USERNAME\.local\bin`
5. Click OK on all windows
6. Restart PowerShell

#### Step 8: First Run

```powershell
# Start with real-time learning (recommended)
cache start --watch

# Or start with one-time processing only
cache start
```

#### Step 9: Configure Claude Code (Optional)

1. Open Notepad:
   ```powershell
   notepad $env:USERPROFILE\.claude.json
   ```

2. Add this content:
   ```json
   {
     "mcpServers": {
       "cache": {
         "type": "stdio",
         "command": "cache-mcp"
       }
     }
   }
   ```

3. Save and close
4. Restart Claude Code

### Windows Troubleshooting

#### "Access Denied" Error
1. Right-click PowerShell in Start Menu
2. Select "Run as Administrator"
3. Try installation again

#### Long Path Support
Enable long paths:
1. Run PowerShell as Administrator
2. Execute:
   ```powershell
   Set-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\FileSystem" -Name "LongPathsEnabled" -Value 1
   ```

---

## Linux Installation

### Ubuntu/Debian

```bash
# Update package list
sudo apt update

# Install Python and pip
sudo apt install python3 python3-pip python3-venv

# Install pipx
python3 -m pip install --user pipx
python3 -m pipx ensurepath

# Restart shell
source ~/.profile

# Install Claude Cache
pipx install "claude-cache[mcp]"

# Verify
cache --version
```

### Fedora/RHEL/CentOS

```bash
# Install Python
sudo dnf install python3 python3-pip

# Install pipx
python3 -m pip install --user pipx
python3 -m pipx ensurepath

# Restart shell
exec $SHELL

# Install Claude Cache
pipx install "claude-cache[mcp]"
```

### Arch/Manjaro

```bash
# Install Python
sudo pacman -S python python-pip

# Install pipx
pip install --user pipx
python -m pipx ensurepath

# Restart shell
exec $SHELL

# Install Claude Cache
pipx install "claude-cache[mcp]"
```

---

## Installation Modes Explained

Once you have Python and pip/pipx installed, you can choose your installation mode:

### 🚀 Mode 1: Basic Installation

```bash
# Using pipx (recommended - isolated and clean)
pipx install claude-cache

# Alternative: Using pip with --user flag
pip install --user claude-cache
```

**Features:**
- ✅ All CLI commands (`cache start`, `cache query`, etc.)
- ✅ Pattern learning and storage
- ✅ Dual-path learning (successes AND failures)
- ✅ Journey pattern tracking
- ✅ TF-IDF keyword search
- ✅ Cross-project intelligence

**Best For:**
- Getting started with Claude Cache
- Simple keyword-based pattern matching
- All core functionality without extra dependencies

### ⚡ Mode 2: Enhanced Installation

```bash
# Using pipx (recommended - isolated and clean)
pipx install "claude-cache[enhanced]"

# Alternative: Using pip with --user flag
pip install --user "claude-cache[enhanced]"
```

**Additional Features:**
- ✅ **Semantic Vector Search** (understands meaning)
- ✅ **2x Better Pattern Matching**
- ✅ **Context Understanding** ("auth bug" finds JWT solutions)
- ✅ **ML-Powered Intelligence**

**Best For:**
- Developers wanting the best pattern matching
- Large codebases with many patterns
- When keyword search isn't enough

### 🎯 Mode 3: MCP Installation (Recommended)

```bash
# Using pipx (recommended - isolated and clean)
pipx install "claude-cache[mcp]"

# Alternative: Using pip with --user flag
pip install --user "claude-cache[mcp]"
```

**Ultimate Features:**
- ✅ Everything from Enhanced mode
- ✅ **Native Claude Code Integration**
- ✅ **Instant Tool Access** (type `/` in Claude Code)
- ✅ **Zero Context Switching**
- ✅ **Real-time Pattern Suggestions**

**Setup MCP Tools:**

1. Add to `.claude.json`:
   ```json
   {
     "mcpServers": {
       "cache": {
         "type": "stdio",
         "command": "cache-mcp"
       }
     }
   }
   ```

2. Restart Claude Code

3. Type `/` to see tools:
   - `/mcp__cache__query` - Search patterns
   - `/mcp__cache__learn` - Save patterns
   - `/mcp__cache__suggest` - Get suggestions
   - `/mcp__cache__stats` - View statistics
   - `/mcp__cache__browse` - Index documentation

**Best For:**
- Claude Code users
- Maximum productivity
- Seamless AI-assisted development

---

## Verification & Testing

### Test Your Installation

```bash
# 1. Check version
cache --version

# 2. Run diagnostics
cache diagnose

# 3. Test basic functionality
cache stats

# 4. Test MCP server (if installed)
cache-mcp --version
```

### Common Installation Issues

#### "Module not found" Error
```bash
# Reinstall with all dependencies
pipx reinstall "claude-cache[mcp]" --force
```

#### Database Permission Error
```bash
# Fix permissions
mkdir -p ~/.claude/knowledge
chmod 755 ~/.claude
```

#### Can't Find cache Command
```bash
# Using pipx
pipx ensurepath

# Using pip
echo $PATH  # Check if .local/bin is in PATH
```

---

## Uninstallation

### Remove Claude Cache

**If installed with pipx:**
```bash
pipx uninstall claude-cache
```

**If installed with pip:**
```bash
pip uninstall claude-cache
```

### Remove Data (Optional)

```bash
# Backup first if needed
cp -r ~/.claude ~/.claude-backup

# Remove all Claude Cache data
rm -rf ~/.claude
```

---

## 💡 Recommendations

### For Absolute Beginners
1. Follow the step-by-step OS instructions above
2. Use pipx for installation (cleaner)
3. Start with basic mode, upgrade later

### For Developers
1. Install Python 3.10+ if not present
2. Use pipx for isolation
3. Go directly to MCP mode

### For Teams
1. Standardize on Python 3.10+
2. Use MCP mode with shared configuration
3. Consider Docker for consistency

---

## Getting Help

If you encounter issues:

1. **Run diagnostics**: `cache diagnose`
2. **Check documentation**: See other docs in this folder
3. **Report issues**: https://github.com/Alyks1/claude-cache/issues

---

## 🎯 Next Steps

Once installed:

1. **Start Background Learning**: `cache start --watch`
2. **Open Interactive Monitor**: `cache monitor` (press 'h' for help)
3. **Read Quick Start**: [QUICK_START.md](QUICK_START.md)
4. **Configure**: [CONFIGURATION.md](CONFIGURATION.md)
5. **Learn More**: [HOW_IT_WORKS.md](HOW_IT_WORKS.md)

**Ready to never repeat the same mistake twice!** 🚀