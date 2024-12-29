import time

Timestamp = float


class Timer:
    def __init__(self):
        self.start = time.time()

    def elapsed(self) -> Timestamp:
        return time.time() - self.start

    def catchup(self, timestamp: Timestamp) -> None:
        now = self.elapsed()
        if now < timestamp:
            time.sleep(timestamp - now)
