# API Guide

## Overview

The Predict-A-Trade v2.0 REST API provides programmatic access to the Master Orchestrated Intelligence Layer (MOIL). It supports JWT (JSON Web Token) and API key authentication, exposes endpoints for verdict retrieval, engine output inspection, real-time WebSocket streaming, and platform administration.

**Base URL:** `https://api.predictatrade.com/v2`

All requests must use HTTPS. The API returns JSON responses with consistent error formatting. Timestamps are in ISO 8601 format with UTC timezone.

## Authentication

### JWT Authentication

Obtain a JWT by authenticating with email and password:

```bash
curl -X POST https://api.predictatrade.com/v2/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "your-password"}'
```

**Response:**

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "refresh_token": "dGhpcyBpcyBhIHJlZnJl...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

Include the token in all subsequent requests:

```bash
curl -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIs..." \
  https://api.predictatrade.com/v2/master/verdicts
```

Refresh an expired token:

```bash
curl -X POST https://api.predictatrade.com/v2/auth/refresh \
  -H "Content-Type: application/json" \
  -d '{"refresh_token": "dGhpcyBpcyBhIHJlZnJl..."}'
```

### API Key Authentication

Generate an API key from the dashboard (`Settings > API Keys`). Use the `X-API-Key` header:

```bash
curl -H "X-API-Key: pat_v2_a1b2c3d4e5f6..." \
  https://api.predictatrade.com/v2/master/verdicts
```

API keys support scoped permissions (read-only, trade-execute, admin). Each key is associated with a single user account and can be revoked individually.

## Core Endpoints

### Master Engine Verdicts

**GET /v2/master/verdicts**

Retrieve the latest trading verdicts from the Master Engine.

**Query Parameters:**

| Parameter    | Type    | Default | Description                              |
|-------------|---------|---------|------------------------------------------|
| `symbol`    | string  | --      | Filter by trading symbol (e.g., ES, NQ)  |
| `timeframe` | string  | `1d`    | Bar timeframe (1m, 5m, 15m, 1h, 4h, 1d)  |
| `from`      | ISO8601 | --      | Start of time range                      |
| `to`        | ISO8601 | --      | End of time range                        |
| `limit`     | integer | 50      | Max results (1-500)                      |
| `offset`    | integer | 0       | Pagination offset                         |
| `confidence_min` | float | 0.0    | Minimum confidence threshold (0.0-1.0)    |

**Response:**

```json
{
  "data": [
    {
      "verdict_id": "vrd_9x8y7z6w5v4u",
      "symbol": "ES",
      "timeframe": "1h",
      "timestamp": "2026-05-05T14:30:00Z",
      "direction": "LONG",
      "confidence": 0.87,
      "score": {
        "total": 83.5,
        "dimensions": {
          "trend": 88,
          "momentum": 76,
          "volatility": 80,
          "volume": 91,
          "support_resistance": 72,
          "pattern": 85,
          "sentiment": 90,
          "correlation": 79,
          "seasonality": 68,
          "macro": 82,
          "order_flow": 94,
          "market_structure": 77,
          "cycles": 73,
          "statistical": 89,
          "risk": 81
        }
      },
      "engine_contributions": [
        {"engine": "cv", "signal": 0.72, "weight": 0.10},
        {"engine": "ai", "signal": 0.65, "weight": 0.15},
        {"engine": "western", "signal": 0.80, "weight": 0.10}
      ],
      "generated_at": "2026-05-05T14:30:01.123Z"
    }
  ],
  "pagination": {
    "total": 1247,
    "limit": 50,
    "offset": 0,
    "next_offset": 50
  },
  "meta": {
    "request_id": "req_a1b2c3d4",
    "processing_ms": 45
  }
}
```

**POST /v2/master/verdicts/request**

Request a fresh verdict for a specific symbol and timeframe. This triggers the full 10-engine pipeline synchronously.

```bash
curl -X POST https://api.predictatrade.com/v2/master/verdicts/request \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"symbol": "ES", "timeframe": "1h"}'
```

### Engine Outputs

**GET /v2/engines/{engine_name}/outputs**

