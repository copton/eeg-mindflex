import matplotlib.pyplot as plt
import matplotlib.animation as animation
import numpy as np
import time

from interpret import replay


class Graph:
    def __init__(self, label: str) -> None:
        (self.plot,) = ax.plot([], [], lw=2, label=label)
        self.data: list = []

    def update(self, x_data, point):
        self.data.append(point)
        self.data = self.data[-len(self.data) :]
        self.plot.set_data(x_data, self.data)


# Create a figure and axis for the plot
fig, ax = plt.subplots()
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
x_range = 10  # Fixed range for the x-axis (e.g., 10 seconds)
y_min = 0
y_max = 10
ax.set_xlim(0, x_range)
ax.set_ylim(y_min, y_max)
ax.set_title("Real-Time Time Series Plot")
ax.set_xlabel("Time (s)")
ax.set_ylabel("Value")
ax.legend(loc="upper right")  # Add a legend

sensor_data = replay(0.1)


# Function to initialize the plot
def init():
    delta.plot.set_data([], [])
    theta.plot.set_data([], [])
    return delta.plot, theta.plot


# Function to update the plot
def update(frame):
    global x_data, y_max, y_min

    # Append new data
    current_time = time.time() - start_time

    x_data.append(current_time)
    x_data = [x for x in x_data if x >= current_time - x_range]

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

    y_max = max(y_max, packet.eeg.delta, packet.eeg.


    # Shift the x-axis while keeping the scale constant
    ax.set_xlim(current_time - x_range, current_time)

    return delta.plot, theta.plot


# Start time for the time series
start_time = time.time()

# Create an animation
ani = animation.FuncAnimation(fig, update, init_func=init, blit=True, interval=50)

# Show the plot
plt.show()
