# Predict-A-Trade v2.0 — Reference

> **Document Type:** Glossary, Schema Reference & Quick Reference
> **Version:** 2.0.0
> **Date:** 2026-05-05

---

## 1. Glossary

| Term | Definition |
|------|-----------|
| **MOIL** | Master-Orchestrated Intelligence Layer — the six-layer hexagonal architecture where ten independent engine families feed analysis into a single authoritative Master Engine. Named for the Yiddish _moil_ (ritual circumciser), reflecting the architecture's role in cleanly separating analysis from decision. |
| **Master Engine** | The sole verdict authority in the MOIL architecture. Consumes Engine Output Contracts, normalises across engines, computes dynamic weights, applies independence discounts, resolves conflicts, evaluates hard override gates, and emits a single Master Verdict Contract. No engine can issue a trading recommendation. |
| **Engine Output Contract** | A JSON document produced by each engine family per analysis cycle, conforming to a shared JSON Schema (`engine-output-contract-v2.0.json`). Contains `engine_id`, `timestamp`, `instrument`, `timeframe`, `normalized_direction_score` (range `[-1.0, +1.0]`), `calibrated_confidence` (`[0.0, 1.0]`), `evidence_quality` (enum: `low|medium|high|excellent`), `raw_factors` (engine-specific detail), and `sha256_checksum` for immutability. |
| **Master Verdict Contract** | The authoritative output document emitted by the Master Engine, conforming to `master-verdict-contract-v2.0.json`. Contains all 15 dimension scores, the composite recommendation band, aggregated confidence, override gate status, and a content-hash covering all inputs and computed outputs. |
| **15-Dimension Scoring** | The multi-axis evaluation framework applied by the Master Engine to every analysis cycle. Dimensions include: `normalized_direction_score`, `calibrated_confidence`, `engine_consensus_strength`, `engine_conflict_ratio`, `evidence_quality_mean`, `weighted_direction`, `conviction_score`, `independence_discount_applied`, `temporal_alignment`, `regime_relevance`, `historical_sharpe_proxy`, `override_gate_triggered`, `gate_type`, `verdict_age_ms`, `immutability_hash`. |
| **Independence Discount** | A weighting adjustment applied when two or more engines share informational inputs. Computed as `1 - overlap_coefficient` where the coefficient is the Jaccard similarity of feature sets. Prevents double-counting correlated signals (e.g., DI and WA both derive features from planetary positions). |
| **Override Gate** | A hard rule that forces a FLAT verdict regardless of composite score. Includes: DI Kala penalty (Rahu Kala, Gulika, Yamaganda periods), CW mandatory flat threshold, risk circuit breakers (max drawdown exceeded), exchange halts (trading suspended), and session boundaries (illiquid periods). |
| **Recommendation Band** | The actionable output classification: `AGGRESSIVE_LONG`, `LONG`, `CAUTIOUS_LONG`, `NEUTRAL`, `CAUTIOUS_SHORT`, `SHORT`, `AGGRESSIVE_SHORT`, `HEDGE`, `FLAT`, `BLOCK`. Determined by composite score magnitude, conviction, conflict ratio, and override gate status. |
| **Engine Family** | A group of related analytical engines sharing a domain. Ten families exist: AI, DI, CW, WA, SMC-ICT, Vision, Macro, Technical, Sentiment, Intermarket. |
| **Walk-Forward Validation** | An expanding-window backtesting methodology that trains models on rolling historical windows and tests on subsequent unseen windows, preventing look-ahead bias. |
| **Conviction Score** | A Master-Engine-computed metric `σ((|weighted_direction| - μ) / σ_s)` — the logistic transform of how many standard deviations the weighted direction exceeds the rolling mean, producing a value in `(0, 1)`. Higher conviction = stronger signal relative to historical distribution. |
| **Directional Fusion** | The Master Engine's mathematical process of combining normalised engine direction scores via `weighted_direction = Σ(w_i · normalized_direction_i)`, where `w_i` are dynamic engine weights and `normalized_direction_i` is the engine's output mapped to `[-1.0, +1.0]`. |

---

## 2. Scoring Ranges Reference

