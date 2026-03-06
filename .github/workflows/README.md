# CI/CD Pipeline

GitHub Actions runs on every push to `main`/`develop` and every PR targeting those branches.

## What Runs

### Backend (Python)

- Ruff linting (style, imports, unused code, formatting)
- Mypy type checking
- Black formatting verification
- Pytest with coverage reporting

### Frontend (TypeScript/React)

- npm ci (clean install)
- ESLint
- TypeScript compiler (`tsc --noEmit`)
- Vite production build

### Docker

- Builds both backend and frontend images
- Validates Dockerfiles and multi-stage builds
- Uses layer caching for speed

### Security

- Trivy vulnerability scanner on the codebase
- Reports CRITICAL and HIGH severity issues
- Results uploaded to GitHub Security tab

## Run Locally

```bash
# Backend
ruff check src/ api/ tests/
mypy src/ api/
black --check src/ api/ tests/
pytest tests/ -v --cov=src

# Frontend
cd frontend
npm ci
npm run lint
npx tsc --noEmit
npm run build

# Docker
docker build -t test-backend .
docker build -t test-frontend --build-arg VITE_API_URL=http://localhost:8000 ./frontend
```

## Quality Gates

All checks must pass before merging. Failed checks block the PR. Results are in the "Checks" tab.

Skip CI on docs-only commits (use sparingly):

```bash
git commit -m "docs: update README [skip ci]"
```

## Troubleshooting

- Backend tests fail locally but pass in CI: check Python version (CI uses 3.11) and install `requirements-dev.txt`
- Frontend build fails: clear `node_modules` and run `npm ci`. CI uses Node 20.
- Docker build fails: check `.dockerignore` and verify model files exist in `models/`
