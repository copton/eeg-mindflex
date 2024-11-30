from pathlib import Path
import time
from datetime import datetime

import serial

# Replace with your serial port
SERIAL_PORT = "/dev/cu.cpt-Mindflex"
BAUD_RATE = 57600  # Adjust to your device's settings


def read_serial():
    try:
        # Open the serial port
        with serial.Serial(
            SERIAL_PORT,
            BAUD_RATE,
            timeout=1,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            bytesize=serial.EIGHTBITS,
            # xonxoff=True,
            # rtscts=True,
            dsrdtr=True,
        ) as ser:
            file = Path("out") / datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            with open(file, "bw") as fd:
                print(f"Connected to {SERIAL_PORT}")
                while True:
                    # Read data from the serial port
                    if ser.in_waiting > 0:  # Check if there's data to read
                        data = ser.readline()
                        print(f"Received: {data.hex()}")
                        fd.write(data)
                    else:
                        time.sleep(0.1)  # Reduce CPU usage when no data
    except serial.SerialException as e:
        print(f"Error: {e}")
    except KeyboardInterrupt:
        print("\nExiting program.")


if __name__ == "__main__":
    read_serial()
