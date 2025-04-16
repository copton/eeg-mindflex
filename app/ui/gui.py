import logging
from typing import Any

from app.framework import Actor, ActorInfrastructure, ChannelID, Timestamp

logger = logging.getLogger(__name__)


class GUI(Actor):
    def __init__(self, infra: ActorInfrastructure) -> None:
        super().__init__(
            infra,
            name="gui",
            channels=[
                infra.raw_channel.id,
                infra.quality_channel.id,
                infra.median_eeg_channel.id,
            ],
            capture_thread=True,
            run_to_completion=False,
        )
        self.infra = infra

    def setup(self) -> bool:
        self.run() 

    def act(self) -> bool:
        raw_data = self.infra.hub.timeseries(self.infra.raw_channel.id, number_of_points=100)
        quality_data = self.infra.hub.timeseries(self.infra.quality_channel.id, number_of_points=100)
        median_eeg_data = self.infra.hub.timeseries(self.infra.median_eeg_channel.id, number_of_points=100)

        logger.info(f"Raw data: {raw_data}")
        logger.info(f"Quality data: {quality_data}")
        logger.info(f"Median EEG data: {median_eeg_data}")

        return True

    def handle(self, channel: ChannelID, timestamp: Timestamp, data: Any) -> None:
        match channel:
            case self._infra.raw_channel.id:
                logger.info(f"Raw data: {data}")
            case self._infra.quality_channel.id:
                logger.info(f"Quality data: {data}")
            case self._infra.median_eeg_channel.id:
                logger.info(f"Median EEG data: {data}")

