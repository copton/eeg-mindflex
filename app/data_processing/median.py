import logging
from typing import Any

import numpy as np

from app.framework import Actor, ActorInfrastructure, ChannelID, MedianEeg, Timestamp, bands

logger = logging.getLogger(__name__)

WINDOW_SIZE = 60


class Median(Actor):
    def __init__(self, infra: ActorInfrastructure) -> None:
        super().__init__(
            infra,
            name="median",
            channels=[infra.eeg_channel.id],
            capture_thread=False,
            run_to_completion=False,
        )
        self.values = np.empty((0, len(bands())))

    def handle(self, channel: ChannelID, timestamp: Timestamp, data: Any) -> None:
        match channel:
            case self._infra.eeg_channel.id:
                eeg = self._infra.eeg_channel.read(data)

            case _:
                raise ValueError(f"don't know how to handle data from channel {channel}")

        eeg_values = np.array([[getattr(eeg, band) for band in bands()]])
        self.values = np.vstack((self.values, eeg_values))

        if len(self.values) < WINDOW_SIZE:
            median_eeg = MedianEeg(**{band: 0 for band in bands()})
            logger.debug(f"{len(self.values)} values in window")
        else:
            median_vector = np.median(self.values, axis=0)
            median_eeg = MedianEeg(*list(median_vector))
            self.values = np.delete(self.values, 0, axis=0)


        self._infra.hub.publish(self._infra.median_eeg_channel.id, median_eeg)
