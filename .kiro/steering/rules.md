---
inclusion: always
---

> **Note:** Global personas (`role:architect`, `role:coder`) and audit protocols (`audit:*`) are defined in `~/.kiro/steering/` and apply automatically. This file contains project-specific conventions and coding standards.
>
> For project overview, see `product.md`. For structure, see `structure.md`. For tech stack and commands, see `tech.md`.

# SHIP WORKFLOW

## Trigger: "ship"

When the user says **"ship"** (with or without a message), run `./ship.sh` via bash.

- If the user provides a message, use it: `./ship.sh "your message"`
- If no message is provided, ask for one before proceeding
- `./ship.sh` is interactive (TTY prompts). If it blocks on a prompt, pipe input: `echo "y" | ./ship.sh "message"`
- On failure: read the error, fix the root cause, re-run. Handle lint/type/test errors autonomously.

---

## Trigger: "ship with next tag" (and similar)

**Trigger phrases:** "ship with next tag", "tag and ship", "release it", or any intent to commit + tag.

**Do NOT run `./ship.sh`** — it requires a TTY and has interactive prompts. Instead, replicate its logic step-by-step using individual tool calls. This is the ONE exception to the "never commit/push" rule.

### Step-by-step execution

#### 1. Determine next tag

- Run: `git tag --merged HEAD --sort=-creatordate | head -10`
- Use only tags **reachable from HEAD** to avoid orphan tags on other branches inflating the version
- Parse the highest reachable semver tag as `vMAJOR.MINOR.PATCH`, increment patch → `vMAJOR.MINOR.(PATCH+1)`
- If no reachable tags exist, use `v0.1.0`
- Always use patch increment unless user says "minor" or "major"

#### 2. Determine commit message

- If user provided one, use it
- Otherwise inspect `git diff --staged` and unstaged changes to write a conventional commit message (`feat/fix/chore/refactor` etc.)

#### 3. Check for untracked files

- Run: `git ls-files --others --exclude-standard`
- If any exist, list them and ask the user: "Include these untracked files?"
- If confirmed, they'll be picked up by `git add .`

#### 4. Run tests

- Run: `export PYTHONPATH=. && python -m pytest tests/ -q --tb=short`
- If `--fast` was requested: add `-m "not slow and not integration"`
- If tests fail: attempt to fix, then re-run. If unfixable, stop and report.

#### 5. Format frontend

- Run: `cd frontend && npx prettier --write "**/*.{js,jsx,ts,tsx,json,css,scss,md,yaml,yml}" --ignore-unknown`
- Ignore errors (non-critical)

#### 6. Stage and commit (GPG signed)

- Run: `git add .`
- Run: `git commit -S -m "<commit message>"`
- If pre-commit hooks auto-fixed files: run `git add -u` then retry commit
- If nothing to commit: note it and continue to push
- If GPG signing fails: diagnose (`git config user.signingkey`, `gpg --list-secret-keys`, `pgrep gpg-agent`) and report clearly

#### 7. Capture commit SHA

- Run: `git rev-parse HEAD` — store as COMMIT_SHA for potential rollback

#### 8. Sync with remote

- Run: `git fetch origin <branch>`
- Check if behind: `git rev-list --count HEAD..origin/<branch>`
- If behind: attempt `git pull --ff-only origin <branch>`, then re-run tests
- If fast-forward fails: stop and tell user to rebase manually

#### 9. Push branch

- Run: `git push origin <branch>`
- If push fails: ask user if they want to undo the commit
- If yes: `git reset --soft <COMMIT_SHA>~1` (only if HEAD still matches COMMIT_SHA)
- Report clearly and stop

#### 10. Create GPG-signed tag

- Verify tag doesn't already exist: `git rev-parse <tag>` should fail
- Run: `git tag -s -m "Release <tag>" <tag>`
- If tag signing fails: diagnose GPG and report

#### 11. Push tag

- Run: `git push origin <tag>`
- If tag push fails: delete local tag (`git tag -d <tag>`) and report
- On success: report the tag and the GitHub Actions URL derived from remote URL

