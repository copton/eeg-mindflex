import logging
from collections import deque
from time import time

from PySide6.QtCharts import QChart, QChartView, QLineSeries, QValueAxis
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QPainter
from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget

from app.framework import Actor, ActorInfrastructure

logger = logging.getLogger(__name__)

class MainWindow(QMainWindow):
    def __init__(self, infra: ActorInfrastructure):
        super().__init__()
        self.infra = infra

        # Constants
        self.WINDOW_SECONDS = 60  # Time window to display
        self.SAMPLING_RATE = 512  # Hz (typical for MindFlex)
        self.MAX_POINTS = self.WINDOW_SECONDS * self.SAMPLING_RATE
        self.DISPLAY_POINTS = 1000  # Maximum points to display

        # Initialize data buffer and tracking
        self.data_buffer = deque(maxlen=self.MAX_POINTS)
        self.last_fetch_time = 0

        self.setWindowTitle("EEG MindFlex")
        self.setMinimumSize(800, 600)

        # Create the main widget and layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)

        # Create the chart
        self.chart = QChart()
        self.chart.setTitle("Raw EEG Signal")
        
        # Create the line series for the data
        self.series = QLineSeries()
        self.chart.addSeries(self.series)

        # Create X axis (time)
        self.axis_x = QValueAxis()
        self.axis_x.setTitleText("Time (seconds)")
        self.axis_x.setRange(0, self.WINDOW_SECONDS)
        self.chart.addAxis(self.axis_x, Qt.AlignmentFlag.AlignBottom)
        self.series.attachAxis(self.axis_x)

        # Create Y axis (signal)
        self.axis_y = QValueAxis()
        self.axis_y.setTitleText("Signal Value")
        self.axis_y.setRange(0, 256)
        self.chart.addAxis(self.axis_y, Qt.AlignmentFlag.AlignLeft)
        self.series.attachAxis(self.axis_y)

        # Create chart view
        chart_view = QChartView(self.chart)
        chart_view.setRenderHint(QPainter.RenderHint.Antialiasing)
        layout.addWidget(chart_view)

        # Setup update timer
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_plot)
        self.update_timer.start(100)  # Update every 100ms

    def update_plot(self):
        # Fetch only new data since last update
        new_data = self.fetch_new_data()
        if not new_data:
            return

        # Add new data to buffer
        self.data_buffer.extend(new_data)

        # Update the plot only if we have data
        if self.data_buffer:
            # Clear and rebuild the series with decimated data
            self.series.clear()
            
            # Calculate stride for data decimation
            stride = max(1, len(self.data_buffer) // self.DISPLAY_POINTS)
            
            # Plot decimated data
            points_to_plot = list(self.data_buffer)[::stride]
            for time, value in points_to_plot:
                self.series.append(time, value)

            # Update X axis range to show the last 60 seconds
            latest_time = self.data_buffer[-1][0]
            self.axis_x.setRange(max(0, latest_time - self.WINDOW_SECONDS), 
                               max(self.WINDOW_SECONDS, latest_time))

    def fetch_new_data(self) -> list[tuple[float, float]]:
        """
        Fetch only new data since the last update.
        Returns:
            A list of (time, value) tuples containing only new data points
        """
        # Get time series data
        time_series = self.infra.hub.timeseries(self.infra.raw_channel.id)
        
        # Filter for only new points
        new_data = [(t, packet.value) for t, packet in time_series 
                   if t > self.last_fetch_time]
        
        if new_data:
            self.last_fetch_time = new_data[-1][0]
        
        return new_data

class GUI(Actor):
    def __init__(self, infra: ActorInfrastructure) -> None:
        super().__init__(
            infra,
            name="gui",
            channels=[infra.packet_channel.id],
            capture_thread=True,
            run_to_completion=False,
        )
        self.infra = infra

    def setup(self) -> None:
        self.app = QApplication([])
        self.window = MainWindow(self.infra)
        self.window.show()
        self.run()

    def act(self) -> bool:
        logger.info("Running GUI")
        self.app.exec()
        logger.info("GUI exited")
        return False