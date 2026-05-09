# Predict-A-Trade vNext — User Guide

> **Version:** 2.0 | **Audience:** End Users (Traders, Analysts, Subscribers)
> **Scope:** Verdict Terminal usage, alerts, API keys, subscription management

---

## 1. Getting Started

### 1.1 Account Creation

1. Navigate to `https://predictatrade.com/register`
2. Enter email, password (min 12 chars, 1 uppercase, 1 number, 1 symbol)
3. Verify email via the 6-digit code sent to your inbox
4. Complete profile: display name, timezone, preferred instruments
5. Choose subscription tier (Free / Pro $29/mo / Elite $99/mo)

### 1.2 Verdict Terminal Overview

The Verdict Terminal is the primary interface. It displays **one canonical verdict per
instrument per timeframe** as computed by the Master Engine — the single source of truth
for all trading decisions on the platform.

**Key UI Sections:**

| Section | Purpose |
|---|---|
| **Master Verdict Bar** | Top-level: direction, conviction %, recommendation band, execution readiness |
| **15-Dimension Radar** | Spider/radar chart showing score across all 15 Master dimensions |
| **Contributor Engine Panel** | Per-engine breakdown: direction score, weight, calibrated confidence, evidence quality |
| **Conflict Monitor** | Active conflicts between engines with severity classification |
| **Scenario Cards** | Bull/Base/Bear/Failure cases with probability % and key drivers |
| **Override & Risk Banner** | Active overrides, circuit breakers, risk state (normal/reduced/blocked) |
| **Verdict History Timeline** | Scrollable history of past verdicts for comparison |

### 1.3 Reading a Verdict

```
┌─────────────────────────────────────────────────────────┐
│ XAUUSD · H1 · 2026-05-05 14:30 UTC                      │
│                                                         │
│ MASTER VERDICT: CONSTRUCTIVE LONG  ↗                     │
│ Net Direction: +62/100  ·  Conviction: 74%              │
│ Execution: READY  ·  Mode: SEMI-AUTO                    │
│                                                         │
│ Bull 45%  │ Base 35% │ Bear 15% │ Failure 5%           │
└─────────────────────────────────────────────────────────┘
```

**Direction Bands:**

| Band | Meaning | Action Expected |
|---|---|---|
| Aggressive Long | Strong multi-engine consensus bullish | Consider full size long |
| Constructive Long | Lean bullish, minor conflicts resolved | Consider reduced size long |
| Watch | Near neutral with slight tilt | Monitor only, no action |
| Neutral | No directional edge detected | Stay flat |
| Constructive Short | Lean bearish, minor conflicts resolved | Consider reduced size short |
| Aggressive Short | Strong multi-engine consensus bearish | Consider full size short |
| Block | Execution blocked by override or breaker | No trading permitted |

---

## 2. Drilling Into Contributor Engines

Click any engine in the Contributor Panel to expand its full output:

- **Normalized Direction Score** — what the engine contributed (-100 to +100)
- **Calibrated Confidence** — Master Engine-adjusted confidence (original raw confidence also shown)
- **Evidence Quality** — how strong the underlying evidence is
- **Freshness** — how recent the data feeding this engine's output is
- **Independence Hint** — how much unique evidence this engine brings (vs. overlap)
- **Key Factors** — the specific drivers the engine identified
- **Risk Flags** — any danger signals published by this engine (passed to Master for adjudication)
- **Recommended Use** — what the engine believes its output is best used for (timing/context/positioning/prediction/execution_gating)

### 2.1 Understanding Conflicts

Conflicts appear in the Conflict Monitor panel. They are classified:

| Conflict Type | Example | Master's Handling |
|---|---|---|
| Timeframe vs Evidence | COT bearish on D1, CV bullish on M5 | Timeframe-fit discount applied; M5 takes priority |
| Symbolic vs Observable | DI eclipse warning vs strong CV long | DI treated as risk modulation only; CV directional weight unchanged |
| Stale vs Fresh | 4-hour-old AI signal vs 30-second CV signal | Freshness penalty on stale engine |
| High-Quality Disagreement | AI strongly bullish, strongly bearish CV on M1 | Conviction capped; Verdict = "Watch" |

---

## 3. Alerts & Notifications

### 3.1 Alert Types

| Alert | Trigger | Channels |
|---|---|---|
| Verdict Change | Master verdict direction or band changes | Email, Telegram, Webhook, Push |
| Conviction Threshold | Conviction crosses above/below your set % | Email, Telegram |
| Execution Readiness | Execution mode changes (ready/conditional/blocked) | Telegram, Push |
| Conflict Alert | New high-severity conflict detected | Email, Telegram |
| Override Applied | Any Master override applied | Email |
| Daily Summary | End-of-day summary of all verdicts for your instruments | Email |

### 3.2 Configuring Alerts

1. Navigate to **Settings → Alerts**
2. Click **+ New Alert Rule**
3. Select instrument(s), timeframe(s), alert type
4. Set thresholds (e.g., conviction > 70%)
5. Choose delivery channels
6. Save

### 3.3 Supported Channels

