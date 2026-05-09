# Technical Compliance Guidelines

## Purpose

This document establishes the mandatory technical standards for all development on the Predict-A-Trade v2.0 platform. Compliance with these guidelines is required for code to be merged into the `main` branch. These standards exist to ensure code quality, maintainability, security, and operational reliability across the codebase.

## Coding Standards

### Python (Backend Services)

All Python code must adhere to PEP 8 with the following project-specific additions:

- **Maximum line length:** 100 characters (not PEP 8's 79). This accommodates type annotations and modern Python patterns without sacrificing readability.
- **Type hints:** All public function signatures must include complete type annotations. Return types must always be specified. Use `| None` (Python 3.10+ union syntax), not `Optional[...]`.
- **Docstrings:** Google-style docstrings for all public modules, classes, and functions. Private helpers may use single-line summaries.
- **Imports order:** Standard library, third-party, local -- each group separated by a blank line. Use absolute imports (no relative imports outside of package-internal test files).
- **Async first:** All I/O-bound code must use `async/await`. Use `asyncio.gather()` for parallel execution. Avoid `run_in_executor` for CPU work (defer to separate worker processes).
- **Error handling:** Catch specific exceptions, never bare `except:`. Always log the exception with traceback before re-raising or handling.
- **Logging:** Use `structlog` for structured JSON logging. Log level: DEBUG for development, INFO for production. Never log secrets (API keys, passwords, tokens).

**Example:**

```python
"""Verdict aggregation module for the Master Engine."""

import asyncio
from datetime import datetime

import structlog
from pydantic import BaseModel

from pat_master.models import EngineSignal, Verdict

logger = structlog.get_logger(__name__)


async def aggregate_signals(
    signals: list[EngineSignal],
    timeout: float = 30.0,
) -> Verdict | None:
    """Aggregate engine signals into a final trading verdict.

    Args:
        signals: List of engine output signals to aggregate.
        timeout: Maximum time in seconds to wait for aggregation.

    Returns:
        A Verdict if aggregation succeeds, None if all engines timed out.

    Raises:
        SignalAggregationError: If signal fusion fails critically.
    """
    if not signals:
        logger.warning("aggregate_signals_no_input")
        return None
    ...
```

### TypeScript/React (Frontend)

- **Strict mode:** `tsconfig.json` must have `"strict": true`.
- **Functional components:** All React components must be function components using hooks. No class components.
- **Props interfaces:** Every component must define a named interface for its props, exported if the component is shared.
- **Early returns:** Handle loading, error, and empty states with early returns before the main render path.
- **CSS:** Use Tailwind CSS utility classes. Custom CSS is allowed in CSS Modules (`*.module.css`) only when Tailwind cannot express the style.
- **Server vs Client:** Explicit `"use client"` directive at the top of client components. Server components are the default in Next.js 15 App Router.

### Configuration and Infrastructure as Code

- **YAML style:** 2-space indentation, no tabs, trailing newline. List items always use the `- ` prefix.
- **Terraform:** All resources must have `description`, `environment`, and `managed_by` tags. Sensitive outputs must be marked `sensitive = true`.
- **Dockerfiles:** Multi-stage builds only. No secrets in build args. Use `.dockerignore` to exclude unnecessary files.
- **Shell scripts:** Must pass ShellCheck with zero errors. Use `set -euo pipefail` at the top of every script.

## Git Workflow

### Branching Strategy

```
main                  # Production-ready code. Protected. Requires PR + review + CI pass.
  feature/*          # New features and enhancements. Branched from main.
  fix/*              # Bug fixes. Branched from main.
  chore/*            # Maintenance: dependency updates, config changes, docs.
  release/*          # Release preparation branches.
```

### Commit Messages

Follow Conventional Commits 1.0.0:

```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

**Types:** `feat`, `fix`, `docs`, `style`, `refactor`, `perf`, `test`, `chore`, `ci`, `build`

**Scopes:** `master`, `api`, `frontend`, `data`, `execution`, `engine-cv`, `engine-ai`, `engine-di`, `engine-cw`, `engine-western`, `engine-cot`, `engine-seasonality`, `engine-macro`, `engine-tech`, `engine-exec`, `infra`, `docs`

**Examples:**
- `feat(master): add 15-dimension scoring framework`
- `fix(engine-cv): resolve memory leak in chart renderer`
- `docs(api): add WebSocket streaming examples`
- `chore(deps): update FastAPI to 0.115.x`

### Pull Request Requirements

1. **One logical change per PR.** No mixed concerns.
2. **PR title** matches the conventional commit format.
3. **Description** includes: what changed, why, testing performed, screenshots (if UI change), breaking changes.
4. **Reviewers:** At least one approving review from a team member who is not the author.
5. **CI checks:** All must pass: linting, type checking, unit tests, integration tests.
6. **Linear history:** Rebase onto `main`, do not merge `main` into the feature branch.
7. **Squash merge** into `main` (preserves clean history).

## Testing Requirements

### Coverage Thresholds

| Component       | Unit Test Coverage | Integration Test Requirement               |
|----------------|-------------------|-------------------------------------------|
| pat-master     | 80%+              | Full verdict pipeline happy + error paths  |
| pat-api        | 80%+              | Auth, rate limiting, all endpoints          |
| Engine families | 70%+              | Engine output validation against known fixtures |
| pat-data       | 75%+              | ETL pipeline, data validation, migrations   |
| pat-frontend   | 60%+              | Critical user flows (login, dashboard, settings) |
| pat-execution  | 80%+              | Order lifecycle, position tracking, risk checks |

### Test Organization

```
tests/
  unit/              # Fast, no external dependencies, mocked I/O
  integration/       # Real database, real service interactions
  e2e/               # Full system tests via docker compose or k8s
  fixtures/           # Test data, mock responses, golden files
```

### Testing Standards

- **Naming:** `test_<unit_under_test>__<scenario>__<expected_result>` (double underscore separators)
- **AAA pattern:** Arrange, Act, Assert -- clearly separated with blank lines
- **One assertion concept per test:** Multiple assertions on the same logical outcome are acceptable
- **No flaky tests:** Tests that fail intermittently must be fixed or quarantined within 24 hours
- **Test data:** Use factories or fixtures, never hardcoded IDs that may shift between runs

## Security Compliance

### Code-Level

1. **No secrets in code:** Zero tolerance. Secrets go in Vault (production) or `.env` (local, never committed). Pre-commit hooks scan for patterns matching API keys, tokens, and passwords.
2. **SQL injection prevention:** Use parameterized queries exclusively. Never string-format SQL. Use SQLAlchemy ORM or `asyncpg` with `$1` placeholders.
3. **Input validation:** All user input must be validated at the API boundary using Pydantic models with strict types and constraints.
4. **Output encoding:** API responses are JSON (auto-encoded). Frontend must use React's default XSS protection. Never use `dangerouslySetInnerHTML`.
5. **Dependency scanning:** `pip-audit` and `npm audit` run in CI on every PR. Critical/High findings block merge.
6. **Authentication:** JWT tokens expire at 1 hour. Refresh tokens at 7 days. API keys are hashed (SHA-256) before storage. Rate limiting enforced per key/user.
7. **Authorization:** Role-based access control (user, analyst, admin). Engine output access requires paid subscription tier.

### Infrastructure-Level

1. **TLS everywhere:** HTTPS for all public endpoints. Internal service communication over private networks. TLS 1.3 minimum.
2. **Least privilege:** Service accounts have minimal permissions. Engine services cannot access each other's data. Database user permissions scoped per service.
3. **Network segmentation:** Public, application, and data tiers on separate networks/VPCs. Firewall rules deny by default.
4. **Secrets rotation:** Database credentials rotated every 90 days. API keys can be revoked individually without platform impact.
5. **Audit logging:** All authentication events, admin actions, and data modifications logged to an append-only audit table.

### Regular Activities

- **Dependency updates:** Weekly automated PRs for patch updates; monthly reviews for minor/major updates.
- **Vulnerability scanning:** Container images scanned with Trivy on every build.
- **Penetration testing:** Annual external pen test; continuous automated scanning via OWASP ZAP in staging.
- **Security review:** Major features require a security review before merge (use `/security-review`).

## Accessibility Standards

The frontend must meet WCAG 2.2 Level AA compliance:

- **Color contrast:** Minimum 4.5:1 for normal text, 3:1 for large text.
- **Keyboard navigation:** All interactive elements reachable and operable via keyboard.
- **Screen readers:** Semantic HTML, ARIA labels where needed, alt text on all images.
- **Focus management:** Visible focus indicators, logical tab order.
- **Forms:** Labels associated with inputs, clear error messages, accessible validation feedback.

## Performance Budgets

| Metric                    | Target          | Measurement Tool     |
|--------------------------|----------------|---------------------|
| API p50 latency          | < 100ms         | Prometheus           |
| API p99 latency          | < 500ms         | Prometheus           |
| Verdict generation       | < 5 seconds      | Prometheus           |
| Frontend LCP             | < 2.5s          | Lighthouse CI        |
| Frontend FID             | < 100ms         | Lighthouse CI        |
| Frontend CLS             | < 0.1           | Lighthouse CI        |
| Frontend bundle size     | < 200 KB (gzip) | Next.js bundle analyzer |
| DB query (simple read)   | < 10ms          | pg_stat_statements   |
| DB query (analytical)    | < 500ms         | pg_stat_statements   |

Performance budgets are enforced in CI. PRs that regress beyond the threshold require explicit justification and approval.

## Documentation Standards

1. **API documentation:** Every endpoint must have an OpenAPI-documented schema with descriptions, parameter types, example requests and responses, and error codes.
2. **Architecture decisions:** Recorded in Architecture Decision Records (ADRs) in `docs/core/adr/`. Format: Title, Status, Context, Decision, Consequences.
3. **README per package:** Every top-level package/service must have a README covering: purpose, setup, environment variables, and how to run tests.
4. **Changelogs:** Keep a `CHANGELOG.md` at the repo root, updated on every release following Keep a Changelog format.
5. **Runbooks:** Operational runbooks in `docs/ops/` for common incidents (database failover, engine degradation, API overload).

## Dependency Management

### Python

- **Package manager:** `uv` (fast, reliable resolution with lock file)
- **Lock file:** `uv.lock` committed to the repository
- **Constraint:** Pin to exact versions in `pyproject.toml`; only direct dependencies listed
- **Update cadence:** Monthly `uv lock --upgrade` with reviewed changelogs

### JavaScript/TypeScript

- **Package manager:** Bun (`bun.lockb` committed)
- **Constraint:** Pin exact versions in `package.json`
- **Audit:** `bun audit` in CI; known vulnerabilities must be patched or explicitly accepted with comment

### Docker Images

- **Base images:** Pin to digest hashes, never use `latest` tag
- **Rebuild regularly:** Weekly rebuilds to pick up security patches in base images
- **Minimal images:** Use `python:3.12-slim` or `alpine` variants; no development tools in production images

### Infrastructure Tools

| Tool           | Version Constraint    |
|---------------|---------------------|
| Terraform      | >= 1.9, < 2.0       |
| Helm           | >= 3.15, < 4.0      |
| kubectl        | >= 1.30, < 2.0      |
| Docker         | >= 26.0             |
| hcloud CLI     | >= 1.48             |

## Enforcement

- **Pre-commit hooks:** Run linting, formatting, secret scanning, and type checking locally.
- **CI pipeline:** Blocks merge if any check fails. No bypass without documented exception.
- **Code review checklist:** Reviewers verify compliance with these guidelines.
- **Quarterly audit:** Automated scan of the full codebase for guideline violations.

Questions or requests for exceptions should be raised as GitHub issues with the `compliance-exception` label and discussed at the weekly engineering sync.
