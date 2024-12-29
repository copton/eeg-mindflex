import numpy as np
import pyqtgraph as pg  # type: ignore
from PySide6.QtCore import QTimer, Signal, Slot  # type: ignore
from PySide6.QtWidgets import QApplication, QPushButton, QVBoxLayout, QWidget  # type: ignore

from app.framework import Actor, ActorInfrastructure, bands

color_palette = [
    (255, 0, 0),  # Red
    (0, 255, 0),  # Green
    (0, 0, 255),  # Blue
    (255, 255, 0),  # Yellow
    (255, 165, 0),  # Orange
    (75, 0, 130),  # Indigo
    (255, 255, 255),  # White
    (0, 255, 255),  # Cyan
]


class RawPlotWindow(QWidget):
    def __init__(self, infra: ActorInfrastructure):
        super().__init__()
        self._infra = infra

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
        pass
        # TODO: Implement this
        # while not self.raw_data.empty():
        #     delay, packet = self.raw_data.get()
        #     self.plot_data = np.roll(self.plot_data, -1)
        #     self.plot_data[-1] = packet.value
        #     self.plot.setData(self.plot_data)


class EegPlotWindow(QWidget):
    def __init__(self, infra: ActorInfrastructure):
        super().__init__()
        self._infra = infra

        self.setWindowTitle("eeg data")
        self.plot_widget = pg.PlotWidget()
        layout = QVBoxLayout()
        layout.addWidget(self.plot_widget)
        self.setLayout(layout)
        self.plot_widget.addLegend()

        # Add second y-axis on the right side
        self.second_axis = pg.ViewBox()
        self.plot_widget.scene().addItem(self.second_axis)
        self.plot_widget.getAxis("right").linkToView(self.second_axis)
        self.second_axis.setXLink(self.plot_widget.getViewBox())

        # Show the right axis
        self.plot_widget.showAxis("right")

        self.plots = {}
        for i, band in enumerate(bands()):
            pen = pg.mkPen(
                color=color_palette[i],
                width=2,
            )

            if band in ("high_beta", "low_beta"):
                # Create plot linked to right axis for beta bands
                plot = pg.PlotDataItem(
                    pen=pen,
                    name=band,
                )
                self.second_axis.addItem(plot)
                self.plots[band] = plot
            else:
                # Create normal plot for other bands
                self.plots[band] = self.plot_widget.plot(
                    pen=pen,
                    name=band,
                )

        self.plot_data = {band: np.zeros(1000) for band in bands()}

    def on_timer(self):
        pass
        # TODO: Implement this
        # while not self.eeg_data.empty():
        #     delay, eeg = self.eeg_data.get()
        #     for band in bands():
        #         value = getattr(eeg, band)
        #         self.plot_data[band] = np.roll(self.plot_data[band], -1)
        #         self.plot_data[band][-1] = value
        #         self.plots[band].setData(self.plot_data[band])


class ControlWindow(QWidget):
    clear_graph_triggered = Signal()

    def __init__(self, infra: ActorInfrastructure):
        super().__init__()
        self._infra = infra

        self.layout_box = QVBoxLayout(self)
        self.button = QPushButton("clear graph")
        self.layout_box.addWidget(self.button)

        self.button.clicked.connect(self.trigger_custom_action)

    @Slot()
    def trigger_custom_action(self):
        self.clear_graph_triggered.emit()


class GUI(Actor):
    def __init__(self, infra: ActorInfrastructure) -> None:
        super().__init__(
            infra,
            name="gui",
            channels=[infra.packet_channel.id],
            capture_thread=True,
            run_to_completion=False,
        )

    def act(self) -> bool:
        self.app = QApplication()

        self.eeg_window = EegPlotWindow(self._infra)
        self.eeg_window.resize(1024, 768)
        self.eeg_window.show()

        self.raw_window = RawPlotWindow(self._infra)
        self.raw_window.resize(800, 600)
        self.raw_window.show()

        self.control_window = ControlWindow(self._infra)
        self.control_window.show()
        # TODO: Implement this
        # self.control_window.clear_graph_triggered.connect(self.eeg_window.on_clear_graph)

        self.timer = QTimer()
        self.timer.timeout.connect(self.on_timer)
        self.timer.start(50)

        self.app.exec()
        return False

    def on_timer(self):
        try:
            self.eeg_window.on_timer()
            self.raw_window.on_timer()
        except KeyboardInterrupt:
            self.quit()

    def quit(self):
        if QApplication.instance() is not None:
            QApplication.quit()
