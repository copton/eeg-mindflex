from dataclasses import dataclass, fields

import numpy as np


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

    def as_vector(self) -> np.ndarray:
        return np.array([getattr(self, band) for band in bands()])

    @classmethod
    def from_vector(cls, arr: np.ndarray) -> "Eeg":
        bs = bands()
        if len(bs) != len(arr):
            raise ValueError(f"length mismatch, {len(bs)} vs. {len(arr)}")
        return Eeg(**{band: int(value) for band, value in zip(bs, arr)})

    @classmethod
    def zero(cls) -> "Eeg":
        return cls.from_vector(np.zeros(len(bands())))


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
