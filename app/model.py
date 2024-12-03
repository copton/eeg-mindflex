from dataclasses import dataclass


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
class Aggregated:
    quality: int
    attention: int
    meditation: int
    eeg: Eeg


@dataclass(frozen=True)
class Raw:
    value: int


Packet = Raw | Aggregated
