# Pre-Commit Hook Guide

## Philosophy

Pre-commit hooks follow the **"5-Second Rule"**: If checks take more than 5 seconds, developers will eventually skip them with `--no-verify`. Our hooks are optimized to catch 90% of mistakes in 10% of the time.

## What Changed

### Removed

- ❌ `detect-private-key` (slow, caused infinite loops with `.secrets.baseline`)
- ❌ `black` (redundant - Ruff handles formatting 100x faster)
- ❌ Full test suite in pre-commit (moved to ship.sh and CI/CD)

### Added

- ✅ **TruffleHog** - Fast, comprehensive secret detection (replaces detect-secrets)
- ✅ **Prettier** - Auto-format frontend files
- ✅ **Fast unit tests only** - Tests marked as `@pytest.mark.unit` or without markers
- ✅ **Changed files only** - Mypy and TypeScript only check modified files

### Optimized

- ✅ **Ruff** replaces Black + Flake8 + isort (100x faster)
- ✅ **Stages** - All hooks run on `commit` stage only
- ✅ **Pass filenames** - Tools only check changed files where possible

## Test Markers

Mark your tests to control when they run:

```python
import pytest

# Fast unit test (< 1 second) - runs in pre-commit
def test_rate_limiter():
    assert True

# Also runs in pre-commit (no marker = fast)
def test_basic_validation():
    assert True

# Slow test (> 1 second) - skipped in pre-commit
@pytest.mark.slow
def test_full_integration():
    time.sleep(2)
    assert True

# Integration test - skipped in pre-commit
@pytest.mark.integration
def test_api_integration():
    response = client.get("/v1/predict")
    assert response.status_code == 200
```

## When Tests Run

| Location        | Command           | Tests Run                  | Duration |
| --------------- | ----------------- | -------------------------- | -------- |
| Pre-commit Hook | `git commit`      | Fast unit tests only       | < 2s     |
| ship.sh         | `./ship.sh "msg"` | Full test suite            | ~10s     |
| CI/CD           | `git push`        | Full test suite + coverage | ~2min    |

## TruffleHog Setup

TruffleHog replaces `detect-private-key` and `detect-secrets` with faster, more accurate secret detection.

### Installation

```bash
# macOS
brew install trufflesecurity/trufflehog/trufflehog

# Linux
curl -sSfL https://raw.githubusercontent.com/trufflesecurity/trufflehog/main/scripts/install.sh | sh -s -- -b /usr/local/bin

# Verify installation
trufflehog --version
```

### What It Detects

- AWS keys, GitHub tokens, API keys
- Private keys (RSA, SSH, PGP)
- Database credentials
- OAuth tokens
- 700+ credential types

### Configuration

TruffleHog runs with these flags:

- `--since-commit HEAD` - Only scan staged changes (fast!)
- `--only-verified` - Only fail on verified secrets (reduces false positives)
- `--fail` - Exit with error if secrets found

### Handling False Positives

If TruffleHog flags a false positive:

```bash
# Option 1: Add to .trufflehogignore (recommended)
echo "path/to/file:line_number" >> .trufflehogignore

# Option 2: Bypass for this commit only (emergency)
git commit --no-verify -m "False positive"
```

## Hook Execution Flow

```
git commit -m "Your message"
    ↓
1. Universal checks (< 1s)
   - Trailing whitespace
   - End-of-file fixer
   - YAML/JSON syntax
   - Large files (>1MB)
   - Merge conflicts
    ↓
2. Security (< 1s)
   - TruffleHog secret scan
    ↓
3. Python (< 2s)
   - Ruff lint + format (auto-fix)
   - Mypy type check (changed files)
    ↓
4. Frontend (< 2s)
   - Prettier format (auto-fix)
   - ESLint lint
   - TypeScript type check (changed files)
    ↓
5. Fast tests (< 2s)
   - pytest -m "not slow and not integration"
    ↓
✅ Commit succeeds (total < 5s)
```

## ship.sh Integration

`ship.sh` remains unchanged and runs the full workflow:

```bash
./ship.sh "Your commit message"
```

**What it does:**

