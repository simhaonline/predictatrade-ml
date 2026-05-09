# Predict-A-Trade v2.0 — Test-Driven Development Strategy

> **Document Type:** Testing Strategy & Quality Gates
> **Version:** 2.0.0
> **Date:** 2026-05-05
> **Scope:** Full greenfield MOIL test strategy — contracts, engines, master, integration, validation, performance

---

## 1. Philosophy: Contract-First Testing

All development in MOIL v2.0 follows a **contract-first** discipline. Before any implementation code is written for a service, the JSON Schema that governs its inputs and outputs must be published, versioned, and accompanied by at least three test fixtures (valid, invalid, edge case). No code review passes without corresponding test coverage that validates contract compliance.

This approach eliminates the most common source of integration failure in distributed systems: mismatched assumptions about message shapes.

---

## 2. Contract-First Testing: Engine Output Schema Validation

**Objective:** Every engine family's output conforms exactly to the `engine-output-contract-v2.0.json` schema.

**Test Structure:**
- **Schema compliance tests** — each engine's test suite includes a parametrised test that runs the engine against a known input fixture, captures the output, and validates against the JSON Schema using `jsonschema.validate()` or `pydantic.TypeAdapter.validate_python()`.
- **Required field tests** — for each required field, a test verifies the field is present and non-null in every output.
- **Range enforcement tests** — `normalized_direction_score` must be in `[-1.0, +1.0]`; `calibrated_confidence` must be in `[0.0, 1.0]`; `evidence_quality` must be one of the four enumerated values.
- **Determinism tests** — running the same engine twice with identical inputs (including the same random seed where applicable) must produce identical checksums. A mismatch fails the build.

**Fixture Location:** `/tests/fixtures/engine-outputs/{engine_id}/`

---

## 3. Master Engine Test Harness: Deterministic Score Reproduction

**Objective:** The Master Engine, given identical sets of Engine Output Contracts, must produce identical Master Verdict Contracts — bit-for-bit identical, verified by SHA-256 comparison.

**Harness Design:**
- A `MasterEngineTestHarness` class accepts a list of precomputed Engine Output Contract JSON files as input.
- It passes them through the full Master Engine pipeline (normalise, weight, independence-discount, directional fusion, 15-dim score, override gates).
- It compares the output `sha256_checksum` against a known expected value stored in the test fixture.
- Any deviation triggers a structured diff report showing which dimension changed and by what magnitude.

**Key Test Scenarios (minimum 50 fixtures):**
1. All engines unanimous strong bullish (expect `AGGRESSIVE_LONG`)
2. All engines unanimous strong bearish (expect `AGGRESSIVE_SHORT`)
3. Mixed signals below conflict threshold (expect directional call with moderate conviction)
4. Mixed signals above conflict threshold (expect `HEDGE`)
5. DI Kala penalty active (expect `FLAT` regardless of composite score)
6. CW mandatory flat threshold triggered (expect `FLAT`)
7. Single engine failure — engine missing from input set (expect graceful degradation, lower confidence)
8. High-confidence signal with low evidence quality (expect `CAUTIOUS_*` band, not full position)
9. Empty engine set (expect `FLAT` with zero confidence)
10. Temporal misalignment — engines computed at different timestamps (expect staleness penalty, reduced weight)

**Fixture Location:** `/tests/fixtures/master-verdicts/`

---

## 4. Per-Engine Test Strategy

Each of the ten engine families follows a uniform testing structure:

### Isolated Unit Tests
- Every computational function in the engine is testable in isolation with mocked dependencies.
- Example: DI Engine's `compute_aspect_score(positions)` is tested with hand-crafted planetary positions at known aspect angles (exact trine, exact square, 3-degree orb, 8-degree orb, out of orb).

### Deterministic Fixture Tests
- Each engine has at least one "golden fixture" — a known input producing a known output, independently verified during Phase 0 contract drafting.
- Engines that depend on external APIs (GLM-4, data providers) use **recorded HTTP responses** via `vcrpy` or a similar cassette library. Tests run offline in CI.

### Mocked Dependency Tests
- `pat-engine-ai` tests mock the Zhipu AI SDK to return canned responses.
- `pat-engine-vision` tests mock the chart renderer and GLM-4V client.
- `pat-engine-sentiment` tests mock the FinBERT inference pipeline.
- All external API calls are mockable via dependency injection — no test reaches the live internet.

### Score Range Tests
- Each engine is tested at the extremes of its native score range to ensure clipping works correctly.
- Example: SMC-ICT Engine tested with perfectly bullish structure (expect +120) and no structure (expect 0).

---

## 5. Integration Tests: Engine to Master to API Pipeline

**Objective:** Verify the full analysis pipeline functions end-to-end with real (or realistically simulated) data flowing through actual service boundaries.

