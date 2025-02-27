import json
import logging
from pathlib import Path
from typing import Any

from app.framework import (
    Actor,
    ActorInfrastructure,
    ActorState,
    ChannelID,
    SubscriberID,
    Timestamp,
    packet_to_dict,
)

logger = logging.getLogger(__name__)


class Recorder(Actor):
    def __init__(self, infra: ActorInfrastructure, recording: Path, wait_for: SubscriberID | None):
        super().__init__(
            infra,
            name="recorder",
            channels=[infra.packet_channel.id],
            capture_thread=False,
            run_to_completion=wait_for is not None,
        )
        self._recording = recording
        self._count = 0
        self._wait_for = wait_for

    def setup(self) -> None:
        with open(self._recording, "w") as fd:
            self._fd = fd
            self._fd.write("[\n")
            self.run()
            self._fd.write("]\n")

    def handle(self, channel: ChannelID, timestamp: Timestamp, data: Any) -> None:
        match channel:
            case self._infra.packet_channel.id:
                packet = self._infra.packet_channel.read(data)
                record = {"timestamp": timestamp, "packet": packet_to_dict(packet)}
                if self._count > 0:
                    self._fd.write(",\n")
                self._fd.write(json.dumps(record))
                self._count += 1
            case _:
                raise ValueError(f"don't know how to handle data from channel {channel}")

    def act(self) -> bool:
        if self._wait_for is not None:
            if self._infra.pool.get_state(self._wait_for) != ActorState.COMPLETED:
                return True

        if self._count < len(self._infra.hub.timeseries(self._infra.packet_channel.id)):
            return True

        return False

    def shutdown(self) -> None:
        logger.info("recorded %d packets", self._count)