### Normalized Direction Score
| Value | Interpretation |
|-------|----------------|
| +1.00 | Unanimous strong bullish across all active engines |
| +0.50 to +0.99 | Predominantly bullish, some engines neutral/cautious |
| +0.20 to +0.49 | Mildly bullish, significant neutral or mixed signals |
| -0.19 to +0.19 | Directionless — no consensus, likely FLAT or HEDGE |
| -0.20 to -0.49 | Mildly bearish |
| -0.50 to -0.99 | Predominantly bearish |
| -1.00 | Unanimous strong bearish |

### Calibrated Confidence (`[0.0, 1.0]`)
| Range | Interpretation |
|-------|----------------|
| 0.80 – 1.00 | High confidence — historical engine agreement strongly predictive |
| 0.60 – 0.79 | Moderate confidence — actionable but with reservation |
| 0.40 – 0.59 | Low confidence — signal present but historically unreliable in this regime |
| 0.00 – 0.39 | No confidence — do not trade |

### Evidence Quality (per-engine ENUM)
| Value | Description |
|-------|-------------|
| `excellent` | High-quality input data, engine operating within calibrated regime, all factors computable |
| `high` | Data complete, regime normal, minor factor gaps |
| `medium` | Partial data, engine operating near regime boundary |
| `low` | Degraded inputs, extrapolated factors, fallback computation |

### Recommendation Bands
| Band | Condition | Action |
|------|-----------|--------|
| `AGGRESSIVE_LONG` | weighted_direction > +0.75, conviction > 0.80, no conflict | Maximum bullish allocation |
| `LONG` | weighted_direction > +0.40, conviction > 0.60 | Standard bullish position |
| `CAUTIOUS_LONG` | weighted_direction > +0.20, conviction > 0.50, conflict ratio < 0.3 | Reduced-size bullish position |
| `NEUTRAL` | |weighted_direction| < 0.20 | No position, monitor |
| `CAUTIOUS_SHORT` | weighted_direction < -0.20, conviction > 0.50, conflict ratio < 0.3 | Reduced-size bearish position |
| `SHORT` | weighted_direction < -0.40, conviction > 0.60 | Standard bearish position |
| `AGGRESSIVE_SHORT` | weighted_direction < -0.75, conviction > 0.80, no conflict | Maximum bearish allocation |
| `HEDGE` | High directional score but conflict_ratio > 0.4 | Long/short pair trade or options hedge |
| `FLAT` | Override gate triggered, or conviction < 0.40 | No position |
| `BLOCK` | Risk circuit breaker active, exchange halt, or Kala penalty | Trading prohibited |

---

## 3. API Endpoint Reference (v2)

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| `GET` | `/v2/master/verdicts` | List recent Master Verdicts with pagination (`?page=1&limit=50`) | JWT |
| `GET` | `/v2/master/verdicts/{verdict_id}` | Single verdict with full 15-dimension breakdown | JWT |
| `GET` | `/v2/master/verdicts/stream` | WebSocket upgrade for real-time verdict stream | JWT (WS) |
| `GET` | `/v2/engines/` | List all engine families with health status | JWT |
| `GET` | `/v2/engines/{engine_id}/outputs` | Recent engine outputs for given engine family | JWT |
| `GET` | `/v2/engines/{engine_id}/health` | Engine health — latency p50/p95/p99, error rate, uptime | JWT (analyst+) |
| `POST` | `/v2/master/analyze` | Trigger analysis cycle for instrument/timeframe | JWT (analyst+) |
| `GET` | `/v2/instruments/` | List all instruments with metadata | JWT |
| `GET` | `/v2/backtest/walk-forward` | Walk-forward validation results | JWT (admin) |
| `GET` | `/v2/backtest/historical-replay` | Historical replay results | JWT (admin) |
| `GET` | `/v2/ops/health` | Aggregate system health (public, no auth) | None |
| `GET` | `/v2/ops/metrics` | Prometheus metrics endpoint | None (internal) |

---

## 4. Engine Families Quick Reference

