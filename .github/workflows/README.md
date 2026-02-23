# CI/CD Pipeline Documentation

## Overview

This repository uses GitHub Actions for Continuous Integration (CI). The pipeline automatically runs on:
- Every push to `main` or `develop` branches
- Every pull request targeting `main` or `develop`

## Pipeline Jobs

### 1. Backend Tests & Linting

**What it does:**
- **Ruff Linting**: Checks Python code style, import sorting, unused imports, and formatting
- **Mypy Type Checking**: Validates type hints and catches type errors
- **Black Formatting**: Ensures consistent code formatting (88 char line length)
- **Pytest Unit Tests**: Runs test suite with coverage reporting

**Why it matters:**
- Catches bugs before they reach production
- Enforces consistent code style across the team
- Validates business logic works correctly
- Provides code coverage metrics

**Run locally:**
```bash
# Linting
ruff check src/ api/ tests/

# Type checking
mypy src/ api/

# Formatting
black --check src/ api/ tests/

# Tests
pytest tests/ -v --cov=src
```

### 2. Frontend Build & Lint

**What it does:**
- **npm ci**: Clean install of dependencies
- **ESLint**: Checks TypeScript/React code style
- **TypeScript Compiler**: Type checks without emitting files
- **Vite Build**: Compiles and bundles for production

**Why it matters:**
- Catches TypeScript errors before deployment
- Ensures production build works
- Validates all imports resolve correctly
- Enforces React best practices

**Run locally:**
```bash
cd frontend

# Install
npm ci

# Lint
npm run lint

# Type check
npx tsc --noEmit

# Build
npm run build
```

### 3. Docker Build Test

**What it does:**
- Builds both backend and frontend Docker images
- Uses layer caching to speed up builds
- Validates Dockerfiles are correct

**Why it matters:**
- Ensures Docker images build successfully
- Catches deployment issues early
- Validates multi-stage builds work

**Run locally:**
```bash
# Backend
docker build -t test-backend .

# Frontend
docker build -t test-frontend --build-arg VITE_API_URL=http://localhost:8000 ./frontend
```

### 4. Security Scan

**What it does:**
- Runs Trivy vulnerability scanner on the codebase
- Checks for known vulnerabilities in dependencies
- Reports CRITICAL and HIGH severity issues
- Uploads results to GitHub Security tab

**Why it matters:**
- Identifies security vulnerabilities early
- Tracks security issues over time
- Helps maintain secure dependencies

## Quality Gates

The CI pipeline acts as a quality gate:
- ✅ All checks must pass before merging
- ❌ Failed checks block the merge
- 🔍 Review results in the "Checks" tab of your PR

## When to Skip CI

You can skip CI on specific commits (use sparingly):
```bash
git commit -m "docs: update README [skip ci]"
```

## Troubleshooting

### Backend tests fail locally but pass in CI
- Check Python version (CI uses 3.11)
- Ensure all dependencies are installed: `pip install -r requirements-dev.txt`
- Check environment variables are set

### Frontend build fails
- Clear node_modules: `rm -rf frontend/node_modules && cd frontend && npm ci`
- Check Node version (CI uses 20)
- Verify TypeScript errors: `cd frontend && npx tsc --noEmit`

### Docker build fails
- Check .dockerignore is correct
- Ensure model files exist in `models/` directory
- Verify build context is correct

## Improving the Pipeline

Future enhancements:
- Add integration tests with Docker Compose
- Add E2E tests with Playwright
- Add performance benchmarks
- Add automatic deployment on successful builds
- Add dependency update automation (Dependabot)
