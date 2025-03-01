from typing import Any

from app.framework import ActorInfrastructure, Channel, ChannelID, MedianEeg, Timestamp
from app.system import OsOperations
from app.ui import VolumeControl


class VolumeControlSink(VolumeControl):
    def __init__(self, count: int, infra: ActorInfrastructure, os_operations: OsOperations):
        super().__init__(infra, os_operations)
        self.count = count

    def act(self) -> bool:
        return self.count > 0

    def handle(self, channel: ChannelID, timestamp: Timestamp, data: Any) -> None:
        self.count -= 1
        super().handle(channel, timestamp, data)


def test_volume_control(infra: ActorInfrastructure, mocker) -> None:
    os_operations = mocker.Mock()
    os_operations.set_volume = mocker.Mock()
    infra.median_eeg_channel = Channel("median_eeg", infra.hub)
    events = [
        MedianEeg(
            delta=1,
            theta=1,
            low_alpha=1,
            high_alpha=1,
            low_beta=1,
            high_beta=1,
            low_gamma=1,
            mid_gamma=1,
        ),
        MedianEeg(
            delta=1,
            theta=1,
            low_alpha=10_001,
            high_alpha=1,
            low_beta=1,
            high_beta=1,
            low_gamma=1,
            mid_gamma=1,
        ),
        MedianEeg(
            delta=1,
            theta=1,
            low_alpha=1,
            high_alpha=1,
            low_beta=1,
            high_beta=1,
            low_gamma=1,
            mid_gamma=1,
        ),
        MedianEeg(
            delta=1,
            theta=1,
            low_alpha=1,
            high_alpha=1,
            low_beta=1,
            high_beta=1,
            low_gamma=1,
            mid_gamma=1,
        ),
        MedianEeg(
            delta=1,
            theta=1,
            low_alpha=1,
            high_alpha=10_001,
            low_beta=1,
            high_beta=1,
            low_gamma=1,
            mid_gamma=1,
        ),
        MedianEeg(
            delta=1,
            theta=1,
            low_alpha=1,
            high_alpha=1,
            low_beta=1,
            high_beta=1,
            low_gamma=1,
            mid_gamma=1,
        ),
    ]
    VolumeControlSink(len(events), infra, os_operations)
    infra.pool.start()
    for event in events:
        infra.hub.publish(infra.median_eeg_channel.id, event)

    infra.pool.wait()
    infra.pool.stop()

    os_operations.set_volume.assert_has_calls(
        [
            mocker.call(0.15),
            mocker.call(0.4),
            mocker.call(0.15),
            mocker.call(0.4),
            mocker.call(0.15),
        ],
    )
