import matplotlib.pyplot as plt
import matplotlib.animation as animation
import numpy as np
import time

# Create a figure and axis for the plot
fig, ax = plt.subplots()
x_data, y_data1, y_data2 = [], [], []  # Lists to store x and y data for two graphs
(line1,) = ax.plot([], [], lw=2, label="Sine Wave")  # First graph
(line2,) = ax.plot([], [], lw=2, label="Cosine Wave")  # Second graph

# Set up the plot axes
x_range = 10  # Fixed range for the x-axis (e.g., 10 seconds)
ax.set_xlim(0, x_range)
ax.set_ylim(-1.5, 1.5)  # Value range for both graphs
ax.set_title("Real-Time Time Series Plot")
ax.set_xlabel("Time (s)")
ax.set_ylabel("Value")
ax.legend(loc="upper right")  # Add a legend


# Function to initialize the plot
def init():
    line1.set_data([], [])
    line2.set_data([], [])
    return line1, line2


# Function to update the plot
def update(frame):
    global x_data, y_data1, y_data2

    # Append new data
    current_time = time.time() - start_time
    x_data.append(current_time)
    y_data1.append(np.sin(2 * np.pi * 0.5 * current_time))  # Sine wave
    y_data2.append(np.cos(2 * np.pi * 0.5 * current_time))  # Cosine wave

    # Remove points outside the fixed range
    x_data = [x for x in x_data if x >= current_time - x_range]
    y_data1 = y_data1[-len(x_data) :]
    y_data2 = y_data2[-len(x_data) :]

    # Update the plot data
    line1.set_data(x_data, y_data1)
    line2.set_data(x_data, y_data2)

    # Shift the x-axis while keeping the scale constant
    ax.set_xlim(current_time - x_range, current_time)

    return line1, line2


# Start time for the time series
start_time = time.time()

# Create an animation
ani = animation.FuncAnimation(fig, update, init_func=init, blit=True, interval=50)

# Show the plot
plt.show()
