from pathlib import Path

from app.framework import (
    ActorInfrastructure,
    Aggregated,
    Channel,
    Eeg,
    Quality,
    Raw,
)
from app.sensor import make_reader
from tests.reader_sink import ReaderSink


def test_reader_from_file(infra: ActorInfrastructure) -> None:
    # Set up channels
    infra.packet_channel = Channel("packet", infra.hub)
    infra.raw_channel = Channel("raw", infra.hub)
    infra.eeg_channel = Channel("eeg", infra.hub)
    infra.quality_channel = Channel("quality", infra.hub)

    # Create test data file
    test_data_path = Path("./tests/test_data.bin")

    # Create reader and sink
    reader = make_reader(infra, test_data_path)
    sink = ReaderSink(infra, reader.name)

    # Run the actor pool
    infra.pool.start()
    infra.pool.wait()
    infra.pool.stop()

    # Verify results
    assert len(sink.packets) == 10_8942, "Wrong number of packets"
    assert len(sink.raw_data) + len(sink.eeg_data) == len(sink.packets), "missing raw or eeg data"
    assert len(sink.quality_data) == len(sink.eeg_data), "missing quality data"

    # Verify that Raw packets went to raw_data
    assert all(isinstance(p, Raw) for p in sink.raw_data), "Non-Raw data in raw_data"

    # Verify that Aggregated packets produced EEG and Quality data
    assert all(isinstance(e, Eeg) for e in sink.eeg_data), "Non-Eeg data in eeg_data"
    assert all(isinstance(q, Quality) for q in sink.quality_data), "Non-Quality data in quality_data"

    # Verify that all packets are either Raw or Aggregated
    assert all(isinstance(p, Raw | Aggregated) for p in sink.packets), "Unknown packet type received"
