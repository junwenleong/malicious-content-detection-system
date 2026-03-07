---
inclusion: always
---

# Task Planning — Think Before You Code

## When to Plan First

Before writing any code, output a planning block when the task involves:

- Modifying the predictor interface or inference layer (`src/inference/`)
- Changing the API request/response contract (`src/api/schemas.py`)
- Adding or removing a dependency from `requirements.txt` or `package.json`
- Touching core config files (`src/config.py`, `.env` variables)
- Modifying the policy/decision logic (`src/utils/policy.py`)
- Changes to authentication or middleware (`src/api/auth.py`, `src/api/middleware.py`)
- Any change that affects more than 3 files
- Anything the user describes as "refactor", "redesign", or "migrate"

## Planning Block Format

Output this before writing code:

```
[PLAN]
What: <one sentence — what is changing>
Why: <one sentence — the reason>
Files affected: <list of files>
Risk: <Low / Medium / High — and why>
Approach: <2-4 bullet points of what you'll do, in order>
[/PLAN]
```

Then ask: "Does this look right before I proceed?" — unless the user has already confirmed the approach.

## When NOT to Plan

Skip the planning block for:

- Single-file bug fixes with obvious scope
- Typo / string / comment changes
- Test additions that don't change production code
- Frontend styling tweaks (CSS/theme changes)

## High-Risk Signals (Always Plan)

**Never modify the predictor interface without planning.** The predictor is the core inference layer. Changes cascade to routes, caching, and batch processing. Breaking the interface breaks the entire API.

**Never change the decision threshold or policy logic without planning.** The threshold (0.536) is calibrated on the validation set. Changes affect all downstream risk levels and actions. Must be validated against test data.

**Never add new environment variables without planning.** Config changes must be validated at startup and documented. Missing vars should fail-fast, not silently default.

**Never modify the API request/response schema without planning.** The schema is the contract with clients. Breaking changes require API versioning or coordinated client updates.

**Never change the model loading or caching strategy without planning.** The LRU cache (10k items) and model integrity checks are critical for performance and security. Changes affect latency and reliability.

**Never modify authentication or rate limiting without planning.** These are security boundaries. Changes can introduce vulnerabilities or break existing integrations.

**Never change the frontend API integration without planning.** The frontend assumes specific endpoint behavior and response formats. Breaking changes require coordinated frontend updates.
