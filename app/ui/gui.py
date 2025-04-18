import logging
import time
from typing import Any, Dict, List, NamedTuple
from dataclasses import dataclass

import numpy as np
from pyqtgraph import PlotWidget, ViewBox, mkPen  # type: ignore
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget

from app.framework import Actor, ActorInfrastructure, ChannelID, Raw, Timestamp
from app.framework.hub import TimeSeries

logger = logging.getLogger(__name__)

# Constants
RAW_SAMPLING_RATE = 100  # Hz
BAND_SAMPLING_RATE = 1  # Hz
WINDOW_SIZE = 60  # seconds

@dataclass
class BandConfig:
    """Configuration for an EEG band plot"""
    name: str
    color: tuple
    data_attr: str  # The attribute name in MedianEeg to access this band's data

# Define all EEG bands configuration
BAND_CONFIGS = [
    BandConfig("Delta", (255, 0, 0), "delta"),      # Red
    BandConfig("Theta", (255, 165, 0), "theta"),    # Orange
    BandConfig("Low Alpha", (0, 100, 0), "low_alpha"),  # Dark Green
    BandConfig("High Alpha", (0, 255, 0), "high_alpha"), # Bright Green
    BandConfig("Low Beta", (0, 0, 255), "low_beta"),    # Blue
    BandConfig("High Beta", (75, 0, 130), "high_beta"), # Indigo
    BandConfig("Low Gamma", (238, 130, 238), "low_gamma"), # Violet
    BandConfig("Mid Gamma", (128, 0, 128), "mid_gamma"),  # Purple
]

class RealTimePlot:
    """A class to manage real-time plotting of sensor data"""

    def __init__(self, plot_widget: PlotWidget, viewbox: ViewBox):
        """
        Initialize the real-time plot.

        Args:
            plot_widget: The pyqtgraph PlotWidget to use for plotting
            viewbox: The pyqtgraph ViewBox to add the plot line to
        """
        self.plot_widget = plot_widget
        self.viewbox = viewbox
        self.window_size_seconds = WINDOW_SIZE
        self.buffer_size = WINDOW_SIZE * RAW_SAMPLING_RATE

        # Initialize empty data arrays
        self.times = np.array([])
        self.values = np.array([])
        self.start_time = 0.0
        self.has_data = False

        # Create the plot line with thinner width
        self.pen = mkPen(color="b", width=1)
        self.plot_line = self.plot_widget.plotItem.plot(self.times, self.values, pen=self.pen, name="Raw")
        self.viewbox.addItem(self.plot_line)

        # Set initial X range to show the full window
        self.plot_widget.setXRange(0, self.window_size_seconds)

    def update_plot(self, time_series: TimeSeries) -> None:
        """
        Update the plot with new data points.

        Args:
            time_series: List of (timestamp, data) tuples
        """
        if not time_series:
            return

        # Extract timestamps and values
        new_times = np.array([point[0] for point in time_series])
        new_values = np.array([point[1].value for point in time_series])

        # If this is our first data, record the start time
        if not self.has_data and len(new_times) > 0:
            self.start_time = new_times[0]
            self.has_data = True

        # Normalize timestamps relative to start time for display
        new_times_normalized = new_times - self.start_time

        # Update our data arrays
        if len(self.times) == 0:
            self.times = new_times_normalized
            self.values = new_values
        else:
            # Only append new points that come after our latest point
            if len(new_times_normalized) > 0:
                # Find the index of new data points that come after our latest point
                last_time = self.times[-1]
                indices = np.where(new_times_normalized > last_time)[0]

                if len(indices) > 0:
                    self.times = np.append(self.times, new_times_normalized[indices])
                    self.values = np.append(self.values, new_values[indices])

        # Update the plot data
        self.plot_line.setData(self.times, self.values)

        # Update the x-axis range
        if len(self.times) > 0:
            current_time = self.times[-1]

            # Only start scrolling after we've filled the initial window
            if current_time >= self.window_size_seconds:
                x_min = current_time - self.window_size_seconds
                x_max = current_time
            else:
                # Keep the view fixed at 0 to window_size while collecting initial data
                x_min = 0
                x_max = self.window_size_seconds

            self.plot_widget.setXRange(x_min, x_max)

            # After setting the view, trim the data to keep only what's needed
            # Keep enough data for the window plus a small buffer
            if current_time > self.window_size_seconds:
                cutoff_time = current_time - self.window_size_seconds - 1  # keep 1 second extra as buffer
                valid_indices = np.where(self.times >= cutoff_time)[0]
                if len(valid_indices) > 0:
                    self.times = self.times[valid_indices]
                    self.values = self.values[valid_indices]

    def add_new_point(self, timestamp: Timestamp, data: Raw) -> None:
        """
        Add a single new data point to the plot.

        Args:
            timestamp: The timestamp of the data point
            data: The Raw data object containing the value
        """
        # If this is our first data point, set the start time
        if not self.has_data:
            self.start_time = timestamp
            self.has_data = True

        # Normalize timestamp
        normalized_time = timestamp - self.start_time

        # Only add if it's a new point
        if len(self.times) == 0 or normalized_time > self.times[-1]:
            # Create a small time series with just this point
            self.times = np.append(self.times, normalized_time)
            self.values = np.append(self.values, data.value)

            # Keep only the most recent buffer_size points
            if len(self.times) > self.buffer_size:
                self.times = self.times[-self.buffer_size :]
                self.values = self.values[-self.buffer_size :]

            # Update the plot
            if len(self.times) > 0:
                current_time = self.times[-1]

                # If we've exceeded the window size, start scrolling
                if current_time > self.window_size_seconds:
                    x_min = current_time - self.window_size_seconds
                    x_max = current_time
                else:
                    # Otherwise, keep the display fixed from 0 to window_size
                    x_min = 0
                    x_max = self.window_size_seconds

                # Update the plot data
                self.plot_line.setData(self.times, self.values)

                # Update the axis range
                self.plot_widget.setXRange(x_min, x_max)

