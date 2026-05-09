# Predict-A-Trade v2.0 — Technical Report

> **Document Type:** Technical Deep-Dive — Algorithms, Mathematics & Performance
> **Version:** 2.0.0
> **Date:** 2026-05-05
> **Scope:** MOIL mathematics, 15-dimension scoring, data pipeline, performance envelope, known limitations

---

## 1. Technical Overview of the MOIL Architecture

The Master-Orchestrated Intelligence Layer (MOIL) is a strictly layered hexagonal architecture where analysis and decision are cleanly separated. Ten engine families operate as stateless, isolated analysis units that produce structured **Engine Output Contracts** — JSON documents conforming to a shared schema. These contracts are consumed exclusively by the **Master Engine**, which normalises all inputs onto a common scoring space, applies dynamic weighting, discounts correlated signals via independence detection, resolves conflicts, evaluates hard override gates, and emits a single **Master Verdict Contract**.

The key architectural properties are:
- **Single Verdict Authority:** No engine can issue a trading recommendation. Only the Master Engine emits a recommendation band.
- **Immutable Audit Trail:** Every contract (engine and master) carries a SHA-256 content-hash that chains from engine input through to final verdict, enabling full historical replay verification.
- **Isolated Engines:** Engines share no state and do not communicate. Cross-engine correlation is handled exclusively by the Master Engine via the independence discount mechanism.

---

## 2. Master Engine Normalization Algorithm

Each engine family operates on a native score range (e.g., DI Engine: `[-70, +70]`, SMC-ICT Engine: `[0, +120]`). The Master Engine projects all scores onto the common interval `[-1.0, +1.0]` using **linear range mapping with configurable clipping**.

### 2.1 Linear Range Mapping

For engine `i` with native score `s_i` in range `[min_i, max_i]`:

```
normalized_direction_i = clip((s_i - min_i) / (max_i - min_i) * 2 - 1, -1.0, 1.0)
```

For asymmetric ranges (e.g., `[0, +120]` where zero represents no signal and +120 represents maximum bullishness), the mapping uses a split-normalisation:

```
if s_i >= 0:
    normalized_direction_i = s_i / max_i           # maps [0, max_i] → [0, +1]
else:
    normalized_direction_i = s_i / abs(min_i)      # maps [min_i, 0] → [-1, 0]
```

### 2.2 Score Clipping

After normalisation, values are clamped to `[-1.0, +1.0]`. Scores that exceed the engine's declared range (possible during edge cases or extrapolation) are clipped and flagged with an `out_of_range_warning` in the verdict metadata.

---

## 3. Directional Fusion Mathematics

### 3.1 Weighted Direction

The core fusion formula:

```
weighted_direction = Σ_i (w_i × normalized_direction_i) / Σ_i w_i
```

Where `w_i` is the dynamic weight for engine `i`, computed as:

```
w_i = α_i × β_i × γ_i
```

| Component | Symbol | Meaning |
|-----------|--------|---------|
| Historical Performance | `α_i` | Rolling 90-day Sharpe ratio of signals where this engine was the dominant contributor, normalised to `[0, 1]` via logistic transform |
| Regime Relevance | `β_i` | Classifier output: how well the engine performs in the current market regime (trending/ranging/breakout). Based on a regime-classifier model trained on ATR, ADX, and volatility cone data. |
| Temporal Alignment | `γ_i` | Decay factor: engines computed more recently have higher weight. `γ_i = exp(-λ × age_seconds)` with `λ` configured so that 60-second-old computations receive half weight. |

### 3.2 Direction Sign Determination

```
direction_sign = sign(weighted_direction)
direction_magnitude = |weighted_direction|
```

If `direction_magnitude < min_signal_threshold` (default 0.05), the direction is classified as NEUTRAL regardless of other dimensions.

---

## 4. Independence Discount Algorithm

### 4.1 Problem Statement

