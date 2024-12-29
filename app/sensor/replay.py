from pathlib import Path
import json
import logging
from app.framework import Actor, ActorInfrastructure, Raw, Aggregated, packet_from_dict

logger = logging.getLogger(__name__)


class Replay(Actor):
    def __init__(self, infra: ActorInfrastructure, recording: Path):
        super().__init__(
            infra,
            name="replay",
            channels=[],
            capture_thread=False,
            run_to_completion=False,
        )
        self._recording = recording
        self._count = 0

    def setup(self) -> None:
        with open(self._recording, "r") as fd:
            self._records = json.load(fd)
            self.run()

    def act(self) -> bool:
        if self._count >= len(self._records):
            return False

        record = self._records[self._count]
        self._count += 1
        timestamp = record["timestamp"]
        packet = packet_from_dict(record["packet"])
        # self._infra.timer.catchup(timestamp)

        self._infra.hub.publish(self._infra.packet_channel.id, packet)
        match packet:
            case Raw():
                self._infra.hub.publish(self._infra.raw_channel.id, packet)
            case Aggregated():
                self._infra.hub.publish(self._infra.eeg_channel.id, packet.eeg)
                self._infra.hub.publish(self._infra.quality_channel.id, packet.quality)

        return True

    def shutdown(self) -> None:
        logger.info("replayed %d packets", self._count)