class BandPlot:
    """A class to manage real-time plotting of EEG band data"""

    def __init__(self, plot_widget: PlotWidget, config: BandConfig, viewbox: ViewBox):
        self.plot_widget = plot_widget
        self.viewbox = viewbox
        self.config = config
        self.window_size_seconds = WINDOW_SIZE
        self.buffer_size = WINDOW_SIZE * BAND_SAMPLING_RATE

        # Initialize empty data arrays
        self.times = np.array([])
        self.values = np.array([])
        self.start_time = 0.0
        self.has_data = False

        # Create the plot line
        self.pen = mkPen(color=self.config.color, width=2)
        self.plot_line = self.plot_widget.plotItem.plot([], [], pen=self.pen, name=self.config.name)
        self.viewbox.addItem(self.plot_line)

    def update_plot(self, time_series: TimeSeries) -> None:
        if not time_series:
            return

        # Extract timestamps and band values from MedianEeg data
        new_times = np.array([point[0] for point in time_series])
        new_values = np.array([getattr(point[1], self.config.data_attr) for point in time_series])

        if not self.has_data and len(new_times) > 0:
            self.start_time = new_times[0]
            self.has_data = True

        new_times_normalized = new_times - self.start_time

        if len(self.times) == 0:
            self.times = new_times_normalized
            self.values = new_values
        else:
            if len(new_times_normalized) > 0:
                last_time = self.times[-1]
                indices = np.where(new_times_normalized > last_time)[0]

                if len(indices) > 0:
                    self.times = np.append(self.times, new_times_normalized[indices])
                    self.values = np.append(self.values, new_values[indices])

        self.plot_line.setData(self.times, self.values)

        if len(self.times) > 0:
            current_time = self.times[-1]

            if current_time >= self.window_size_seconds:
                x_min = current_time - self.window_size_seconds
                x_max = current_time
            else:
                x_min = 0
                x_max = self.window_size_seconds

            self.plot_widget.setXRange(x_min, x_max)

            if current_time > self.window_size_seconds:
                cutoff_time = current_time - self.window_size_seconds - 1
                valid_indices = np.where(self.times >= cutoff_time)[0]
                if len(valid_indices) > 0:
                    self.times = self.times[valid_indices]
                    self.values = self.values[valid_indices]

