# Release Process for Claude Cache

This document describes how to release new versions of Claude Cache to PyPI.

## Automatic Release (GitHub Actions)

### Setup (One-time)

1. **Add PyPI API Token to GitHub Secrets:**
   - Go to your GitHub repo settings
   - Navigate to Settings → Secrets and variables → Actions
   - Click "New repository secret"
   - Name: `PYPI_API_TOKEN`
   - Value: Your PyPI API token (create at https://pypi.org/manage/account/token/)

### Creating a New Release

1. **Update version number** in `pyproject.toml`:
   ```toml
   version = "0.2.0"  # Increment as needed
   ```

2. **Update CHANGELOG.md** with release notes

3. **Commit and push changes:**
   ```bash
   git add -A
   git commit -m "Release v0.2.0"
   git push origin main
   ```

4. **Create a GitHub Release:**
   - Go to https://github.com/ga1ien/claude-cache/releases
   - Click "Create a new release"
   - Choose a tag: `v0.2.0` (create new tag)
   - Release title: `v0.2.0`
   - Describe the changes
   - Click "Publish release"

5. **GitHub Actions will automatically:**
   - Build the package
   - Upload to PyPI
   - Anyone can now `pip install claude-cache`

## Manual Release (Backup Method)

If GitHub Actions fails, you can manually release:

```bash
# 1. Clean old builds
rm -rf dist/ build/ *.egg-info

# 2. Build
python -m build

# 3. Upload to PyPI
python -m twine upload dist/*
```

## Version Numbering

Follow semantic versioning:
- **MAJOR.MINOR.PATCH** (e.g., 1.2.3)
- **MAJOR**: Breaking changes
- **MINOR**: New features, backward compatible
- **PATCH**: Bug fixes

## Post-Release

After releasing:
1. Verify on PyPI: https://pypi.org/project/claude-cache/
2. Test installation: `pip install claude-cache --upgrade`
3. Update any documentation if needed