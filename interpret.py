import sys
from dataclasses import dataclass
from typing import Optional, Generator, Any
import time

MAX_PACKET_LEN = 169


@dataclass(frozen=True)
class Eeg:
    delta: int
    theta: int
    low_alpha: int
    high_alpha: int
    low_beta: int
    high_beta: int
    low_gamma: int
    mid_gamma: int


@dataclass(frozen=True)
class Packet:
    quality: int
    attention: int
    meditation: int
    eeg: Eeg
    raw: Optional[int] = None


class MindFlex:
    """
    https://developer.neurosky.com/docs/doku.php?id=thinkgear_communications_protocol
    """

    def __init__(self, fd):
        self.fd = fd
        self.total = 0

    def read(self) -> Generator[Packet, None, None]:
        prev_byte: str = "c"
        in_packet: bool = False
        packet: list[str] = []
        try:
            while True:
                cur_byte = self.fd.read(1)
                if len(cur_byte) == 0:
                    return None
                self.total += 1

                # If in Mode 1, enable Mode 2
                if not in_packet and ord(prev_byte) == 224 and ord(cur_byte) == 224:
                    raise ValueError("device is in Mode 1")

                # Look for the start of the packet
                if not in_packet and ord(prev_byte) == 170 and ord(cur_byte) == 170:
                    in_packet = True
                    packet = []
                    continue

                if in_packet:
                    if len(packet) == 0:
                        if ord(cur_byte) == 170:
                            continue
                        packet_len = ord(cur_byte)
                        if packet_len >= MAX_PACKET_LEN:
                            raise ValueError("Packet too long: %s" % packet_len)
                        checksum_total = 0
                        packet = [cur_byte]
                    elif len(packet) - 1 == packet_len:
                        packet_checksum = ord(cur_byte)
                        in_packet = False
                        if (~(checksum_total & 255) & 255) == packet_checksum:
                            if packet_len > 4:
                                yield self.parser(packet)
                        else:
                            print(~(checksum_total & 255) & 255)
                            print(packet_checksum)
                            print(packet)
                            raise ValueError("Warning: invalid checksum")
                    else:
                        checksum_total += ord(cur_byte)
                        packet.append(cur_byte)

                # keep track of last byte to catch sync bytes
                prev_byte = cur_byte

        except KeyboardInterrupt as e:
            return

    def parser(self, packet: list[str]) -> Packet:
        # See the MindSet Communications Protocol
        quality: Optional[int] = None
        attention: Optional[int] = None
        meditation: Optional[int] = None
        eeg: list[int] = []
        raw: Optional[int] = None

        # The first byte in the list was packet_len, so start at i = 1
        i = 1
        while i < len(packet) - 1:
            code_level = ord(packet[i])
            # signal quality
            if code_level == 0x02:
                quality = ord(packet[i + 1])
                i += 2
            # attention
            elif code_level == 0x04:
                attention = ord(packet[i + 1])
                i += 2
            # meditation
            elif code_level == 0x05:
                meditation = ord(packet[i + 1])
                i += 2
            # EEG power
            elif code_level == 0x83:
                for c in range(i + 1, i + 25, 3):
                    eeg.append(
                        ord(packet[c]) << 16
                        | ord(packet[c + 1]) << 8
                        | ord(packet[c + 2])
                    )
                i += 26
            # Raw Wave Value
            elif code_level == 0x80:
                raw = ord(packet[i + 1]) << 8 | ord(packet[i + 2])
                i += 4

        if quality is None:
            raise ValueError("quality is None")
        if attention is None:
            raise ValueError("attention is None")
        if meditation is None:
            raise ValueError("meditation is None")
        if len(eeg) != 8:
            raise ValueError(f"invalid eeg readings: {len(eeg)}")

        return Packet(
            quality=quality,
            attention=attention,
            meditation=meditation,
            eeg=Eeg(
                delta=eeg[0],
                theta=eeg[1],
                low_alpha=eeg[2],
                high_alpha=eeg[3],
                low_beta=eeg[4],
                high_beta=eeg[5],
                low_gamma=eeg[6],
                mid_gamma=eeg[7],
            ),
            raw=raw,
        )


def replay(file: str, delay: Optional[float] = None) -> Generator[Packet, None, None]:
    with open(file, "br") as fd:
        connection = MindFlex(fd)
        for packet in connection.read():
            yield packet
            if delay is not None:
                time.sleep(delay)

        print(f"interpreted {connection.total} bytes")


if __name__ == "__main__":
    for packet in replay(sys.argv[1]):
        print(packet)