**Pipeline Integration Test Suite:**
1. **Engine-to-Master:** Spin up a test instance of one engine service and the Master Engine. The engine receives a request, produces an Engine Output Contract, publishes to Valkey. The Master Engine consumes it and produces a verdict. Assert the verdict references the correct engine ID and the checksum chain is intact.
2. **Master-to-API:** The Master Engine publishes a verdict to the `verdicts:{instrument}:{timeframe}` Valkey channel. The API's Valkey bridge receives it and makes it available via the REST endpoint `GET /v2/master/verdicts/{id}`. Assert the JSON matches.
3. **API-to-WebSocket:** A WebSocket client connects, subscribes to the verdict channel for an instrument/timeframe, and asserts it receives the verdict within the latency SLA (p95 < 100ms from Valkey publish to client receive).
4. **Full Pipeline:** Ingest synthetic OHLCV bars into TimescaleDB, trigger all ten engines in parallel, wait for Master Engine verdict, retrieve via REST, and compare against a known expected verdict for that synthetic data.

**Test Infrastructure:** Docker Compose stack with all services, a small TimescaleDB volume pre-seeded with synthetic data, and Valkey. The full pipeline test runs as a CI job on every push to `main`.

---

## 6. Walk-Forward Validation Framework

**Objective:** Automate statistical validation of the complete MOIL pipeline against historical data.

**Framework Design:**
- A `WalkForwardValidator` class accepts a date range, a list of instruments, and timeframe parameters.
- For each test window, it replays historical data through the full MOIL pipeline (all engines + Master Engine).
- It records every verdict alongside the subsequent price movement.
- It computes: directional accuracy (did the market move in the predicted direction within the holding period?), Sharpe ratio, Calmar ratio, win rate, profit factor, max drawdown, average favourable/adverse excursion.
- Results are compared against the technical-only baseline (Engines 5, 8, 10 only, no metaphysical, no AI/Vision).

**CI Execution:** Walk-forward validation runs weekly (not per-commit due to compute cost) and fails if the full MOIL Sharpe ratio drops below the technical-only baseline or falls below 0.8.

---

## 7. Historical Replay Testing: Reproducibility Verification

**Objective:** Guarantee that the same historical data replayed through the system produces identical verdicts every time — critical for regulatory audit and research credibility.

**Mechanism:**
- A `HistoricalReplayRunner` ingests timestamps from the past, fetches the exact OHLCV data available at that timestamp (not future data), and feeds it to the MOIL pipeline.
- The emitted Master Verdict Contract is stored alongside its SHA-256 immutability hash.
- On a subsequent replay, the runner recomputes the verdict and compares checksums.
- Any checksum mismatch triggers a structured diff and blocks deployment.

**Coverage Requirement:** At least one replay test per engine family per quarter (2024 Q1 through 2025 Q4) for EURUSD at H1 timeframe — minimum 80 replay scenarios.

---

## 8. Performance Test Thresholds

| Metric | Threshold | Measurement Method |
|--------|-----------|--------------------|
| Single engine analysis latency (p95) | < 1s (non-AI), < 8s (AI/Vision) | `locust` timed task execution |
| Master Engine adjudication latency (p95) | < 100ms | Instrumented timer in Master Engine |
| Full pipeline end-to-end (p95) | < 10s | Timer from trigger to verdict persistence |
| REST API response time (p95) | < 200ms | NGINX access log parsing |
| WebSocket verdict delivery (p95) | < 100ms from Valkey publish | Timestamp delta in message envelope |
| Database query performance (single instrument, 500 bars) | < 50ms | `EXPLAIN ANALYZE` in test suite |
| Concurrent WebSocket connections | 200 sustained without message loss | `locust` WebSocket plugin |
| REST throughput | 50 req/s sustained | `locust` HTTP user simulation |
| Engine memory per instance | < 512 MB | `psutil` monitoring in performance tests |
| CPU utilisation per engine instance | < 2 cores at full load | `psutil` monitoring |

Performance tests run on every PR against a staging environment. Threshold violations block merge.

---

## 9. CI/CD Test Gates and Coverage Requirements

### Per-Commit Gates (fast, < 5 minutes)
- **Lint:** `ruff check`, `mypy --strict`, `eslint` — zero warnings
- **Unit tests:** All engine unit tests, Master Engine harness tests (50+ fixtures), contract validation tests
- **Coverage floor:** 85% line coverage for Master Engine, 80% for each engine family

### Per-PR Gates (medium, < 15 minutes)
- **Integration tests:** Full pipeline integration test suite (Docker Compose)
- **Schema compliance:** All contract fixtures validated
- **Determinism checks:** All engine determinism tests pass
- **Security scan:** `bandit` (Python), `npm audit` (frontend), dependency vulnerability check

### Per-Merge to Main (comprehensive, < 30 minutes)
- **Performance test:** Staging environment load test with thresholds
- **Walk-forward:** Abbreviated walk-forward (last 6 months, top 10 instruments)
- **Historical replay:** Spot-check 20 replay scenarios

### Pre-Release Gates (full, runs overnight)
- **Full walk-forward:** All instruments, full date range
- **Full historical replay:** 200+ scenarios
- **Security audit:** Full OWASP Top 10 penetration test
- **Disaster recovery drill:** Simulated DB loss and restore

---

*TDD Strategy — v2.0.0. All test fixtures stored in `/tests/fixtures/`. Coverage reports generated via `pytest-cov` and uploaded to Grafana dashboard.*
