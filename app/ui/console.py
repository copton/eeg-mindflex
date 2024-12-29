from typing import Any, TextIO

from app.framework import Actor, ActorInfrastructure, ChannelID, Timestamp


class Console(Actor):
    def __init__(self, infra: ActorInfrastructure, output: TextIO):
        super().__init__(
            infra,
            name="console",
            channels=[infra.packet_channel.id],
            capture_thread=True,
            run_to_completion=False,
        )
        self._output = output

    def handle(self, channel: ChannelID, timestamp: Timestamp, data: Any) -> None:
        match channel:
            case self._infra.packet_channel.id:
                packet = self._infra.packet_channel.read(data)
                self._output.write(str(timestamp))
                self._output.write(str(packet))
                self._output.write("\n")
