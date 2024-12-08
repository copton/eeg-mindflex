import sys
from queue import Queue

import numpy as np
import pyqtgraph as pg  # type: ignore
from PySide6.QtCore import QTimer  # type: ignore
from PySide6.QtWidgets import (  # type: ignore
    QApplication,
    QVBoxLayout,
    QWidget,
)

from model import Eeg, Raw, bands

color_palette = [
    (255, 0, 0),  # Red
    (0, 255, 0),  # Green
    (0, 0, 255),  # Blue
    (255, 255, 0),  # Yellow
    (255, 165, 0),  # Orange
    (75, 0, 130),  # Indigo
    (238, 130, 238),  # Violet
    (0, 255, 255),  # Cyan
]


class RawPlotWindow(QWidget):
    def __init__(self, raw_data: Queue[tuple[float, Raw]]):
        super().__init__()

        self.raw_data: Queue[tuple[float, Raw]] = raw_data

        self.setWindowTitle("raw data")
        self.plot_widget = pg.PlotWidget()
        layout = QVBoxLayout()
        layout.addWidget(self.plot_widget)
        self.setLayout(layout)
        self.plot_widget.addLegend()
        self.plot_widget.setYRange(-500, 500)

        self.plot = self.plot_widget.plot(
            pen=pg.mkPen(
                color=(255, 255, 255),
                width=1,
            ),
            name="raw",
        )

        self.plot_data = np.zeros(10_000)

    def on_timer(self):
        while not self.raw_data.empty():
            delay, packet = self.raw_data.get()
            self.plot_data = np.roll(self.plot_data, -1)
            self.plot_data[-1] = packet.value
            self.plot.setData(self.plot_data)


class EegPlotWindow(QWidget):
    def __init__(self, eeg_data: Queue[tuple[float, Eeg]]):
        super().__init__()

        self.eeg_data: Queue[tuple[float, Eeg]] = eeg_data

        self.setWindowTitle("eeg data")
        self.plot_widget = pg.PlotWidget()
        layout = QVBoxLayout()
        layout.addWidget(self.plot_widget)
        self.setLayout(layout)
        self.plot_widget.addLegend()

        self.plots = {
            band: self.plot_widget.plot(
                pen=pg.mkPen(
                    color=color_palette[i],
                    width=1,
                ),
                name=band,
            )
            for i, band in enumerate(bands())
        }

        self.plot_data = {band: np.zeros(100) for band in bands()}

    def on_timer(self):
        while not self.eeg_data.empty():
            delay, eeg = self.eeg_data.get()
            for band in bands():
                value = getattr(eeg, band)
                self.plot_data[band] = np.roll(self.plot_data[band], -1)
                self.plot_data[band][-1] = value
                self.plots[band].setData(self.plot_data[band])


class Gui:
    def __init__(self, eeg_data: Queue, raw_data: Queue) -> None:
        self.app = QApplication(sys.argv)

        self.eeg_window = EegPlotWindow(eeg_data)
        self.eeg_window.resize(1024, 768)
        self.eeg_window.show()

        self.raw_window = RawPlotWindow(raw_data)
        self.raw_window.resize(800, 600)
        self.raw_window.show()

        self.timer = QTimer()
        self.timer.timeout.connect(self.on_timer)
        self.timer.start(50)

    def on_timer(self):
        try:
            self.eeg_window.on_timer()
            self.raw_window.on_timer()
        except KeyboardInterrupt:
            self.quit()

    def run(self):
        self.app.exec()

    def quit(self):
        if QApplication.instance() is not None:
            QApplication.quit()