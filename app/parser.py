"""
https://developer.neurosky.com/docs/doku.php?id=thinkgear_communications_protocol
"""

from typing import Generator, Optional
import struct

from model import Aggregated, Eeg, Packet, Raw

MAX_PACKET_LEN = 169


def parse(input: Generator[int, None, None]) -> Generator[Packet, None, None]:
    prev_byte: int = ord("c")
    in_packet: bool = False
    packet: list[int] = []
    while True:
        cur_byte = next(input)

        # If in Mode 1, enable Mode 2
        if not in_packet and prev_byte == 224 and cur_byte == 224:
            raise ValueError("device is in Mode 1")

        # Look for the start of the packet
        if not in_packet and prev_byte == 170 and cur_byte == 170:
            in_packet = True
            packet = []
            continue

        if in_packet:
            if len(packet) == 0:
                if cur_byte == 170:
                    continue
                packet_len = cur_byte
                if packet_len >= MAX_PACKET_LEN:
                    raise ValueError("Packet too long: %s" % packet_len)
                checksum_total = 0
                packet = [cur_byte]
            elif len(packet) - 1 == packet_len:
                packet_checksum = cur_byte
                in_packet = False
                if (~(checksum_total & 255) & 255) == packet_checksum:
                    if packet_len > 4:
                        yield aggregated_parser(packet)
                    else:
                        yield raw_parser(packet)
                else:
                    print("Warning: invalid checksum")
            else:
                checksum_total += cur_byte
                packet.append(cur_byte)

        # keep track of last byte to catch sync bytes
        prev_byte = cur_byte


def raw_parser(packet: list[int]) -> Raw:
    code_level = packet[1]
    if code_level != 0x80:
        raise ValueError(f"raw packet with unexpected code '{code_level}`")

    vlength = packet[2]
    if vlength != 2:
        raise ValueError(f"raw packet with unexpected vlength '{vlength}`")

    value = (packet[3] << 8) | packet[4]

    # Check if the sign bit is set
    if value & 0x8000:
        value -= 0x10000

    return Raw(value=value)


def aggregated_parser(packet: list[int]) -> Aggregated:
    quality: Optional[int] = None
    attention: Optional[int] = None
    meditation: Optional[int] = None
    eeg: list[int] = []

    # The first byte in the list was packet_len, so start at i = 1
    i = 1
    while i < len(packet) - 1:
        code_level = packet[i]
        # signal quality
        if code_level == 0x02:
            quality = packet[i + 1]
            i += 2
        # attention
        elif code_level == 0x04:
            attention = packet[i + 1]
            i += 2
        # meditation
        elif code_level == 0x05:
            meditation = packet[i + 1]
            i += 2
        # EEG power
        elif code_level == 0x83:
            for c in range(i + 1, i + 25, 3):
                eeg.append(packet[c] << 16 | packet[c + 1] << 8 | packet[c + 2])
            i += 26
        # Raw Wave Value
        else:
            raise ValueError(f"unexpected code '{code_level}'")

    if quality is None:
        raise ValueError("quality is None")
    if attention is None:
        raise ValueError("attention is None")
    if meditation is None:
        raise ValueError("meditation is None")
    if len(eeg) != 8:
        raise ValueError(f"invalid eeg readings: {len(eeg)}")

    return Aggregated(
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
    )
