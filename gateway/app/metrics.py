"""All Prometheus metrics live here and are registered only once.
Importing this module registers every metric. Keep it free of imports from other app modules to avoid circular imports.
"""

from prometheus_client import Counter, Histogram

# Requests that reach /v1/chat.
gateway_requests_total = Counter(
    "gateway_requests_total",
    "Total number of chat requests received by the gateway",
)

# Calls made to each provider (mock_a, mock_b, later ollama).
provider_requests_total = Counter(
    "provider_requests_total",
    "Total number of calls made to each provider",
    labelnames=["provider"],
)

# Failed provider calls.
provider_failures_total = Counter(
    "provider_failures_total",
    "Total number of failed calls made to each provider",
    labelnames=["provider"],
)

# Retry attempts made by the retry helper.
retry_total = Counter(
    "retry_total",
    "Total number of retry attempts",
)

# Times the gateway switched from primary to fallback provider.
fallback_total = Counter(
    "fallback_total",
    "Total number of times the gateway switched to a fallback provider",
)

# Requests rejected by the token-bucket rate limiter (HTTP 429).
rate_limit_hits_total = Counter(
    "rate_limit_hits_total",
    "Total number of requests rejected by the Redis rate limiter",
)

# End-to-end latency of /v1/chat requests.
gateway_request_duration_seconds = Histogram(
    "gateway_request_duration_seconds",
    "Latency of /v1/chat requests in seconds",
    buckets=(0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0),
)
