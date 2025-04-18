import pytest


class Timer:
    def __init__(self):
        self.counter = 0.0

    def elapsed(self) -> float:
        self.counter += 1.0
        return self.counter

    def catchup(self, time: float) -> None:
        self.counter += time


@pytest.fixture(scope="function")
def timer():
    return Timer()


@pytest.fixture(scope="function")
def hub(timer):
    from app.framework import Hub

    return Hub(timer)


@pytest.fixture(scope="function")
def infra():
    from app.framework import ActorInfrastructure, ActorPool, Hub

    timer = Timer()
    hub = Hub(timer)
    pool = ActorPool()

    return ActorInfrastructure(
        hub,
        pool,
        timer,
        raw_channel=None,
        eeg_channel=None,
        quality_channel=None,
        packet_channel=None,
        median_eeg_channel=None,
    )
