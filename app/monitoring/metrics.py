# app/monitoring/metrics.py
from prometheus_client import Counter, Gauge, Histogram, generate_latest, CONTENT_TYPE_LATEST

REQUEST_COUNT = Counter(
    "astro_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status_code"],
)

REQUEST_LATENCY = Histogram(
    "astro_request_latency_seconds",
    "Latency of HTTP requests",
    ["endpoint"],
)

LAST_REPORT_ROWS = Gauge(
    "astro_last_report_rows",
    "Rows in last generated report"
)

LAST_REPORT_SESSIONS = Gauge(
    "astro_last_report_sessions",
    "Number of sessions in last report"
)