When two engines derive signals from overlapping information sources (e.g., DI Engine and WA Engine both use planetary positions from Swiss Ephemeris), their agreement does not represent independent confirmation — it represents a single information source counted twice. The Master Engine must detect this and discount accordingly.

### 4.2 Feature Overlap Matrix

A static `feature_overlap_matrix` is defined in `engine-overlap.yaml`, where each cell `(i, j)` contains the **Jaccard similarity** of engine `i` and engine `j`'s feature sets:

```
J(i, j) = |features_i ∩ features_j| / |features_i ∪ features_j|
```

Example values:

| Engine Pair | Jaccard | Rationale |
|-------------|---------|-----------|
| DI ↔ WA | 0.65 | Both use ephemeris positions, aspects, and retrograde data |
| AI ↔ Sentiment | 0.40 | Both use GLM-4 API and news sentiment |
| DI ↔ CW | 0.15 | Minimal overlap (different coordinate systems, different traditions) |
| SMC ↔ Technical | 0.30 | SMC uses OHLCV but entirely different methodology |
| Vision ↔ AI | 0.50 | Both use GLM-4 family models, different modalities |

### 4.3 Effective Weight Computation

For each engine `i`, the **independence-adjusted weight** is:

```
w_i_effective = w_i × Π_{j ≠ i} (1 - J(i, j) × w_j_active)
```

Where `w_j_active = 1` if engine `j` contributed to this analysis cycle, `0` if it was skipped or failed.

In practice, this means an engine's weight is attenuated by a fraction proportional to the weight of every other active engine multiplied by their feature overlap. Two nearly identical engines seeing the same data both get their weights reduced, preventing their agreement from dominating the verdict.

### 4.4 Independence Discount Dimension

The overall independence discount applied is recorded in the Master Verdict as:

```
independence_discount_applied = 1 - (Σ_i w_i_effective / Σ_i w_i)
```

A value near 0 means engines are largely independent. A value near 1 means heavy overlap and substantial discounting.

---

## 5. Conviction Calculation Methodology

Conviction is a Master-Engine-computed metric representing how unusual the current weighted direction is relative to its historical distribution.

### 5.1 Rolling Distribution

A rolling window (90 days) of `weighted_direction` values is maintained per instrument/timeframe pair. From this window, the **rolling mean** (`μ_s`) and **rolling standard deviation** (`σ_s`) are computed using Welford's online algorithm for numerical stability.

### 5.2 Conviction Score Formula

```
conviction_score = σ(|weighted_direction| / max(σ_s, ε))
```

Where `σ(x) = 1 / (1 + exp(-k × (x - c)))` is the logistic function with steepness `k` (default 5.0) and center `c` (default 1.5, meaning 1.5 standard deviations from the mean produces 0.5 conviction).

The `ε` floor (default 0.01) prevents division by zero when the rolling window has near-zero variance (e.g., extended ranging periods).

### 5.3 Confidence-Conviction Interaction

The final `calibrated_confidence` in the verdict is:

```
calibrated_confidence = conviction_score × (1 - conflict_ratio) × independence_factor
```

Where:
- `conflict_ratio` = proportion of engine pairs with opposing direction signs
- `independence_factor` = `1 - independence_discount_applied`

A highly convicted signal with conflicting engines or heavy feature overlap receives a proportionally lower confidence.

---

## 6. Fifteen-Dimension Scoring Framework

Every Master Verdict Contract contains scores on 15 independent dimensions, providing a comprehensive multi-axis view of signal quality.

