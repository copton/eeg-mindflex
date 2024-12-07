import pickle
import time
from contextlib import contextmanager
from parser import parse
from pathlib import Path
from queue import Empty, Queue
from threading import Event, Thread
from typing import Callable, Generator, TextIO

import serial  # type: ignore

from average import Average
from gui import Gui
from model import Packet, Aggregated, Raw, Eeg


@contextmanager
def _coordinated(stop: Event):
    try:
        yield None
    except Exception:
        stop.set()
        raise


Task = Callable[[Event], None]


def read_serial_task(
    port: str,
    baud: int,
    output: Queue[tuple[float, Packet]],
    stop: Event,
) -> None:
    with _coordinated(stop):

        def reader() -> Generator[int, None, None]:
            with serial.Serial(
                port,
                baud,
                timeout=1,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                bytesize=serial.EIGHTBITS,
                dsrdtr=True,
            ) as ser:
                print(f"reading data from `{port}` at `{baud}` symbols per second")
                while not stop.is_set():
                    if ser.in_waiting > 0:
                        data = ser.read(64)
                        for p in data:
                            yield p
                    else:
                        time.sleep(0.1)

        start = time.time()
        for packet in parse(reader()):
            now = time.time()
            output.put((now - start, packet))


def fork_task(
    input: Queue,
    output1: Queue,
    output2: Queue,
    stop: Event,
) -> None:
    with _coordinated(stop):
        while not stop.is_set():
            try:
                data = input.get(block=True, timeout=0.1)
            except Empty:
                continue

            output1.put(data)
            output2.put(data)


def write_file_task(
    input: Queue[tuple[float, Packet]],
    file: Path,
    stop: Event,
) -> None:
    with _coordinated(stop):
        with open(file, "wb") as fd:
            while not stop.is_set():
                try:
                    data = input.get(block=True, timeout=0.1)
                except Empty:
                    continue

                pickle.dump(data, fd)


def replay_task(
    file: Path,
    output: Queue[tuple[float, Packet]],
    stop: Event,
) -> None:
    with _coordinated(stop):
        with open(file, "rb") as fd:
            while not stop.is_set():
                delay, packet = pickle.load(fd)
                time.sleep(delay)
                output.put((delay, packet))


def prepare_data_task(
    input: Queue[tuple[float, Packet]],
    eeg_data: Queue[tuple[float, Eeg]],
    raw_data: Queue[tuple[float, Raw]],
    stop: Event,
) -> None:
    average = Average()
    with _coordinated(stop):
        while not stop.is_set():
            try:
                timestamp, packet = input.get(block=True, timeout=0.1)
            except Empty:
                continue

            if isinstance(packet, Aggregated):
                eeg_data.put((timestamp, average.update(packet.eeg)))
            else:
                raw_data.put((timestamp, packet))


def print_packets_task(
    eeg_data: Queue[tuple[float, Eeg]],
    raw_data: Queue[tuple[float, Raw]],
    output: TextIO,
    stop: Event,
) -> None:
    def go(queue: Queue):
        while not queue.empty():
            _, packet = queue.get(block=False)
            output.write(str(packet))
            output.write("\n")

    with _coordinated(stop):
        while not stop.is_set():
            go(raw_data)
            go(eeg_data)
            time.sleep(0.1)


def gui_task(
    eeg_data: Queue[tuple[float, Eeg]],
    raw_data: Queue[tuple[float, Raw]],
    stop: Event,
) -> None:
    def watchdog():
        with _coordinated(stop):
            while not stop.is_set():
                time.sleep(1)
            gui.quit()

    thread = Thread(target=watchdog, args=(), daemon=True)
    thread.start()
    gui = Gui(eeg_data, raw_data)
    gui.run()
    stop.set()
    thread.join()


def run_app(tasks: list[Task]) -> None:
    # GUI frameworks insist on running on main thread

    stop = Event()
    threads = [
        Thread(
            target=task,
            args=(stop,),
            daemon=True,
        )
        for task in tasks[:-1]
    ]

    for thread in threads:
        thread.start()

    try:
        tasks[-1](stop)
    finally:
        stop.set()

    for thread in threads:
        thread.join()
