from typing import Any

from app.data_processing import Median
from app.framework import Actor, ActorInfrastructure, Channel, ChannelID, Eeg, MedianEeg, Timestamp


class Sink(Actor):
    def __init__(self, test_size: int, infra: ActorInfrastructure):
        super().__init__(
            infra,
            name="test_median",
            channels=[infra.median_eeg_channel.id],
            capture_thread=False,
            run_to_completion=False,
        )
        self.collected: list[MedianEeg] = []
        self.test_size = test_size

    def handle(self, channel: ChannelID, timestamp: Timestamp, data: Any) -> None:
        match channel:
            case self._infra.median_eeg_channel.id:
                median_eeg = self._infra.median_eeg_channel.read(data)
                self.collected.append(median_eeg)
            case _:
                raise ValueError(f"don't know how to handle data from channel {channel}")

    def act(self) -> bool:
        keep_running = len(self.collected) < self.test_size
        return keep_running


def test_median(infra: ActorInfrastructure, mocker) -> None:
    test_size = 10
    window_size = 5

    mocker.patch("app.data_processing.median.WINDOW_SIZE", window_size)

    infra.eeg_channel = Channel("eeg", infra.hub)
    infra.median_eeg_channel = Channel("median_eeg", infra.hub)
    Median(infra)
    sink = Sink(test_size, infra)

    input = [
        Eeg(
            delta=i,
            theta=i,
            low_alpha=i,
            high_alpha=i,
            low_beta=i,
            high_beta=i,
            low_gamma=i,
            mid_gamma=i,
        )
        for i in range(test_size)
    ]
    for eeg in input:
        infra.hub.publish(infra.eeg_channel.id, eeg)

    infra.pool.start()
    infra.pool.wait()
    infra.pool.stop()

    given = sink.collected
    expected = [
        MedianEeg(  # Position 0: window not filled yet, output 0
            delta=0, theta=0, low_alpha=0, high_alpha=0, low_beta=0, high_beta=0, low_gamma=0, mid_gamma=0
        ),
        MedianEeg(  # Position 1: window not filled yet, output 0
            delta=0, theta=0, low_alpha=0, high_alpha=0, low_beta=0, high_beta=0, low_gamma=0, mid_gamma=0
        ),
        MedianEeg(  # Position 2: window not filled yet, output 0
            delta=0, theta=0, low_alpha=0, high_alpha=0, low_beta=0, high_beta=0, low_gamma=0, mid_gamma=0
        ),
        MedianEeg(  # Position 3: window not filled yet, output 0
            delta=0, theta=0, low_alpha=0, high_alpha=0, low_beta=0, high_beta=0, low_gamma=0, mid_gamma=0
        ),
        MedianEeg(  # Position 4: window size (5) reached, median of [0,1,2,3,4]
            delta=2, theta=2, low_alpha=2, high_alpha=2, low_beta=2, high_beta=2, low_gamma=2, mid_gamma=2
        ),
        MedianEeg(  # Position 5: median of [1,2,3,4,5]
            delta=3, theta=3, low_alpha=3, high_alpha=3, low_beta=3, high_beta=3, low_gamma=3, mid_gamma=3
        ),
        MedianEeg(  # Position 6: median of [2,3,4,5,6]
            delta=4, theta=4, low_alpha=4, high_alpha=4, low_beta=4, high_beta=4, low_gamma=4, mid_gamma=4
        ),
        MedianEeg(  # Position 7: median of [3,4,5,6,7]
            delta=5, theta=5, low_alpha=5, high_alpha=5, low_beta=5, high_beta=5, low_gamma=5, mid_gamma=5
        ),
        MedianEeg(  # Position 8: median of [4,5,6,7,8]
            delta=6, theta=6, low_alpha=6, high_alpha=6, low_beta=6, high_beta=6, low_gamma=6, mid_gamma=6
        ),
        MedianEeg(  # Position 9: median of [5,6,7,8,9]
            delta=7, theta=7, low_alpha=7, high_alpha=7, low_beta=7, high_beta=7, low_gamma=7, mid_gamma=7
        ),
    ]

    assert len(given) == len(expected), f"expected {len(expected)} items, but got {len(given)}"

    for i, (g, e) in enumerate(zip(expected, given, strict=False)):
        assert g == e, f"{i}: expected\n{g}\nbut got\n{e}"
