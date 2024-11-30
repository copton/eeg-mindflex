import time
import sys
from typing import Optional

import matplotlib.pyplot as plt
import matplotlib.animation as animation

from interpret import replay, Aggregated, Packet

sensor_data = replay(sys.argv[1], 0.001)


class Graph:
    def __init__(self, label: str) -> None:
        (self.plot,) = ax.plot([], [], lw=1, label=label)
        self.data: list = []

    def update(self, x_data, point):
        self.data.append(point)
        self.data = self.data[-len(x_data) :]
        self.plot.set_data(x_data, sliding_average(self.data, 10))


def sliding_average(numbers, window_size):
    averages = []
    for i in range(len(numbers)):
        # Define the start of the window
        start_index = max(0, i - window_size)
        # Define the current window
        window = numbers[start_index : i + 1]
        # Calculate the average for the current window
        averages.append(sum(window) / len(window))
    return averages


def min_max(
    packet: Aggregated, cur_min: Optional[int], cur_max: Optional[int]
) -> tuple[int, int]:
    y_min = min(
        packet.eeg.delta,
        packet.eeg.theta,
        packet.eeg.low_alpha,
        packet.eeg.high_alpha,
        packet.eeg.low_beta,
        packet.eeg.high_beta,
        packet.eeg.low_gamma,
        packet.eeg.mid_gamma,
    )
    if cur_min is not None:
        y_min = min(y_min, cur_min)

    y_max = max(
        packet.eeg.delta,
        packet.eeg.theta,
        packet.eeg.low_alpha,
        packet.eeg.high_alpha,
        packet.eeg.low_beta,
        packet.eeg.high_beta,
        packet.eeg.low_gamma,
        packet.eeg.mid_gamma,
    )
    if cur_max is not None:
        y_max = max(y_max, cur_max)

    if y_min == y_max:
        y_max += 1

    return (y_min, y_max)


# Create a figure and axis for the plot
fig, ax = plt.subplots(dpi=180)
x_data: list = []
delta = Graph("delta")
theta = Graph("theta")
low_alpha = Graph("low_alpha")
high_alpha = Graph("high_alpha")
low_beta = Graph("low_beta")
high_beta = Graph("high_beta")
low_gamma = Graph("low_gamma")
mid_gamma = Graph("mid_gamma")

# Set up the plot axes
x_range = 50  # Fixed range for the x-axis (e.g., 10 seconds)
y_min = None
y_max = None
ax.set_xlim(0, x_range)
ax.set_ylim(0, 10)
ax.set_title("Real-Time Time Series Plot", fontsize=8)
ax.set_xlabel("Time (s)", fontsize=8)
ax.set_ylabel("Value", fontsize=8)
ax.legend(loc="upper right", fontsize=8)  # Add a legend


# Start time for the time series
start_time = time.time()


# Function to initialize the plot
def init():
    delta.plot.set_data([], [])
    theta.plot.set_data([], [])
    low_alpha.plot.set_data([], [])
    high_alpha.plot.set_data([], [])
    low_beta.plot.set_data([], [])
    high_beta.plot.set_data([], [])
    low_gamma.plot.set_data([], [])
    mid_gamma.plot.set_data([], [])
    return (
        delta.plot,
        theta.plot,
        low_alpha.plot,
        high_alpha.plot,
        low_beta.plot,
        high_beta.plot,
        low_gamma.plot,
        mid_gamma.plot,
    )


# Function to update the plot
def update(frame):
    global x_data, y_max, y_min

    # Append new data
    current_time = time.time() - start_time

    x_data.append(current_time)
    x_data = [x for x in x_data if x >= current_time - x_range]

    packet = None
    while not isinstance(packet, Aggregated):
        packet = next(sensor_data)
    print(packet)
    delta.update(x_data, packet.eeg.delta)
    theta.update(x_data, packet.eeg.theta)
    low_alpha.update(x_data, packet.eeg.low_alpha)
    high_alpha.update(x_data, packet.eeg.high_alpha)
    low_beta.update(x_data, packet.eeg.low_beta)
    high_beta.update(x_data, packet.eeg.high_beta)
    low_gamma.update(x_data, packet.eeg.low_gamma)
    mid_gamma.update(x_data, packet.eeg.mid_gamma)

    y_min, y_max = min_max(packet, y_min, y_max)
    ax.set_ylim(y_min, y_max)

    # Shift the x-axis while keeping the scale constant
    ax.set_xlim(current_time - x_range, current_time)

    return (
        delta.plot,
        theta.plot,
        low_alpha.plot,
        high_alpha.plot,
        low_beta.plot,
        high_beta.plot,
        low_gamma.plot,
        mid_gamma.plot,
    )


# Create an animation
ani = animation.FuncAnimation(fig, update, init_func=init, blit=True, interval=50)

# Show the plot
plt.show()
