import argparse
import logging
import os
import sys
from datetime import datetime
from enum import Enum
from pathlib import Path

from app.data_processing import Median
from app.framework import (
    ActorInfrastructure,
    ActorPool,
    Channel,
    Eeg,
    Hub,
    MedianEeg,
    Packet,
    Quality,
    Raw,
    Timer,
)
from app.sensor import Recorder, Replay, make_reader
from app.system import OsOperations, PreventSleep, create_os_operations
from app.ui import GUI, Console, VolumeControl

RECORDINGS_DIR = "recordings"


class UIMode(str, Enum):
    GUI = "gui"
    TERMINAL = "terminal"


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

    parser.add_argument(
        "--prevent-sleep",
        action="store_true",
        default=True,
        help="Prevent system from sleeping while running (default: true)",
    )

    # Parse arguments
    args = parser.parse_args()

    setup_console_logger(args.debug)
    logger = logging.getLogger(__name__)
    logger.debug("debug logs enabled")

    run(args)


def run(args: argparse.Namespace) -> None:
    ui_mode = UIMode(args.mode)

    os_operations: OsOperations | None = create_os_operations()
    if os_operations is None:
        sys.stderr.write("No specific implementation for os available")
        sys.exit(1)

    timer = Timer()
    hub = Hub(timer)
    pool = ActorPool()
    raw_channel: Channel[Raw] = Channel("raw", hub)
    eeg_channel: Channel[Eeg] = Channel("eeg", hub)
    quality_channel: Channel[Quality] = Channel("quality", hub)
    packet_channel: Channel[Packet] = Channel("packet", hub)
    median_eeg_channel: Channel[MedianEeg] = Channel("median_eeg", hub)
    infra = ActorInfrastructure(
        hub,
        pool,
        timer,
        raw_channel,
        eeg_channel,
        quality_channel,
        packet_channel,
        median_eeg_channel,
    )

    if args.live:
        make_reader(infra, Path(args.live))

    elif args.replay:
        replay = Path(args.replay)

        if not replay.exists():
            sys.stderr.write(f"Replay file `{replay}` does not exist")
            sys.exit(1)

        Replay(infra, replay)

    else:
        sys.stderr.write("internal error: argparse is configured with expecting one of --live or --replay")
        sys.exit(1)

    if args.record:
        os.makedirs(RECORDINGS_DIR, exist_ok=True)
        record = Path(RECORDINGS_DIR) / f"{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.json"
        Recorder(infra, record, wait_for=None)

    Median(infra)
    VolumeControl(infra, os_operations)

    if ui_mode == UIMode.GUI:
        GUI(infra)
    elif ui_mode == UIMode.TERMINAL:
        Console(infra, sys.stdout)
    else:
        sys.stderr.write(f"internal error: unknown ui mode `{ui_mode}`")
        sys.exit(1)

    with PreventSleep(args.prevent_sleep, os_operations):
        run_app(pool)


def run_app(pool: ActorPool) -> None:
    # One of the actors will capture the main thread that runs this function...
    pool.start()
    # .. so we reach this point here when that main actor quits.
    pool.stop()


if __name__ == "__main__":
    main()