| # | Dimension | Type | Range | Description |
|---|-----------|------|-------|-------------|
| 1 | `normalized_direction_score` | float | [-1.0, +1.0] | The Master Engine's fused directional signal |
| 2 | `calibrated_confidence` | float | [0.0, 1.0] | Probability-weighted confidence accounting for conviction, consensus, and independence |
| 3 | `engine_consensus_strength` | float | [0.0, 1.0] | How strongly engines agree on direction — `1.0` = unanimous, `0.0` = evenly split |
| 4 | `engine_conflict_ratio` | float | [0.0, 1.0] | Proportion of engine pairs with opposing signs — `0.0` = no conflict, `1.0` = maximum conflict |
| 5 | `evidence_quality_mean` | float | [0.0, 1.0] | Average `evidence_quality` across active engines, mapped to numeric scale (low=0.0, excellent=1.0) |
| 6 | `weighted_direction` | float | [-1.0, +1.0] | Raw weighted sum before any override processing, for transparency |
| 7 | `conviction_score` | float | [0.0, 1.0] | How many standard deviations the signal exceeds the rolling mean (logistic transform) |
| 8 | `independence_discount_applied` | float | [0.0, 1.0] | How much engine weights were discounted for feature overlap |
| 9 | `temporal_alignment` | float | [0.0, 1.0] | How temporally coherent engine outputs are — `1.0` = all computed within 1 second, `0.0` = widely staggered |
| 10 | `regime_relevance` | float | [0.0, 1.0] | How well the current market regime matches the engine ensemble's training distribution |
| 11 | `historical_sharpe_proxy` | float | [-inf, +inf] | Rolling Sharpe of the dominant engine's historical signals in this regime — negative values suppress direction |
| 12 | `override_gate_triggered` | bool | {true, false} | Whether any hard override gate is active |
| 13 | `gate_type` | string | enum | Which gate triggered: `none`, `di_kala`, `cw_flat`, `risk_circuit_breaker`, `exchange_halt`, `session_boundary` |
| 14 | `verdict_age_ms` | int | [0, +inf) | Milliseconds since Master Engine computation — for staleness detection by consumers |
| 15 | `immutability_hash` | string | 64 hex chars | SHA-256 hash covering all inputs and computed outputs for audit/replay verification |

---

## 7. Engine Output Contract Technical Specification

Every engine service exposes a uniform interface:

### Request (`POST /analyze`)
```json
{
  "instrument": "EURUSD",
  "timeframe": "H1",
  "bar_count": 500,
  "ephemeris_position": {
    "timestamp": "2026-05-05T14:00:00Z",
    "coordinates": "sidereal_lahiri",
    "bodies": ["sun", "moon", "mars", "mercury", "jupiter", "venus", "saturn"]
  },
  "request_id": "uuid-v4"
}
```

### Response — Engine Output Contract
```json
{
  "engine_id": "di",
  "engine_version": "2.0.0",
  "timestamp": "2026-05-05T14:00:00.123456Z",
  "instrument": "EURUSD",
  "timeframe": "H1",
  "request_id": "uuid-v4",
  "normalized_direction_score": 0.42,
  "calibrated_confidence": 0.73,
  "evidence_quality": "high",
  "raw_factors": {
    "hora_score": 8,
    "dasha_score": 12,
    "aspect_score": 15,
    "shadbala_score": 9,
    "nakshatra_score": 6,
    "kala_penalty": 0
  },
  "computation_time_ms": 8,
  "sha256_checksum": "a1b2c3d4e5f6..."
}
```

### Required Field Validation Rules

- `normalized_direction_score`: Must be in `[-1.0, +1.0]`. Exactly 15 decimal places.
- `calibrated_confidence`: Must be in `[0.0, 1.0]`. Exactly 15 decimal places.
- `evidence_quality`: Must be one of `["low", "medium", "high", "excellent"]`.
- `timestamp`: ISO 8601 with microsecond precision, UTC.
- `sha256_checksum`: Hex-encoded SHA-256 of `engine_id|timestamp|instrument|timeframe|normalized_direction_score|calibrated_confidence`.

---

## 8. Data Pipeline Latency Analysis

### 8.1 Ingestion Latency (Market Data)

| Stage | Latency (p95) | Notes |
|-------|---------------|-------|
| Provider API call | 200-800ms | TwelveData primary, Yahoo fallback |
| JSON deserialisation + validation | 5-10ms | Pydantic v2 model validation |
| TimescaleDB upsert (batch of 1000 bars) | 20-50ms | Single `INSERT ... ON CONFLICT` with chunked TimeScaleDB partitioning |
| **Total ingestion per instrument/timeframe** | **225-860ms** | Dominated by provider API |

