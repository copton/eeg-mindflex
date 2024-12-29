from dataclasses import dataclass, fields, asdict
from typing import Any


def bands() -> list[str]:
    return [f.name for f in fields(Eeg)]


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

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Eeg":
        return cls(**data)


Quality = int


@dataclass(frozen=True)
class Aggregated:
    quality: Quality
    attention: int
    meditation: int
    eeg: Eeg

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Aggregated":
        return cls(
            quality=data["quality"],
            attention=data["attention"],
            meditation=data["meditation"],
            eeg=Eeg.from_dict(data["eeg"]),
        )


@dataclass(frozen=True)
class Raw:
    value: int

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Raw":
        return cls(value=data["value"])


Packet = Raw | Aggregated


def packet_to_dict(packet: Packet) -> dict[str, Any]:
    return {"type": packet.__class__.__name__, "data": asdict(packet)}


def packet_from_dict(data: dict[str, Any]) -> Packet:
    packet_type = data["type"]
    packet_data = data["data"]

    if packet_type == "Raw":
        return Raw.from_dict(packet_data)
    elif packet_type == "Aggregated":
        return Aggregated.from_dict(packet_data)
    else:
        raise ValueError(f"Unknown packet type: {packet_type}")


@dataclass(frozen=True)
class MedianEeg(Eeg):
    pass
