import logging
from collections import defaultdict
from typing import Any, TextIO

from rich.console import Console as RichConsole
from rich.live import Live
from rich.table import Table

from app.framework import Actor, ActorInfrastructure, ChannelID, Timestamp, bands

logger = logging.getLogger(__name__)


class Console(Actor):
    def __init__(self, infra: ActorInfrastructure, output: TextIO):
        super().__init__(
            infra,
            name="console",
            channels=[
                infra.raw_channel.id,
                infra.quality_channel.id,
                infra.median_eeg_channel.id,
            ],
            capture_thread=True,
            run_to_completion=False,
        )
        self._output = output
        self._latest_values: dict[str, Any] = defaultdict(lambda: "N/A")
        self._rich_console = RichConsole(file=output)

    def setup(self) -> None:
        with Live(self._generate_table(), refresh_per_second=4) as live:
            self._live = live
            self.run()

    def _generate_table(self) -> Table:
        table = Table(title="EEG Signal Monitor")
        table.add_column("Signal Type")
        table.add_column("Value", width=20)
        table.add_column("Timestamp")

        # Add rows with latest values
        table.add_row(
            "raw signal", str(self._latest_values["raw"]), format_time(self._latest_values["raw_time"])
        )
        table.add_row(
            "signal quality",
            str(self._latest_values["quality"]),
            format_time(self._latest_values["quality_time"]),
        )

        for band in bands():
            table.add_row(
                f"{band.replace('_', ' ')}",
                str(self._latest_values[f"median_{band}"]),
                format_time(self._latest_values[f"median_time_{band}"]),
            )

        return table

    def handle(self, channel: ChannelID, timestamp: Timestamp, data: Any) -> None:
        match channel:
            case self._infra.raw_channel.id:
                raw = self._infra.raw_channel.read(data)
                self._latest_values["raw"] = raw
                self._latest_values["raw_time"] = timestamp
            case self._infra.quality_channel.id:
                quality = self._infra.quality_channel.read(data)
                self._latest_values["quality"] = quality
                self._latest_values["quality_time"] = timestamp
            case self._infra.median_eeg_channel.id:
                median = self._infra.median_eeg_channel.read(data)
                for band in bands():
                    self._latest_values[f"median_{band}"] = getattr(median, band)
                    self._latest_values[f"median_time_{band}"] = timestamp

        # Update the live display
        self._live.update(self._generate_table())

    def __del__(self):
        # Ensure we stop the live display when the object is destroyed
        if hasattr(self, "_live"):
            self._live.stop()


def format_time(timestamp: str | Timestamp) -> str:
    if isinstance(timestamp, str):
        return timestamp
    return f"{timestamp:.2f}"
