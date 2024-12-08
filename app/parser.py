"""
https://developer.neurosky.com/docs/doku.php?id=thinkgear_communications_protocol
"""

from typing import Generator, Optional
import logging

from model import Aggregated, Eeg, Packet, Raw

logger = logging.getLogger(__name__)

MAX_PACKET_LEN = 169


def parse(input: Generator[int, None, None]) -> Generator[Packet, None, None]:
    prev_byte: int = ord("c")
    in_packet: bool = False
    payload: Optional[list[int]] = None
    packet: Optional[Packet] = None

    while True:
        try:
            cur_byte = next(input)
        except StopIteration:
            return

        if not in_packet and prev_byte == 0xAA and cur_byte == 0xAA:
            in_packet = True
            payload = None
            continue

        if in_packet:
            if payload is None:
                if cur_byte == 0xAA:
                    continue
                packet_len = cur_byte
                if packet_len >= MAX_PACKET_LEN:
                    logger.warning("Packet too long: %d", packet_len)
                    continue
                checksum_total = 0
                payload = []

            elif len(payload) == packet_len:
                packet_checksum = cur_byte
                in_packet = False
                if (~(checksum_total & 0xFF) & 0xFF) != packet_checksum:
                    logger.warning("invalid checksum")
                    continue

                if packet_len > 4:
                    packet = aggregated_parser(payload)
                else:
                    packet = raw_parser(payload)
                if packet is not None:
                    yield packet
            else:
                checksum_total += cur_byte
                payload.append(cur_byte)

        # keep track of last byte to catch sync bytes
        prev_byte = cur_byte


def raw_parser(payload: list[int]) -> Optional[Raw]:
    code_level = payload[0]
    if code_level != 0x80:
        logger.warning("raw packet with unexpected code %d", code_level)
        return None

    vlength = payload[1]
    if vlength != 2:
        logger.warning("raw packet with unexpected vlength %d", vlength)
        return None

    value = (payload[2] << 8) | payload[3]

    # Check if the sign bit is set
    if value & 0x8000:
        value -= 0x10000

    return Raw(value=value)


def aggregated_parser(payload: list[int]) -> Optional[Aggregated]:
    quality: Optional[int] = None
    attention: Optional[int] = None
    meditation: Optional[int] = None
    eeg: list[int] = []

    i = 0
    while i < len(payload):
        code_level = payload[i]
        # signal quality
        if code_level == 0x02:
            quality = payload[i + 1]
            i += 2
        # attention
        elif code_level == 0x04:
            attention = payload[i + 1]
            i += 2
        # meditation
        elif code_level == 0x05:
            meditation = payload[i + 1]
            i += 2
        # EEG power
        elif code_level == 0x83:
            i += 1
            vlength = payload[i]
            if vlength != 24:
                logger.warning("unexpected vlength %d", vlength)
                return None
            i += 1
            for c in range(i, i + vlength, 3):
                eeg.append(payload[c] << 16 | payload[c + 1] << 8 | payload[c + 2])
            i += vlength
        else:
            logger.warning("unexpected code %d'", code_level)
            return None

    if quality is None:
        logger.warning("quality is None")
        return None
    if attention is None:
        logger.warning("attention is None")
        return None
    if meditation is None:
        logger.warning("meditation is None")
        return None
    if len(eeg) != 8:
        logger.warning("invalid eeg readings: %d", len(eeg))
        return None

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