Retrieve raw output from a specific engine family. Available engine names: `cv`, `ai`, `di`, `cw`, `western`, `cot`, `seasonality`, `macro`, `tech`, `exec`.

```bash
curl -H "Authorization: Bearer $TOKEN" \
  "https://api.predictatrade.com/v2/engines/cv/outputs?symbol=ES&timeframe=1d"
```

**Response:**

```json
{
  "engine": "cv",
  "symbol": "ES",
  "timeframe": "1d",
  "output": {
    "signal": 0.72,
    "confidence": 0.84,
    "features_detected": ["double_bottom", "bullish_divergence", "volume_confirmation"],
    "chart_render_url": "https://api.predictatrade.com/v2/engines/cv/charts/vrd_9x8y7z6w5v4u.png",
    "metadata": {
      "model_version": "cv-resnet-v3.2",
      "inference_time_ms": 340
    }
  }
}
```

**GET /v2/engines**

List all engine families with status and health metrics:

```bash
curl -H "Authorization: Bearer $TOKEN" \
  https://api.predictatrade.com/v2/engines
```

### System and Health

**GET /v2/system/status**

Returns the overall platform health status, including all service healthchecks, database connectivity, Valkey status, and engine fleet status.

**GET /v2/system/metrics**

Returns aggregate platform metrics (requests per second, average latency, engine throughput, active WebSocket connections).

**GET /health** (unauth)

Public health endpoint for load balancer probes. Returns `{"status": "healthy"}` with HTTP 200.

## WebSocket API

Connect to real-time streaming at `wss://api.predictatrade.com/v2/ws`. Authentication is required. Pass the JWT as a query parameter:

```javascript
const ws = new WebSocket(
  `wss://api.predictatrade.com/v2/ws?token=${accessToken}`
);

ws.onopen = () => {
  // Subscribe to verdict stream for ES
  ws.send(JSON.stringify({
    action: "subscribe",
    channel: "verdicts",
    symbols: ["ES", "NQ"],
    timeframes: ["5m", "1h"]
  }));
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log("Verdict:", data.verdict_id, data.direction, data.confidence);
};
```

**Available channels:**

| Channel        | Description                              |
|---------------|------------------------------------------|
| `verdicts`    | Real-time verdicts as they are produced  |
| `engines`     | Individual engine outputs (per-engine)   |
| `alerts`      | System alerts, risk warnings, errors     |
| `market_data` | Streaming price/market data (tick/bar)   |

## Pagination

All list endpoints support cursor-based pagination:

```
GET /v2/master/verdicts?limit=50&offset=100
```

The response includes a `pagination` object with `total`, `limit`, `offset`, and `next_offset` fields. When `next_offset` is `null`, you have reached the last page.

## Rate Limiting

Rate limits are enforced per API key or JWT, returned in response headers:

```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1714924800
```

- **Free tier:** 100 requests per minute
- **Pro tier:** 1,000 requests per minute
- **Enterprise tier:** 10,000 requests per minute
- **WebSocket:** Max 5 concurrent connections per user

Exceeding the limit returns HTTP 429 with a `Retry-After` header.

## Error Codes

All errors follow a consistent format:

```json
{
  "error": {
    "code": "INVALID_SYMBOL",
    "message": "Symbol 'INVALID' is not supported.",
    "details": {
      "supported_symbols": ["ES", "NQ", "YM", "RTY", "CL", "GC", "ZB", "6E"]
    }
  },
  "request_id": "req_a1b2c3d4"
}
```

| HTTP Status | Code                  | Description                             |
|------------|----------------------|-----------------------------------------|
| 400        | `INVALID_REQUEST`     | Malformed request body or parameters    |
| 400        | `INVALID_SYMBOL`      | Unsupported trading symbol              |
| 400        | `INVALID_TIMEFRAME`   | Unsupported timeframe value             |
| 401        | `UNAUTHORIZED`        | Missing or invalid authentication       |
| 401        | `TOKEN_EXPIRED`       | JWT has expired, use refresh endpoint   |
| 403        | `FORBIDDEN`           | Insufficient permissions for resource   |
| 404        | `NOT_FOUND`           | Resource does not exist                 |
| 409        | `CONFLICT`            | Resource state conflict                 |
| 422        | `VALIDATION_ERROR`    | Request failed schema validation         |
| 429        | `RATE_LIMITED`        | Too many requests, retry after interval |
| 500        | `INTERNAL_ERROR`      | Unexpected server error                 |
| 502        | `ENGINE_UNAVAILABLE`  | Upstream engine service is down         |
| 503        | `SERVICE_UNAVAILABLE` | Platform is in maintenance mode         |

## Python Client Example

```python
import requests
from datetime import datetime, timedelta