### 8.2 Engine Compute Latency

| Engine | Cold Start | Warm (cached) | Notes |
|--------|-----------|---------------|-------|
| DI, CW, WA | 2-15ms | 2-15ms | Purely computational, no external API |
| SMC-ICT, Technical | 50-200ms | 50-150ms | OHLCV processing, NumPy vectorised |
| Macro, Sentiment | 100-500ms | 100-300ms | DB queries for external data |
| AI | 2000-5000ms | 2000-5000ms | GLM-4 API round-trip (dominates) |
| Vision | 3000-8000ms | 3000-8000ms | Chart render + GLM-4V API round-trip |
| Intermarket | 100-250ms | 100-250ms | Cross-asset correlation computation |

### 8.3 Master Engine Latency

| Stage | Latency |
|-------|----------|
| Input collection (Valkey Pub/Sub) | 1-10ms |
| Normalisation (10 engines) | < 1ms |
| Weight computation | 2-5ms |
| Independence discount | 1-3ms |
| Directional fusion | < 1ms |
| 15-dimension scoring | 3-8ms |
| Override gate evaluation | < 1ms |
| Output persistence (TimescaleDB + Valkey publish) | 5-15ms |
| **Total Master Engine** | **12-43ms** |

### 8.4 End-to-End Latency

Under normal conditions, the full pipeline (data available to verdict persisted) completes in:
- **Without AI/Vision engines:** 0.5-2 seconds
- **With AI and Vision engines:** 4-11 seconds (dominated by GLM-4 API calls)

The AI and Vision engines are configured with timeouts (10s) and the Master Engine will proceed with available engine outputs if AI/Vision responses are not yet received, flagging the verdict with `partial_engine_set = true` and reduced confidence. This ensures the pipeline is never blocked by a slow or unavailable LLM API.

---

## 9. System Performance Characteristics

### 9.1 Throughput

| Workload | Throughput |
|----------|------------|
| Single instrument, single timeframe, continuous | 1 verdict / 5-11 seconds |
| 10 instruments, 6 timeframes each (60 analysis cycles) | With 10 parallel engine instances: 60 verdicts / 10-15 seconds |
| REST API read queries (cached) | 200+ req/s per API instance |
| REST API write (verdict generation trigger) | 10 req/s (rate-limited) |
| WebSocket message fanout | 500+ msg/s with 200 connected clients |

### 9.2 Resource Consumption (per service, typical)

| Service | CPU (idle/load) | Memory | Disk I/O |
|---------|-----------------|--------|----------|
| pat-api (4 workers) | 2% / 30% (2 cores) | 256 MB / 512 MB | Low |
| pat-master | 1% / 15% (1 core) | 128 MB / 256 MB | Low |
| pat-data | 5% / 25% (1 core) | 128 MB / 512 MB | Moderate (ingestion writes) |
| pat-engine-ai | 1% / 5% (1 core) | 64 MB / 128 MB | None (API calls) |
| pat-engine-vision | 2% / 10% (1 core) | 128 MB / 256 MB | Chart render temp files |
| pat-engine-* (others) | 1% / 8% (1 core) | 64 MB / 128 MB | Low |
| PostgreSQL | 10% / 40% (4 cores) | 2 GB / 4 GB | High (continuous ingestion) |
| Valkey | 2% / 10% (1 core) | 256 MB / 1 GB | Moderate |

### 9.3 Database Sizing

| Data | Growth Rate | Retention | Steady-State Size |
|------|------------|-----------|-------------------|
| ohlcv_data (M1, 187 instruments) | ~50 GB/month | 90 days | ~150 GB |
| ohlcv_data (D1, 187 instruments) | ~200 MB/month | 10 years | ~24 GB |
| ephemeris_cache (17 bodies, 1h) | ~5 GB one-time | Permanent | ~5 GB |
| signals.master_verdicts | ~10 GB/month | 5 years | ~600 GB |
| ops.metrics | ~2 GB/month | 90 days | ~6 GB |
| **Total steady-state** | | | **~800 GB** |

