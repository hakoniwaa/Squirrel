# Handover

Remaining work before v1 release.

## Owner Split

| Owner | Tasks |
|-------|-------|
| Lyrica | Linux build |
| Friend | macOS + Windows build, features below |

---

## 1. Config UI Improvement

Current UI is basic. Improve:
- Visual styling
- Loading states and error messages
- Drag & drop for MCP files
- Responsive design

File: `daemon/src/web/static/index.html`

---

## 2. MCP List Management

**Goal**: User builds a library of MCPs from different projects, enables/disables them, applies to any project.

**Implementation**:
- `sqrl init` reads project's `.mcp.json`, imports MCPs to global list at `~/.sqrl/`
- Deduplicate by name (newer overwrites)
- `sqrl config` UI shows all MCPs with enable/disable checkboxes
- `sqrl apply` only registers enabled MCPs to CLI tools
- Never modify project's `.mcp.json`, only read from it

**Files**:
- `daemon/src/global_config/mod.rs` - store MCP list with enabled flags
- `daemon/src/cli/init.rs` - auto-import MCPs
- `daemon/src/cli/apply.rs` - only apply enabled MCPs
- `daemon/src/web/static/index.html` - UI for MCP management
- `daemon/src/web/api.rs` - API endpoints

---

## 3. Token Bucket

**Goal**: Central place for user tokens. CLIs read from here instead of env vars.

**Implementation**:
- New file `~/.sqrl/secrets.yaml`:
  ```yaml
  tokens:
    github: ghp_xxx
    openrouter: sk-or-xxx
    anthropic: sk-ant-xxx
  custom:
    my_key: xxx
  ```
- New "Tokens" tab in web UI (mask values, never log)
- New module `daemon/src/secrets.rs`

---

## 4. Codex & Cursor Integration

**Goal**: `sqrl apply` registers MCPs with Codex and Cursor, not just Claude Code.

**Implementation**:
- Research where Cursor stores MCP config
- Research where Codex stores MCP config
- Update `daemon/src/cli/apply.rs` to write to their config files

---

## 5. Auto-Update

**Goal**: sqrl updates itself automatically, no commands.

**Implementation**:
- Use [self_update](https://github.com/jaemk/self_update) crate
- Check GitHub releases once per day (not every run)
- Download and replace binary silently

---

## 6. Repo Sync

**Goal**: User connects a git repo, memories sync automatically. No cloud service.

**Implementation**:
- User enters repo URL + token in `sqrl config` UI
- sqrl clones to `~/.sqrl/sync/` or makes `~/.sqrl/` itself a git repo
- Run `git maintenance start --scheduler=auto` to register with OS scheduler:
  - Linux: systemd-timer
  - macOS: launchd
  - Windows: Task Scheduler
- Git handles background sync automatically, no daemon needed
- Reference: [git-maintenance](https://git-scm.com/docs/git-maintenance)

---

## 7. README Improvement

**Goal**: Clear README with what sqrl does and quickstart guide.

**Include**:
- What is Squirrel (one paragraph)
- Key features (bullet points)
- Quickstart (install → configure → use)
- How MCP works with CLI tools
- How repo sync works

File: `README.md`

---

## 8. Pre-Release

- [ ] Build binaries (Linux/macOS/Windows) with cargo-dist
- [ ] Installation docs for each platform
- [ ] Test on all platforms