BASE_URL = "https://api.predictatrade.com/v2"
TOKEN = "your-jwt-token"

headers = {"Authorization": f"Bearer {TOKEN}"}

# Fetch recent verdicts for ES
resp = requests.get(
    f"{BASE_URL}/master/verdicts",
    headers=headers,
    params={
        "symbol": "ES",
        "timeframe": "1h",
        "from": (datetime.utcnow() - timedelta(hours=24)).isoformat() + "Z",
        "limit": 100
    }
)

verdicts = resp.json()
for v in verdicts["data"]:
    print(f"{v['timestamp']} | {v['direction']} | confidence={v['confidence']:.2f} | score={v['score']['total']}")
```

## JavaScript/TypeScript Client Example

```typescript
interface Verdict {
  verdict_id: string;
  symbol: string;
  timeframe: string;
  direction: "LONG" | "SHORT" | "NEUTRAL";
  confidence: number;
  score: { total: number; dimensions: Record<string, number> };
}

async function getVerdicts(symbol: string): Promise<Verdict[]> {
  const resp = await fetch(
    `https://api.predictatrade.com/v2/master/verdicts?symbol=${symbol}&limit=50`,
    {
      headers: {
        Authorization: `Bearer ${process.env.PAT_API_TOKEN}`,
        "Content-Type": "application/json",
      },
    }
  );

  if (!resp.ok) {
    const err = await resp.json();
    throw new Error(`API Error ${err.error.code}: ${err.error.message}`);
  }

  const body = await resp.json();
  return body.data;
}
```

## SDKs and OpenAPI

The complete OpenAPI 3.1 specification is available at `https://api.predictatrade.com/v2/openapi.json`. Auto-generated client SDKs are available for:

- **Python:** `pip install predictatrade-client`
- **JavaScript/TypeScript:** `npm install @predictatrade/client`
- **Go:** `go get github.com/predictatrade/client-go`

## Additional Endpoints

### User Management

**GET /v2/users/me**

Retrieve information about the authenticated user.

**PUT /v2/users/me**

Update user profile information.

**GET /v2/users/api-keys**

List all API keys for the authenticated user.

**POST /v2/users/api-keys**

Create a new API key.

**DELETE /v2/users/api-keys/{key_id}**

Revoke an API key.

### Settings

**GET /v2/settings**

Retrieve user settings and preferences.

**PUT /v2/settings**

Update user settings and preferences.

### Notifications

**GET /v2/notifications**

Retrieve recent notifications and alerts.

**POST /v2/notifications/subscribe**

Subscribe to specific notification types.

## Response Format

All successful API responses follow this format:

```json
{
  "data": {...},           // The primary response data
  "meta": {...},           // Metadata about the response
  "pagination": {...}      // Pagination info (for list endpoints)
}
```

## Best Practices

1. **Cache appropriately**: Use the `Cache-Control` headers in responses to optimize client-side caching.
2. **Handle rate limits gracefully**: Check `X-RateLimit-Remaining` and implement exponential backoff when approaching limits.
3. **Use specific timeframes**: Request only the data you need to minimize response size and processing time.
4. **Validate tokens regularly**: Refresh JWTs before they expire to maintain uninterrupted access.
5. **Implement robust error handling**: Check for all possible error codes and handle them appropriately in your client code.

## Changelog

| Version | Date       | Changes                                            |
|---------|------------|---------------------------------------------------|
| v2.0.0  | 2026-05-01 | Initial v2 release. 15-dimension scoring, 10 engines |
| v2.1.0  | Planned    | Enhanced WebSocket, streaming market data, OAuth2   |