from model import Eeg, bands

SIZE = 10


class Average:
    def __init__(self) -> None:
        self.window: list[Eeg] = []

    def update(self, eeg: Eeg) -> Eeg:
        self.window.append(eeg)

        if len(self.window) < SIZE:
            return Eeg.zero()

        while len(self.window) > SIZE:
            self.window.pop(0)

        res = Eeg.zero()
        for eeg in self.window:
            res = res + eeg

        return res / SIZE