class GUI(Actor):
    def __init__(self, infra: ActorInfrastructure) -> None:
        super().__init__(
            infra,
            name="gui",
            channels=[
                infra.raw_channel.id,
                infra.median_eeg_channel.id,
            ],
            capture_thread=True,
            run_to_completion=False,
        )
        self.infra = infra

        # Configuration parameters
        self.update_interval = 100  # ms

        # Create the application and main window
        self.app = QApplication.instance() or QApplication([])
        self.main_window = QMainWindow()
        self.main_window.setWindowTitle("EEG Mindflex Visualizer")
        self.main_window.resize(1000, 600)  # Back to original height since we're using one plot

        # Create central widget and layout
        self.central_widget = QWidget()
        self.main_layout = QVBoxLayout()
        self.central_widget.setLayout(self.main_layout)

        # Create single plot widget for all signals
        self.plot_widget = PlotWidget()
        
        # Configure the main plot
        self.plot_widget.setBackground("w")
        self.plot_widget.setTitle("EEG Signals")
        self.plot_widget.setLabel("right", "Raw signal")
        self.plot_widget.setLabel("left", "Band power")
        self.plot_widget.setLabel("bottom", "Time (s)")
        self.plot_widget.showGrid(x=True, y=True, alpha=0.3)
        
        # Create two ViewBoxes
        self.raw_viewbox = self.plot_widget.getPlotItem().getViewBox()
        self.band_viewbox = ViewBox()
        
        # Add the band ViewBox to the plot
        self.plot_widget.getPlotItem().scene().addItem(self.band_viewbox)
        
        # Set up left Y axis for bands
        left_axis = self.plot_widget.getPlotItem().getAxis('left')
        self.plot_widget.getPlotItem().scene().addItem(left_axis)
        left_axis.linkToView(self.band_viewbox)
        self.band_viewbox.setYRange(0, 100_000)
        
        # Set up right Y axis for raw signal
        right_axis = self.plot_widget.getPlotItem().getAxis('right')
        right_axis.linkToView(self.raw_viewbox)
        self.raw_viewbox.setYRange(-600, 600)
        
        # Link X axes
        self.band_viewbox.setXLink(self.raw_viewbox)
        
        # Update views when resizing
        def updateViews():
            self.band_viewbox.setGeometry(self.raw_viewbox.sceneBoundingRect())
        
        updateViews()
        self.raw_viewbox.sigResized.connect(updateViews)
        
        # Add legend
        self.plot_widget.addLegend()
        
        # Create the raw signal plot (using raw ViewBox)
        self.real_time_plot = RealTimePlot(self.plot_widget, self.raw_viewbox)
        
        # Create all band plots (using band ViewBox)
        self.band_plots = []
        for config in BAND_CONFIGS:
            band_plot = BandPlot(self.plot_widget, config, self.band_viewbox)
            self.band_plots.append(band_plot)

        # Add widget to main layout
        self.main_layout.addWidget(self.plot_widget)

        # Set central widget
        self.main_window.setCentralWidget(self.central_widget)

        # Create timer for periodic updates
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_plot)

        # Keep track of last processed timestamp
        self.last_timestamp = 0.0

    def setup(self) -> None:
        """Set up the GUI and show the main window"""
        # Show the main window
        self.main_window.show()

        # Start the timer for periodic updates
        self.timer.start(self.update_interval)

        # Start the main event loop
        self.run()

    def act(self) -> bool:
        """
        Process the QT events and update the GUI

        Returns:
            True to keep the actor running
        """
        # Process QT events
        self.app.processEvents()

        # Sleep a bit to not hog the CPU
        time.sleep(0.01)

        return True

    def update_plot(self) -> None:
        """Update the plots with the latest data from the hub"""
        # Fetch raw data from hub
        raw_data = self.infra.hub.timeseries(
            self.infra.raw_channel.id,
            number_of_points=RAW_SAMPLING_RATE * WINDOW_SIZE
        )
        
        # Fetch median EEG data from hub (using band sampling rate)
        median_data = self.infra.hub.timeseries(
            self.infra.median_eeg_channel.id,
            number_of_points=BAND_SAMPLING_RATE * WINDOW_SIZE
        )

        # Update raw signal plot
        self.real_time_plot.update_plot(raw_data)
        
        # Update all band plots
        for band_plot in self.band_plots:
            band_plot.update_plot(median_data)

    def handle(self, channel: ChannelID, timestamp: Timestamp, data: Any) -> None:
        """
        Handle incoming data from the subscribed channels

        Args:
            channel: The channel ID
            timestamp: The timestamp of the data
            data: The data object
        """
        if channel == self.infra.raw_channel.id:
            # Add the new data point to the plot
            self.real_time_plot.add_new_point(timestamp, data)
            self.last_timestamp = timestamp

    def shutdown(self) -> None:
        """Clean up resources when shutting down"""
        logger.info("GUI shutting down")
        self.timer.stop()
