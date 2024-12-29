import logging
import time
from pathlib import Path

import serial  # type: ignore

from app.framework import Actor, ActorInfrastructure, Aggregated, Raw

from .parser import Parser

logger = logging.getLogger(__name__)

BAUD_RATE = 57600


def make_reader(infra: ActorInfrastructure, port: Path) -> Actor:
    if port.parts[0] == "dev":
        return SensorReaderFromDevice(infra, port)
    else:
        return SensorReaderFromFile(infra, port)


class _SensorReader(Actor):
    def __init__(self, infra: ActorInfrastructure):
        super().__init__(
            infra,
            name="sensor-reader",
            channels=[],
            capture_thread=False,
            run_to_completion=False,
        )
        self._parser = Parser()
        self._count = 0

    def process(self, data: bytes) -> None:
        result = self._parser(data)
        if result is None:
            return None
        rest, packet = result

        self._infra.hub.publish(self._infra.packet_channel.id, packet)
        self._count += 1
        match packet:
            case Raw():
                self._infra.hub.publish(self._infra.raw_channel.id, packet)
            case Aggregated():
                self._infra.hub.publish(self._infra.eeg_channel.id, packet.eeg)
                self._infra.hub.publish(self._infra.quality_channel.id, packet.quality)

        self.process(rest)

    def shutdown(self) -> None:
        logger.info("read %d packets", self._count)


class SensorReaderFromFile(_SensorReader):
    def __init__(self, infra: ActorInfrastructure, filename: Path):
        super().__init__(infra)
        self._filename = filename

    def setup(self) -> None:
        with open(self._filename, "br") as fd:
            logger.info("reading binary data from file '%s'", self._filename)
            self._fd = fd
            self.run()

    def act(self) -> bool:
        data = self._fd.read(128)
        if not data:
            return False

        self.process(data)
        return True


class SensorReaderFromDevice(_SensorReader):
    def __init__(self, infra: ActorInfrastructure, port: Path):
        super().__init__(infra)
        self._port = port
        self._parser = Parser()

    def setup(self) -> None:
        with serial.Serial(
            self._port,
            BAUD_RATE,
            timeout=1,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            bytesize=serial.EIGHTBITS,
        ) as ser:
            logger.info(
                "reading binary data from device '%s' at '%s' symbols per second",
                self._port,
                BAUD_RATE,
            )
            self._ser = ser
            self.run()

    def act(self) -> bool:
        if self._ser.in_waiting <= 0:
            time.sleep(0)
            return True

        data = self._ser.read(64)
        self.process(data)
        return True
