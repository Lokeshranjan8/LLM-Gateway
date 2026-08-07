import time
from app.config import settings

class Tokenbucket:
    def __init__(self):
        self.capacity=settings.token_bucket_capacity
        self.refill_rate=settings.refill_rate
        self.current_tokens=self.capacity
        self.last_refill_time=time.time()

    def refill_tokens(self):
        elapsed_time =time.time() - self.last_refill_time
        tokens_to_add = int(elapsed_time * self.refill_rate)
        if tokens_to_add > 0:
            self.current_tokens =min(
                self.current_tokens + tokens_to_add,
                self.capacity,
            )
            self.last_refill_time = time.time()

    def take_token(self) ->bool:
        if self.current_tokens > 0:
            self.current_tokens -= 1
            return True
        return False

    def check_rate_limit(self) ->bool :
        self.refill_tokens()
        allowed = self.take_token()

        if allowed:
            print("Request allowed.")
        else:
            print("Rate limit exceeded.")

        return allowed

    