### Error handling

- Tests fail → fix and retry before committing
- GPG commit fails → diagnose signing key and agent
- Push rejected → offer soft reset, explain what to fix
- Tag already exists → increment to next available patch
- Fast-forward fails → stop, tell user to rebase

# ENGINEERING PRINCIPLES

- API-first design: Backend must remain fully usable without the frontend.
- Separation of concerns: Ingress (API), business logic (policy), and inference must remain modular.
- Explicit scalability boundaries: Document assumptions and limits (CPU-bound, single-process, etc.).
- Production-aware defaults: Favor predictable, observable, fail-safe behavior over clever optimizations.
- Backwards compatibility: Avoid breaking API contracts; version endpoints when necessary.
- Enterprise deployability: System must support isolated/on-prem environments without cloud dependency.

# CODING STANDARDS

## Backend (Python)

- Type hints for all functions (no `Any` unless justified)
- Google-style docstrings for public APIs
- PEP8 compliance; use `black`, `ruff`, and `mypy`
- Structured JSON logging with correlation IDs
- Log levels must be meaningful (INFO vs WARNING vs ERROR)
- Never log PII or raw sensitive content
- Use Pydantic for configuration and validation
- Async/await for I/O-bound operations only (avoid fake async)
- Business policy logic must live in a dedicated module (no duplication across routes)
- All API responses must include model version metadata

## Frontend (TypeScript)

- TypeScript strict mode enabled
- Explicit interfaces for all props and state
- Functional components with hooks (no class components)
- Material-UI (MUI) components for consistency
- Prettier and ESLint for formatting
- Error boundaries to isolate component crashes
- Frontend must degrade gracefully if backend unavailable
- UI must not assume synchronous API responses

## Testing

- Unit tests for utilities, rate limiters, circuit breakers
- Integration tests for full API flows
- Performance benchmarks for prediction latency
- Mock external dependencies in tests
- Use pytest for backend
- Aim for >80% coverage on critical paths
- Include at least one failure-mode test per endpoint
- Include regression tests for threshold/policy logic

# ACCESSIBILITY & UX PRINCIPLES

## Language & Clarity

- Use plain English; avoid ML jargon (say "confidence score" not "calibrated probability")
- All UI text must be understandable by non-technical users
- Error messages should explain what happened and what to do next
- Never show raw Python tracebacks to users
- Distinguish clearly between "confidence" and "final action" (ALLOW/REVIEW/BLOCK)

## Accessibility Requirements

- Keyboard navigation: All interactive elements must be focusable (Tab, Enter, Space)
- Screen reader compatible: Use proper ARIA labels and semantic HTML
- Color contrast: Follow WCAG 2.1 AA standards
- Focus indicators: Visible focus states on all interactive elements
- MUI components provide baseline accessibility; verify custom components

## UI Patterns

- Empty states: Show helpful guidance when no data is present
- Loading states: Use spinners or progress indicators for async operations
- Confirmation dialogs: Require confirmation for destructive actions
- Tooltips: Provide context for complex options
- Visual feedback: Show risk levels with clearly labeled badges (LOW/MEDIUM/HIGH)
- Consistent theming: Use MUI's theme system throughout
- API-first posture: UI should be demonstrative, not required for system usage

# SECURITY & PERFORMANCE

## Security Requirements

- API key authentication required for all prediction endpoints
- HMAC signature verification available for high-security deployments
- Rate limiting on authentication failures (5 attempts/minute)
- Input sanitization: Unicode normalization (NFKC) before processing
- Maximum input size enforced with configurable limit
- Model integrity: SHA256 checksum verification at startup
- Security headers: CSP, HSTS, X-Frame-Options, etc.
- Never log raw sensitive content; use hashing for debugging
- Audit logging with correlation IDs for traceability
- Document threat model assumptions in `THREAT_MODEL.md`

## Performance Optimization