| Engine ID | Name | Native Score Range | Key Dependencies | Approx. Compute (ms) |
|-----------|------|--------------------|------------------|----------------------|
| `ai` | AI Engine | [-80, +80] | GLM-4 API, prompt templates | 2000-5000 |
| `di` | DI Engine | [-70, +70] | PySwissEph, ephemeris cache | 5-15 |
| `cw` | CW Engine | [-50, +50] | Lunisolar calendar, I-Ching tables | 2-8 |
| `wa` | WA Engine | [-30, +30] | Tropical ephemeris, natal chart | 3-10 |
| `smc` | SMC-ICT Engine | [0, +120] | OHLCV bars (500+) | 50-150 |
| `vision` | Vision Engine | [-100, +100] | GLM-4V API, chart renderer | 3000-8000 |
| `macro` | Macro Engine | [-60, +60] | COT data, economic calendar | 100-300 |
| `technical` | Technical Engine | [-80, +80] | OHLCV bars (200+), 33 indicators | 50-200 |
| `sentiment` | Sentiment Engine | [-40, +40] | FinBERT model, news feed | 200-500 |
| `intermarket` | Intermarket Engine | [-50, +50] | Cross-asset OHLCV, ETF data | 100-250 |

---

## 5. Configuration File Reference

| File | Purpose | Format |
|------|---------|--------|
| `/etc/pat/master.yaml` | Master Engine configuration — weight strategy, conflict thresholds, independence discount matrix, override gate parameters | YAML |
| `/etc/pat/engines.yaml` | Per-engine configuration — model paths, API keys (referenced via env vars), feature flags, score range overrides | YAML |
| `/etc/pat/data.yaml` | Data pipeline config — provider priority order, refresh intervals per timeframe, retention policies, quarantine thresholds | YAML |
| `/etc/pat/api.yaml` | API configuration — rate limits per tier, CORS origins, WebSocket heartbeat interval, JWT expiry | YAML |
| `/etc/pat/execution.yaml` | Execution config — bridge endpoints, max position size per instrument, circuit breaker thresholds | YAML |
| `/etc/pat/monitoring.yaml` | Monitoring config — alert rules, log levels, metric collection intervals | YAML |
| `/srv/predictatrade.com/.env` | Secrets — DB connection strings, API keys, HMAC shared secrets, JWT signing key, S3 credentials | dotenv |

---

## 6. Environment Variables Quick Reference

| Variable | Purpose | Required |
|----------|---------|----------|
| `PAT_ENV` | Environment: `development`, `staging`, `production` | Yes |
| `DATABASE_URL` | Async PostgreSQL connection string (`postgresql+asyncpg://...`) | Yes |
| `VALKEY_URL` | Valkey connection string (`valkey://host:port/db`) | Yes |
| `JWT_SECRET_KEY` | HS256 signing key for JWT tokens (min 32 chars) | Yes |
| `MASTER_HMAC_KEY` | HMAC-SHA256 key for inter-service message signing | Yes |
| `ZHIPU_API_KEY` | Zhipu AI API key for GLM-4/GLM-4V | Yes (AI/Vision engines) |
| `TWELVEDATA_API_KEY` | TwelveData API key for market data | Yes (production) |
| `WASABI_ACCESS_KEY` / `WASABI_SECRET_KEY` | Wasabi S3 credentials for backups | Yes (production) |
| `STRIPE_SECRET_KEY` | Stripe API secret for billing | Yes (billing) |
| `TELEGRAM_BOT_TOKEN` | Telegram Bot API token for alerts | No |
| `DISCORD_WEBHOOK_URL` | Discord webhook for alerts | No |
| `TWILIO_ACCOUNT_SID` / `TWILIO_AUTH_TOKEN` | Twilio credentials for SMS alerts | No |

---

## 7. SHA-256 Immutability

Every Engine Output Contract and Master Verdict Contract includes a `sha256_checksum` field computed as:

```
SHA-256(
    engine_id + "|" +
    timestamp.isoformat() + "|" +
    instrument + "|" +
    timeframe + "|" +
    normalized_direction_score (15 decimal places) + "|" +
    calibrated_confidence (15 decimal places)
)
```

For the Master Verdict Contract, the checksum additionally covers all input engine checksums, ensuring end-to-end immutability from engine output through to final verdict. Any discrepancy during historical replay indicates data corruption, code regression, or non-deterministic computation — all of which trigger immediate investigation.

---

*Reference — v2.0.0. All schema paths relative to `/contracts/v2.0/` in the monorepo.*