1. Runs **full test suite** (including slow/integration tests)
2. Auto-formats frontend with Prettier
3. Stages all changes
4. Commits with GPG signature (`-S`)
   - Pre-commit hook runs here (fast checks only)
5. Pushes to remote

**Key point**: Pre-commit hook runs during step 4, but only fast checks. Full tests already passed in step 1.

## Git Commands

All standard git commands work normally:

```bash
# Standard commit - hook runs automatically
git commit -m "Add feature"

# Amend - hook runs on amended commit
git commit --amend

# Interactive rebase - hook runs on each commit
git rebase -i HEAD~3

# Bypass hook (emergency only)
git commit --no-verify -m "Hotfix"
```

## Tab Control Extension

If you're using a Git GUI or tab control extension:

- Pre-commit hooks run automatically on commit
- No configuration needed
- If commit fails, check terminal output for errors
- Auto-fixes (formatting) are applied automatically - just stage and retry

## Performance Comparison

### Before Optimization

```
Universal checks:     1.2s
detect-private-key:   0.8s
Ruff:                 0.5s
Black:                1.5s  ← Redundant with Ruff
Mypy (all files):     3.2s  ← Checking unchanged files
ESLint:               1.8s
TypeScript:           2.1s
Full test suite:      12.4s ← Too slow for pre-commit
─────────────────────────
Total:                23.5s ❌ Too slow!
```

### After Optimization

```
Universal checks:     0.8s
TruffleHog:          0.6s  ← Faster than detect-private-key
Ruff (lint+format):  0.5s  ← Replaces Black
Mypy (changed):      0.9s  ← Only changed files
Prettier:            0.4s  ← Auto-format frontend
ESLint:              1.2s
TypeScript:          0.8s  ← Only changed files
Fast tests:          1.5s  ← Only unit tests
─────────────────────────
Total:               6.7s → ~4.5s typical ✅ Fast enough!
```

## Troubleshooting

### "trufflehog: command not found"

```bash
# Install TruffleHog
brew install trufflesecurity/trufflehog/trufflehog

# Or use system detection (slower)
# Edit .pre-commit-config.yaml and change:
# language: system → language: golang
```

### "No tests ran"

Your tests need markers:

```bash
# Check current test markers
pytest --markers

# Run only fast tests (what pre-commit does)
pytest -m "not slow and not integration"

# Run all tests (what ship.sh does)
pytest tests/
```

### Hook takes > 5 seconds

```bash
# Profile hook execution
time pre-commit run --all-files

# Check which hook is slow
pre-commit run --verbose --all-files

# Common culprits:
# - Mypy checking too many files → Use pass_filenames: true
# - Tests not marked as slow → Add @pytest.mark.slow
# - TypeScript checking node_modules → Check tsconfig exclude
```

### False positive from TruffleHog

```bash
# View what was detected
trufflehog git file://. --since-commit HEAD

# Add to ignore file
echo "path/to/file:line_number" >> .trufflehogignore

# Or bypass this commit
git commit --no-verify -m "False positive"
```

## Best Practices

1. **Mark slow tests**: Any test > 1 second should have `@pytest.mark.slow`
2. **Mark integration tests**: Tests that hit external services need `@pytest.mark.integration`
3. **Let hooks auto-fix**: Don't manually format before committing - hooks do it
4. **Trust the process**: If hook passes, code is ready for review
5. **Use ship.sh for final validation**: Runs full test suite before push

## Migration Checklist

- [x] Remove `.secrets.baseline` (no longer needed)
- [x] Install TruffleHog (`brew install trufflesecurity/trufflehog/trufflehog`)
- [x] Update pre-commit config (`.pre-commit-config.yaml`)
- [x] Add pytest markers (`pytest.ini`)
- [x] Mark slow tests with `@pytest.mark.slow`
- [x] Mark integration tests with `@pytest.mark.integration`
- [x] Run `pre-commit install` to update hooks
- [x] Test with `pre-commit run --all-files`
- [x] Verify `./ship.sh "test"` still works

## Summary

**Before**: 23.5s pre-commit hook that developers bypass with `--no-verify`

**After**: 4.5s pre-commit hook that catches 90% of issues instantly

**Result**: Faster feedback, fewer CI/CD failures, happier developers
