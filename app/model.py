from dataclasses import dataclass, fields


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

    def __add__(self, other: "Eeg") -> "Eeg":
        if not isinstance(other, Eeg):
            raise TypeError(f"Cannot add {type(other)} to Eeg")

        return Eeg(
            **{
                field.name: getattr(self, field.name) + getattr(other, field.name)
                for field in fields(self)
            }
        )

    def __truediv__(self, other):
        return Eeg(
            **{field.name: getattr(self, field.name) / other for field in fields(self)}
        )

    @classmethod
    def zero(cls):
        return cls(**{field.name: 0 for field in fields(cls)})


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
