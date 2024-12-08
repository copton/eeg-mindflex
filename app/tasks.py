import logging
import pickle
import time
from parser import parse
from pathlib import Path
from queue import Empty, Queue
from threading import Event, Thread
from typing import Callable, Generator, TextIO

import numpy as np
import serial  # type: ignore

from gui import Gui
from model import Aggregated, Eeg, Packet, Raw

WINDOW_SIZE = 60


def coordinated_task(func):
    logger = logging.getLogger(f"{__name__}.{func.__name__}")

    def wrapper(*args, stop: Event):
        logger.debug("start")
        try:
            func(*args, stop=stop, logger=logger)
        except Exception:
            logger.debug("abort")
            raise
        finally:
            stop.set()
        logger.debug("stop")

    return wrapper


@coordinated_task
def read_serial_task(
    port: str,
    baud: int,
    output: Queue[tuple[float, Packet]],
    stop: Event,
    logger: logging.Logger,
) -> None:
    def file_reader() -> Generator[int, None, None]:
        logger.info("reading binary data from file '%s'", port)
        with open(port, "br") as fd:
            while not stop.is_set():
                data = fd.read(128)
                if not data:
                    break
                for p in data:
                    yield p
                time.sleep(0.01)

    def serial_reader() -> Generator[int, None, None]:
        with serial.Serial(
            port,
            baud,
            timeout=1,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            bytesize=serial.EIGHTBITS,
        ) as ser:
            logger.info(
                "reading binary data from device '%s' at '%s' symbols per second",
                port,
                baud,
            )
            while not stop.is_set():
                if ser.in_waiting > 0:
                    data = ser.read(64)
                    for p in data:
                        yield p
                else:
                    time.sleep(0.1)

    start = time.time()
    gen = serial_reader if port.startswith("/dev") else file_reader
    for packet in parse(gen()):
        now = time.time()
        output.put((now - start, packet))


@coordinated_task
def fork_task(
    input: Queue,
    output1: Queue,
    output2: Queue,
    stop: Event,
    logger: logging.Logger,
) -> None:
    while not stop.is_set():
        try:
            data = input.get(block=True, timeout=0.1)
        except Empty:
            continue

        output1.put(data)
        output2.put(data)


@coordinated_task
def write_file_task(
    input: Queue[tuple[float, Packet]],
    file: Path,
    stop: Event,
    logger: logging.Logger,
) -> None:
    logger.info("capturing recording to '%s'", file)
    with open(file, "wb") as fd:
        while not stop.is_set():
            try:
                data = input.get(block=True, timeout=0.1)
            except Empty:
                continue

            pickle.dump(data, fd)


@coordinated_task
def replay_task(
    file: Path,
    output: Queue[tuple[float, Packet]],
    stop: Event,
    logger: logging.Logger,
) -> None:
    logger.info("replaying recording from '%s'", file)
    with open(file, "rb") as fd:
        while not stop.is_set():
            delay, packet = pickle.load(fd)
            time.sleep(delay)
            output.put((delay, packet))


def componentwise_median(vectors: list[np.ndarray]) -> Eeg:
    array_stack = np.vstack(vectors)
    median_vector = np.median(array_stack, axis=0)
    return Eeg.from_vector(median_vector)


@coordinated_task
def prepare_data_task(
    input: Queue[tuple[float, Packet]],
    eeg_data: Queue[tuple[float, Eeg]],
    raw_data: Queue[tuple[float, Raw]],
    stop: Event,
    logger: logging.Logger,
) -> None:
    window: list[np.ndarray] = []
    while not stop.is_set():
        try:
            timestamp, packet = input.get(block=True, timeout=0.1)
        except Empty:
            continue

        if isinstance(packet, Aggregated):
            window.append(packet.eeg.as_vector())
            logger.debug("window size is %d", len(window))
            if len(window) == WINDOW_SIZE:
                eeg_data.put((timestamp, componentwise_median(window)))
                window.pop(0)
            else:
                eeg_data.put((timestamp, Eeg.zero()))
        else:
            raw_data.put((timestamp, packet))


@coordinated_task
def print_packets_task(
    eeg_data: Queue[tuple[float, Eeg]],
    raw_data: Queue[tuple[float, Raw]],
    output: TextIO,
    stop: Event,
    logger: logging.Logger,
) -> None:
    def go(queue: Queue):
        while not queue.empty():
            _, packet = queue.get(block=False)
            output.write(str(packet))
            output.write("\n")

    while not stop.is_set():
        go(raw_data)
        go(eeg_data)
        time.sleep(0.1)


@coordinated_task
def gui_task(
    eeg_data: Queue[tuple[float, Eeg]],
    raw_data: Queue[tuple[float, Raw]],
    stop: Event,
    logger: logging.Logger,
) -> None:
    def watchdog():
        while not stop.is_set():
            time.sleep(1)
        gui.quit()

    thread = Thread(target=watchdog, args=(), daemon=True)
    thread.start()
    gui = Gui(eeg_data, raw_data)
    gui.run()
    stop.set()
    thread.join()


def run_app(tasks: list[Callable]) -> None:
    # GUI frameworks insist on running on main thread

    stop = Event()
    threads = [
        Thread(
            target=task,
            args=(),
            kwargs={"stop": stop},
            daemon=True,
        )
        for task in tasks[:-1]
    ]

    for thread in threads:
        thread.start()

    try:
        tasks[-1](stop=stop)
    finally:
        stop.set()

    for thread in threads:
        thread.join()
