import logging
from typing import Any

from app.framework import Actor, ActorInfrastructure, ChannelID, MedianEeg, Timestamp
from app.system import OsOperations

logger = logging.getLogger(__name__)

HIGH_VOLUME = 0.4
LOW_VOLUME = 0.15


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
        self._volume: None | float = None

    def handle(self, channel: ChannelID, timestamp: Timestamp, data: Any) -> None:
        match channel:
            case self._infra.median_eeg_channel.id:
                median_eeg = self._infra.median_eeg_channel.read(data)
                self.set_volume(median_eeg)

    def set_volume(self, data: MedianEeg) -> None:
        if data.high_alpha > 10_000 or data.low_alpha > 10_000:
            target_volume = HIGH_VOLUME
        else:
            target_volume = LOW_VOLUME

        if self._volume != target_volume:
            logger.debug(f"Setting volume from {self._volume} to {target_volume}")
            self._os_operations.set_volume(target_volume)
            self._volume = target_volume