---

## 10. Known Technical Limitations and Mitigations

| Limitation | Impact | Mitigation |
|-----------|--------|------------|
| **GLM-4 API Latency** | AI and Vision engines are the pipeline bottleneck at 2-8 seconds per call. | Asynchronous engine collection — Master Engine proceeds without AI/Vision if timeout exceeded. Cached responses for stable market conditions (no new bars, no ephemeris change). |
| **LLM Non-Determinism** | GLM-4 and GLM-4V responses can vary for identical inputs, breaking SHA-256 immutability. | Record LLM responses via `vcrpy` cassettes for replay testing. In production, the `raw_factors` field captures the LLM output and the checksum covers the interpretation, not the raw LLM text. |
| **Ephemeris Precision** | Swiss Ephemeris computes to arcsecond precision. Rounding differences between builds or platforms could produce divergent computations. | Ephemeris values are stored as double-precision floats in TimescaleDB. All engines read from the database, not direct PySwissEph calls. The ephemeris cache is the single source of truth for positions. |
| **TimescaleDB Chunk Overhead** | With 6 timeframes and 187 instruments, the number of hypertable chunks grows rapidly. | Automated `drop_chunks` policies for short-retention data. M1 data limited to 90 days. Chunk_time_interval set to 1 day for M1, 7 days for higher timeframes. |
| **Engine Failure Cascading** | If multiple engines fail simultaneously, the Master Engine operates with a partial engine set, reducing confidence. | Each engine is independently monitored. Health-check endpoints at `/health` are polled every 5 seconds. Engine failure alerts fire at first occurrence. The Master Engine records `partial_engine_set = true` and degraded confidence. |
| **Valkey Pub/Sub Message Loss** | Pub/Sub is fire-and-forget — subscribers that disconnect miss messages. | Critical verdicts are persisted to TimescaleDB before publishing. Consumers that detect gaps request backfill via the REST API. For execution-critical messages, Valkey Streams (with consumer groups and acknowledgement) supplement Pub/Sub. |
| **Regime Shift Detection Lag** | The regime classifier operates on a rolling window — it may lag behind sudden regime changes. | The `historical_sharpe_proxy` dimension provides a secondary, more reactive signal. When Sharpe drops sharply, engine weights are reduced even if the regime classifier has not yet updated. |
| **Startup Ephemeris Cold Start** | On first deploy, the 2015-2030 ephemeris cache must be precomputed (millions of rows). | One-time seed job runs during Phase 3 infrastructure setup. Takes approximately 30 minutes for full 15-year cache at 1-hour granularity for 17 bodies in two coordinate systems. Subsequent deploys use the existing cache. |

---

## 11. Mathematical Notation Summary

For academic reference and PhD thesis alignment:

```
Let E = {e_1, ..., e_n} be the set of n active engines (n ≤ 10).
Let s_i ∈ [min_i, max_i] be the native score of engine e_i.
Let norm(s_i) → [-1, +1] be the normalisation function.
Let w_i = α_i · β_i · γ_i be the dynamic weight.
Let w'_i = w_i · Π_{j≠i} (1 - J(i,j) · 1_{e_j active}) be the independence-adjusted weight.

Then:
  weighted_direction = Σ_i (w'_i · norm(s_i)) / Σ_i w'_i
  conviction_score = σ(|weighted_direction| / max(σ_s, ε))
  calibrated_confidence = conviction_score · (1 - conflict_ratio) · (1 - independence_discount_applied)

The Master Verdict recommendation band = f(weighted_direction, calibrated_confidence, override_gate_triggered)
```

---

*Technical Report — v2.0.0. All algorithm descriptions reference the production implementation at `app/services/master/` in the monorepo.*
