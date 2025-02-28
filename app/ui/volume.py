from typing import Any

from app.framework import Actor, ActorInfrastructure, ChannelID, MedianEeg, Timestamp
from app.system import OsOperations


class VolumeControl(Actor):
    def __init__(self, infra: ActorInfrastructure, os_operations: OsOperations):
        super().__init__(
            infra,
            name="volume_control",
            channels=[infra.median_eeg_channel.id],
            capture_thread=False,
            run_to_completion=False,
        )
        self._os_operations = os_operations

    def handle(self, channel: ChannelID, timestamp: Timestamp, data: Any) -> None:
        match channel:
            case self._infra.median_eeg_channel.id:
                median_eeg = self._infra.median_eeg_channel.read(data)
                self.set_volume(median_eeg)

    def set_volume(self, data: MedianEeg) -> None:
        if data.high_alpha > 10_000 or data.low_alpha > 10_000:
            self._os_operations.set_volume(0.4)
        else:
            self._os_operations.set_volume(0.15)
