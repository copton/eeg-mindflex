import json
import tempfile
from dataclasses import dataclass
from pathlib import Path

import pytest

from app.framework import Channel
from app.sensor import Recorder, Replay, make_reader
from tests.reader_sink import ReaderSink


@dataclass
class Context:
    """We run this test in two phases.

    This context tracks the results of the first phase so that we can compare
    them to the results of the second phase.

    The first phase writes data, then the second phase replays it.

    """

    recording_file: Path | None
    sink: ReaderSink | None


@pytest.fixture(scope="session")
def context():
    return Context(recording_file=None, sink=None)


@pytest.mark.dependency()
def test_read_write_replay_cycle_phase_1(infra, context):
    # Set up channels
    infra.packet_channel = Channel("packet", infra.hub)
    infra.raw_channel = Channel("raw", infra.hub)
    infra.eeg_channel = Channel("eeg", infra.hub)
    infra.quality_channel = Channel("quality", infra.hub)

    # Create test data file and output file
    test_data_path = Path("./tests/test_data.bin")
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as fd:
        output_path = Path(fd.name)

    # Create reader, writer and sink
    reader = make_reader(infra, test_data_path)
    Recorder(infra, output_path, reader.name)
    sink = ReaderSink(infra, reader.name)

    # Create actors
    infra.pool.start()
    infra.pool.wait()
    infra.pool.stop()

    # Verify results like in test_reader_from_file
    assert len(sink.packets) == 10_8942, "Wrong number of packets in sink"
    assert len(sink.raw_data) + len(sink.eeg_data) == len(sink.packets), "missing raw or eeg data"
    assert len(sink.quality_data) == len(sink.eeg_data), "missing quality data"

    # Verify that the output file was created
    assert output_path.exists(), "Output file was not created"
    with open(output_path) as fd:
        data = json.load(fd)
        assert len(data) == 10_8942, "Wrong number of packets in output file"

    # Save for phase 2
    context.recording_file = output_path
    context.sink = sink


@pytest.mark.dependency(depends=["test_read_write_replay_cycle_phase_1"])
def test_read_write_replay_cycle_phase_2(infra, context):
    # Set up channels
    infra.packet_channel = Channel("packet", infra.hub)
    infra.raw_channel = Channel("raw", infra.hub)
    infra.eeg_channel = Channel("eeg", infra.hub)
    infra.quality_channel = Channel("quality", infra.hub)

    # Create actors
    replay = Replay(infra, context.recording_file)
    sink = ReaderSink(infra, replay.name)

    # Run the actor pool
    infra.pool.start()
    infra.pool.wait()
    infra.pool.stop()

    # Verify results
    assert len(sink.packets) == 10_8942, "Wrong number of packets in sink"
    assert sink.packets == context.sink.packets, "packets do not match"
    assert sink.raw_data == context.sink.raw_data, "raw data do not match"
    assert sink.eeg_data == context.sink.eeg_data, "eeg data do not match"
    assert sink.quality_data == context.sink.quality_data, "quality data do not match"