- LRU cache (10,000 items) for repeated queries
- Gunicorn workers: `(2 x CPU cores) + 1`
- Batch processing parallelized with joblib
- Circuit breaker to prevent cascading failures
- Target latency: <10ms p50 for single predictions (document hardware assumptions)
- Explicitly document scaling limits in `SCALING_STRATEGY.md`

# MODEL & DATA GOVERNANCE

## Model Integrity

- Model files verified via SHA256 checksums at startup
- Model version included in all prediction responses
- Model card maintained in `MODEL_CARD.md` with:
  - Intended use and out-of-scope use
  - Performance metrics and limitations
  - Ethical considerations and bias risks
  - Failure modes and mitigation strategies
  - Evaluation dataset provenance

## Data Handling

- Dataset: Public HuggingFace dataset (guychuk/benign-malicious-prompt-classification)
- No PII logging; use hashing/sampling for audit logs
- Prediction logging includes: timestamp, label, confidence, correlation ID (no raw text)
- Data splits: 70% train / 15% validation / 15% test (never mix)
- Never mix evaluation data into policy threshold tuning

## Configuration Management

- All settings via environment variables (see `tech.md` for list)
- Validation at startup; fail-fast if required config missing
- Support for zero-downtime API key rotation (multiple active keys)
- Feature flags via environment variables for experimental features
- No hardcoded environment assumptions (must run in containerized environments)

# ERROR HANDLING

## API Error Responses

- Use RFC 7807 Problem Details format for structured errors
- Include correlation IDs in all error responses
- Provide actionable error messages (what happened + what to do)
- Return appropriate HTTP status codes (400, 401, 403, 429, 500, 503)
- Circuit breaker opens on repeated failures; return 503 with retry-after
- Never expose stack traces or internal file paths

## Graceful Degradation

- If model fails to load, system refuses to start (fail-fast)
- If prediction times out, return 503 with clear message
- Input validation rejects oversized or malformed inputs with 400
- Rate limit exceeded returns 429 with retry-after header
- If metrics subsystem fails, prediction service must continue operating

# OBSERVABILITY & OPERATIONS

- Health endpoint must verify model availability, not just process liveness
- Metrics endpoint must expose request counts, error rates, latency percentiles
- All logs must be machine-parseable JSON
- Correlation IDs must propagate through request lifecycle
- Model version must be visible in logs and API responses
- Document operational playbooks in `docs/OPERATIONS.md`

# ARCHITECTURAL DOCUMENTATION

- Maintain `SCALING_STRATEGY.md` documenting:
  - Current architecture assumptions
  - Known bottlenecks
  - What changes at 10x load
  - What changes at 100x load
- Maintain `THREAT_MODEL.md` documenting:
  - Attacker assumptions
  - Abuse scenarios
  - Failure impact analysis
- Maintain ADRs (Architecture Decision Records) for major changes

# AUDIT PROTOCOL INTEGRATION

> **Note:** Global audit protocols (`audit:logic`, `audit:ux`, `audit:sec`, `audit:arch`, `audit:perf`, `audit:test`, `audit:docs`, `audit:compliance`, `audit:devops`, `audit:ai`, `audit:env`, `audit:maintain`) are defined in `~/.kiro/steering/audit-protocols.md`.

## Project-Specific Audit Triggers

When working on this codebase, automatically apply relevant audits:

- **API endpoints** → `audit:sec` (input validation, auth, rate limiting, abuse amplification)
- **Model inference** → `audit:ai` (brittleness, adversarial inputs, threshold stability)
- **Frontend components** → `audit:ux` (plain language, accessibility, empty states)
- **Docker/deployment** → `audit:devops` (resource limits, isolation, secrets management)
- **Prediction logic** → `audit:logic` (null handling, edge cases, error propagation)
- **Performance changes** → `audit:perf` (latency, caching, parallelization)
- **Architecture changes** → `audit:arch` (scalability boundaries, coupling, service split readiness)

## Enforcement

- Audits run automatically based on file changes (implicit triggers)
- Explicit audit keywords override automatic inference
- Multiple audits may apply to complex changes
- Report only critical issues or high-value improvements
- Prefer architectural clarity over premature optimization
