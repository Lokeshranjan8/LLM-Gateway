from prometheus_client import Counter

request_counter = Counter(
    "gateway_requests_total",
    "Total number of requests received by the gateway",
)