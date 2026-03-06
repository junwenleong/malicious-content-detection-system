# Pre-commit Hook Setup

## Install

```bash
pip install -r requirements-dev.txt
./scripts/setup-hooks.sh
```

That's it. Every `git commit` now runs quality checks automatically.

## What It Checks

The hook runs in under 5 seconds and covers:

- Trailing whitespace, end-of-file fixes, YAML/JSON syntax
- Large file detection (>1MB), merge conflict markers
- Secret detection via TruffleHog (700+ credential types)
- Python: Ruff lint + format, Mypy type checking (changed files only)
- Frontend: Prettier format, ESLint lint, TypeScript (changed files only)
- Fast unit tests only (tests not marked `@pytest.mark.slow` or `@pytest.mark.integration`)

## When It Auto-Fixes

Ruff and Prettier will auto-fix formatting issues. If that happens, the commit is blocked so you can review the fixes:

```bash
git add .           # Stage the auto-fixes
git commit -m "..."  # Try again
```

## Bypass (Emergency Only)

```bash
git commit --no-verify -m "Hotfix: critical bug"
```

Fix linting in the next commit. Don't make this a habit.

## TruffleHog Secret Detection

Replaced `detect-private-key` and `detect-secrets` with TruffleHog for better accuracy and fewer false positives.

Install: `brew install trufflesecurity/trufflehog/trufflehog`

Handle false positives:

```bash
echo "path/to/file:line_number" >> .trufflehogignore
```

## Troubleshooting

**Hook not running:**

```bash
ls -la .git/hooks/pre-commit   # Check if it exists
./scripts/setup-hooks.sh        # Reinstall
```

**Linting passes locally but fails in CI:**

```bash
pip install -r requirements-dev.txt  # Update deps
cd frontend && npm install           # Update frontend deps
```

## How It Fits Together

| Layer           | When         | Duration | What it catches                                        |
| --------------- | ------------ | -------- | ------------------------------------------------------ |
| Pre-commit hook | Every commit | < 5s     | 90% of issues (formatting, types, secrets, fast tests) |
| `ship.sh`       | Before push  | ~10s     | Full test suite + everything above                     |
| CI/CD           | On push/PR   | 2-5min   | Full tests, builds, Docker images, security scans      |

The hook is the fast filter. Heavy validation happens in `ship.sh` and CI/CD.