| Channel | Setup Required |
|---|---|
| Email | Verified email (default) |
| Telegram | Connect via `/start` bot link in Settings |
| Webhook | Provide HTTP endpoint, secret header supported |
| Discord | Connect via webhook URL |
| Push | Mobile browser notification permission |

---

## 4. API Access

### 4.1 Generating API Keys

1. Navigate to **Settings → API Keys**
2. Click **Create API Key**
3. Enter label (e.g., "My Algo Bot"), select scopes
4. Select expiry (never / 30d / 90d / 365d)
5. Copy the key — it will **not** be shown again

### 4.2 API Rate Limits

| Tier | Requests / Minute | Concurrent WebSocket Streams |
|---|---|---|
| Free | No API access | 1 |
| Pro | 300 | 5 |
| Elite | 1,000 | Unlimited |

### 4.3 Quick API Examples

```bash
# Get latest master verdict for XAUUSD H1
curl -s -H "Authorization: Bearer $API_KEY" \
  https://api.predictatrade.com/v2/master/verdicts/XAUUSD/H1/latest

# Get engine contributions for a specific verdict
curl -s -H "Authorization: Bearer $API_KEY" \
  https://api.predictatrade.com/v2/master/verdicts/XAUUSD/H1/contributors

# Subscribe to WebSocket for real-time verdicts
wscat -c "wss://api.predictatrade.com/v2/ws/verdicts?token=$API_KEY&instrument=XAUUSD"
```

---

## 5. Subscription Management

### 5.1 Tier Comparison

| Feature | Free | Pro ($29/mo) | Elite ($99/mo) |
|---|---|---|---|
| Instruments | 1 (XAUUSD) | 15 | 104 (all) |
| Timeframes | H1, H4, D1 | All 9 | All 9 |
| Verdicts / day | 5 | 50 | Unlimited |
| Verdict history | 7 days | 90 days | Unlimited |
| Alert rules | 2 | 10 | Unlimited |
| API access | No | Yes (300/min) | Yes (1000/min) |
| WebSocket streams | 1 | 5 | Unlimited |
| Export (JSON/CSV) | No | Yes | Yes |
| MQL5 Export | No | No | Yes |
| Backtesting | No | 100/mo | Unlimited |
| Execution Bridge | No | Manual only | Semi-Auto + Autonomous |
| Priority support | Community | Email (24h) | Priority (4h) |

### 5.2 Upgrading / Downgrading

1. Navigate to **Settings → Billing**
2. Select desired tier, billing cycle (monthly / annual — 20% discount)
3. Payment via **Stripe** (cards) or **NOWPayments** (crypto: BTC, ETH, USDT, USDC)
4. Upgrade is instant; downgrade takes effect at end of current billing period

### 5.3 Quota Tracking

Navigate to **Settings → Usage** to see current period:
- Verdict views used / remaining
- API calls made / limit
- Backtests run / remaining
- Active alert rules / limit

---

## 6. Export & Integration

### 6.1 Export Formats

| Format | Tier | Use Case |
|---|---|---|
| JSON | Pro+ | Custom analysis, algorithmic consumption |
| CSV | Pro+ | Spreadsheet analysis, backtesting in external tools |
| MQL5 (.mqh) | Elite | Direct import into MetaTrader 5 Expert Advisors |

### 6.2 MetaTrader Integration (Elite)

1. Export signals as `.mqh` from the Verdict Terminal
2. Copy to `<MT5_Data_Folder>/MQL5/Include/PredictATrade/`
3. Load the PredictATrade EA onto your XAUUSD chart
4. Configure: execution mode (autonomous/semi-auto/manual), risk %, circuit breakers
5. The EA consumes only Master Engine verdicts via the ZeroMQ bridge (not raw engine outputs)

---

## 7. Frequently Asked Questions

**Q: Why does the Master Engine sometimes disagree with individual engines?**
A: Engines analyze independently; they don't see each other's outputs. The Master Engine considers all engines, applies independence discounts (to avoid double-counting overlapping evidence), resolves conflicts, and calibrates confidence. Disagreement is a feature — it means the Master is doing its job of not blindly averaging.

**Q: What does "Conviction: Low" with a strong direction mean?**
A: The net direction is strong, but the Master has low confidence in it — likely due to unresolved conflicts, stale evidence, or low evidence quality. The Master recommends "Monitor Only" in this state. Do not trade on strong direction + low conviction.

**Q: Can I see what each engine said individually?**
A: Yes. Click any engine in the Contributor Panel for the full breakdown, or use the API endpoints `/v2/engines/{name}/outputs` (API access requires Pro+).

**Q: Why is a trade blocked even though the score is positive?**
A: Execution Readiness is a separate dimension. Circuit breakers (spread too wide, liquidity vacuum, volatility halt) or active Master overrides (eclipse window, risk reduction) can block execution regardless of directional score.

**Q: How do I report a problem with a verdict?**
A: Use the "Flag Verdict" button in the Verdict Terminal. This creates a research ticket visible to the platform analysts. Do not email individual engine outputs — the Master Engine verdict is the canonical record.
