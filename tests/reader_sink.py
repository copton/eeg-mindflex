import logging
from typing import Any

from app.framework import (
    Actor,
    ActorInfrastructure,
    ChannelID,
    SubscriberID,
    Eeg,
    Packet,
    Quality,
    Raw,
    Timestamp,
    ActorState,
)

logger = logging.getLogger(__name__)


class ReaderSink(Actor):
    def __init__(self, infra: ActorInfrastructure, wait_for: SubscriberID):
        super().__init__(
            infra,
            name="test_reader_sink",
            channels=[
                infra.packet_channel.id,
                infra.raw_channel.id,
                infra.eeg_channel.id,
                infra.quality_channel.id,
            ],
            capture_thread=False,
            run_to_completion=True,
        )
        self.packets: list[Packet] = []
        self.raw_data: list[Raw] = []
        self.eeg_data: list[Eeg] = []
        self.quality_data: list[Quality] = []
        self._infra = infra
        self._wait_for = wait_for

    def handle(self, channel: ChannelID, timestamp: Timestamp, data: Any) -> None:
        match channel:
            case self._infra.packet_channel.id:
                self.packets.append(data)
            case self._infra.raw_channel.id:
                self.raw_data.append(data)
            case self._infra.eeg_channel.id:
                self.eeg_data.append(data)
            case self._infra.quality_channel.id:
                self.quality_data.append(data)
            case _:
                raise ValueError(f"Unknown channel: {channel}")

    def act(self) -> bool:
        if self._infra.pool.get_state(self._wait_for) != ActorState.COMPLETED:
            return True
        if len(self.packets) < len(self._infra.hub.timeseries(self._infra.packet_channel.id)):
            return True
        if len(self.raw_data) < len(self._infra.hub.timeseries(self._infra.raw_channel.id)):
            return True
        if len(self.eeg_data) < len(self._infra.hub.timeseries(self._infra.eeg_channel.id)):
            return True
        if len(self.quality_data) < len(self._infra.hub.timeseries(self._infra.quality_channel.id)):
            return True
        return False

    def shutdown(self) -> None:
        logger.info("read %d packets", len(self.packets))
