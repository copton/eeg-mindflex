import time
from threading import Event, Thread
from contextlib import contextmanager
import pickle
from pathlib import Path
from queue import Queue, Empty
from typing import Generator, Callable, TextIO

import serial  # type: ignore

from model import Packet
from parser import parse


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

        last = time.time()
        for packet in parse(reader()):
            now = time.time()
            output.put((now - last, packet))
            last = now


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


def print_packets_task(
    input: Queue[tuple[float, Packet]],
    output: TextIO,
    stop: Event,
) -> None:
    with _coordinated(stop):
        while not stop.is_set():
            try:
                _, packet = input.get(block=True, timeout=0.1)
            except Empty:
                continue
            output.write(str(packet))
            output.write("\n")


def run_app(tasks: list[Task]) -> None:
    stop = Event()
    threads = [
        Thread(
            target=task,
            args=(stop,),
            daemon=True,
        )
        for task in tasks
    ]

    for thread in threads:
        thread.start()

    try:
        while not stop.is_set():
            time.sleep(1)
    except Exception:
        stop.set()

    for thread in threads:
        thread.join()
