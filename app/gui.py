import sys
import time
from queue import Queue
from threading import Thread

import numpy as np
import pyqtgraph as pg
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import (
    QApplication,
    QColorDialog,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from model import Aggregated, Packet, Raw


class MyApp(QMainWindow):
    def __init__(self, sensor_data: Queue):
        super().__init__()
        self.sensor_data = sensor_data
        self.start = None
        self.bands = (
            "delta",
            "theta",
            "low_alpha",
            "high_alpha",
            "low_beta",
            "high_beta",
            "low_gamma",
            "mid_gamma",
        )

        self.setWindowTitle("Real-Time Sensor Data Plotter")

        # Main widget and layout
        self.main_widget = QWidget()
        self.setCentralWidget(self.main_widget)
        self.layout = QVBoxLayout(self.main_widget)

        # Plot widget and configuration buttons
        self.plot_widget = pg.GraphicsLayoutWidget()
        self.layout.addWidget(self.plot_widget)
        self.config_layout = QHBoxLayout()
        self.layout.addLayout(self.config_layout)

        # Add plots
        self.sensor1_plot = self.plot_widget.addPlot(title="EEG")
        self.sensor2_plot = self.plot_widget.addPlot(
            title="Sensor 2 (Single Time Series)"
        )
        self.plot_widget.nextRow()

        # Initialize line objects
        self.sensor1_lines = {
            band: self.sensor1_plot.plot(
                pen=pg.mkPen(color=(i * 50, 200, 255 - i * 50), width=2)
            )
            for i, band in enumerate(self.bands)
        }
        self.sensor2_line = self.sensor2_plot.plot(
            pen=pg.mkPen(color=(255, 0, 0), width=2)
        )

        self.sensor1_data = {band: np.zeros(100) for band in self.bands}
        self.sensor2_data = np.zeros(100)
        self.time = np.arange(100)

        # Timer for real-time updates
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_plots)
        self.timer.start(50)  # Update every 50ms

    def update_plots(self):
        if self.start is None:
            self.start = time.time()

        while not self.sensor_data.empty():
            delay, packet = self.sensor_data.get()
            if isinstance(packet, Raw):
                self.update_raw_plot(delay, packet)
            else:
                self.update_eeg_plot(delay, packet)

    def update_raw_plot(self, delay: float, packet: Raw):
        self.sensor2_data = np.roll(self.sensor2_data, -1)
        self.sensor2_data[-1] = packet.value
        self.sensor2_line.setData(self.time, self.sensor2_data)

    def update_eeg_plot(self, delay: float, packet: Aggregated):
        for band in self.bands:
            self.sensor1_data[band] = np.roll(self.sensor1_data[band], -1)
            self.sensor1_data[band][-1] = getattr(packet.eeg, band)
            self.sensor1_lines[band].setData(self.time, self.sensor1_data[band])


class Gui:
    def __init__(self, sensor_data: Queue) -> None:
        self.app = QApplication(sys.argv)
        self.window = MyApp(sensor_data)
        self.window.resize(800, 600)
        self.window.show()

    def run(self):
        self.app.exec()

    def quit(self):
        QApplication.quit()
