import time


class CircuitBreaker:
    def __init__(self, provider_name: str, failure_threshold: int, cooldown_seconds: int) -> None:
        self.provider_name = provider_name
        self.failure_threshold = failure_threshold
        self.cooldown_seconds = cooldown_seconds
        self.state = "CLOSED"
        self.failure_count = 0
        self.opened_at = None
        print(f"Circuit CLOSED for {self.provider_name}")

    def can_call_provider(self) -> bool:
        if self.state == "CLOSED":
            return True

        if self.state == "OPEN":
            seconds_open = time.monotonic() - self.opened_at

            if seconds_open < self.cooldown_seconds:
                print(f"Skipping for now {self.provider_name} as cooldown not expired")
                return False

            print(f"Cooldown expired for {self.provider_name}")
            print(f"Half-Open Testing started for {self.provider_name}")
            self.state = "HALF_OPEN"
            return True

        # While one Half-Open request is running, use the fallback for new requests.
        print(f"Skipping for now {self.provider_name} (Half-Open test already running)")
        return False

    def record_success(self) -> None:
        if self.state == "HALF_OPEN":
            print(f"It was open {self.provider_name} So,im closing thecircuit ")

        self.state = "CLOSED"
        self.failure_count = 0
        self.opened_at = None

    def record_failure(self) -> None:
        if self.state == "HALF_OPEN":
            print(f"Half-Open request failed for {self.provider_name}")
            self._open_circuit()
            return

        self.failure_count += 1
        print(f"Failure count for {self.provider_name}: {self.failure_count}")

        if self.failure_count >= self.failure_threshold:
            self._open_circuit()

    def _open_circuit(self) -> None:
        self.state = "OPEN"
        self.failure_count = self.failure_threshold
        self.opened_at = time.monotonic()
        print(f"Opening circuit for {self.provider_name} for {self.cooldown_seconds} seconds")
