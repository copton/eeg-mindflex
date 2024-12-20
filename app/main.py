import argparse
import logging
import os
import sys
import subprocess
from datetime import datetime
from enum import Enum
from functools import partial
from pathlib import Path
from queue import Queue
from typing import Callable, Optional

from model import Eeg, Packet, Raw
from tasks import (
    fork_task,
    gui_task,
    prepare_data_task,
    print_packets_task,
    read_serial_task,
    replay_task,
    run_app,
    write_file_task,
)

RECORDINGS_DIR = "recordings"
BAUD_RATE = 57600


def setup_console_logger(enable_debug: bool) -> None:
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)

    # Create a console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG if enable_debug else logging.INFO)

    # Create and set a formatter
    formatter = logging.Formatter(
        fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    console_handler.setFormatter(formatter)

    # Avoid adding multiple handlers during reconfiguration
    if not logger.handlers:
        logger.addHandler(console_handler)


class Mode(str, Enum):
    GUI = "gui"
    TERMINAL = "terminal"


def main():
    # Set up argument parser
    parser = argparse.ArgumentParser(description="Interact with Mindflex")

    # Add mutually exclusive group for input source
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument(
        "--live",
        type=str,
        metavar="device",
        help="Name of the device to read from, e.g. `/dev/cu.Mindflex`",
    )
    input_group.add_argument(
        "--replay",
        type=str,
        metavar="file",
        help="Name of previuosly recorded file to read from",
    )

    parser.add_argument(
        "--record",
        action="store_true",
        default=False,
        help="Record the session (default: false)",
    )

    parser.add_argument(
        "-m",
        "--mode",
        type=str,
        choices=["gui", "terminal"],
        default="gui",
        help="Mode selector for output (default: terminal)",
    )

    parser.add_argument(
        "--debug",
        action="store_true",
        default=False,
        help="Enable debug logging",
    )

    # Parse arguments
    args = parser.parse_args()

    mode = Mode(args.mode)

    setup_console_logger(args.debug)
    logger = logging.getLogger(__name__)
    logger.debug("debug logs enabled")

    if args.live:
        if args.record:
            os.makedirs(RECORDINGS_DIR, exist_ok=True)
            record = (
                Path(RECORDINGS_DIR)
                / f"{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.pkl"
            )
        else:
            record = None

        app = app_live(args.live, record, mode)

    elif args.replay:
        if args.record:
            sys.stderr.write("--record is not supported in --replay mode")
            sys.exit(1)

        replay = Path(args.replay)
        if not replay.exists():
            sys.stderr.write(f"Replay file `{replay}` does not exist")
            sys.exit(1)

        app = app_replay(replay, mode)

    else:
        sys.stderr.write(
            "internal error: argparse is configured with expecting one of "
            "--live or --replay"
        )
        sys.exit(1)
    subprocess.Popen("caffeinate -di", shell=True)
    run_app(app)


def app_live(port: str, record: Optional[Path], mode: Mode) -> list[Callable]:
    tasks: list[Callable] = []
    packets: Queue[tuple[float, Packet]] = Queue()
    tasks.append(partial(read_serial_task, port, BAUD_RATE, packets))

    if record is not None:
        packets_fork1: Queue = Queue()
        packets_fork2: Queue = Queue()
        tasks.append(partial(fork_task, packets, packets_fork1, packets_fork2))
        tasks.append(partial(write_file_task, packets_fork1, record))
        packets = packets_fork2

    tasks.extend(_consumers(packets, mode))
    return tasks


def app_replay(replay: Path, mode: Mode) -> list[Callable]:
    tasks: list[Callable] = []
    packets: Queue[tuple[float, Packet]] = Queue()
    tasks.append(partial(replay_task, replay, packets))

    tasks.extend(_consumers(packets, mode))
    return tasks


def _consumers(
    packets: Queue[tuple[float, Packet]],
    mode: Mode,
) -> list[Callable]:
    tasks: list[Callable] = []
    eeg_data: Queue[tuple[float, Eeg]] = Queue()
    raw_data: Queue[tuple[float, Raw]] = Queue()
    tasks.append(partial(prepare_data_task, packets, eeg_data, raw_data))

    if mode == Mode.TERMINAL:
        tasks.append(partial(print_packets_task, eeg_data, raw_data, sys.stdout))
    else:
        tasks.append(partial(gui_task, eeg_data, raw_data))

    return tasks


if __name__ == "__main__":
    main()
