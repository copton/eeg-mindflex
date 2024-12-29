from app.framework import Channel, Hub


def test_no_subscribers(hub: Hub):
    hub.publish("channel1", "data1")
    assert hub.timeseries("channel1", 1) == [(1.0, "data1")]
    hub.publish("channel1", "data2")
    assert hub.timeseries("channel1", 2) == [(1.0, "data1"), (2.0, "data2")]
    assert hub.timeseries("channel1", 1) == [(2.0, "data2")]
    assert hub.timeseries("channel1", 10) == [(1.0, "data1"), (2.0, "data2")]


def test_single_subscriber_single_channel(hub: Hub):
    subscriber = "subscriber1"
    channel = "channel1"
    hub.subscribe(subscriber, [channel])
    hub.publish(channel, "data1")
    assert hub.read(subscriber) == (channel, (1.0, "data1"))


def test_single_subscriber_multiple_channels(hub: Hub):
    subscriber = "subscriber1"
    channels = ["channel1", "channel2"]
    hub.subscribe(subscriber, channels)
    hub.publish(channels[0], "data1")
    hub.publish(channels[1], "data2")
    assert hub.read(subscriber) == (channels[0], (1.0, "data1"))
    assert hub.read(subscriber) == (channels[1], (2.0, "data2"))


def test_multiple_subscribers_single_channel(hub: Hub):
    subscriber1 = "subscriber1"
    subscriber2 = "subscriber2"
    channel = "channel1"
    hub.subscribe(subscriber1, [channel])
    hub.subscribe(subscriber2, [channel])
    hub.publish(channel, "data1")
    assert hub.read(subscriber1) == (channel, (1.0, "data1"))
    assert hub.read(subscriber2) == (channel, (1.0, "data1"))


def test_channel_adapter(hub: Hub):
    channel = Channel[str]("channel1", hub)
    subscriber = "subscriber1"
    hub.subscribe(subscriber, [channel.id])
    channel.publish("data1")
    message = hub.read(subscriber)
    assert message is not None
    channel_id, (timestamp, data) = message
    assert channel_id == channel.id
    assert timestamp == 1.0
    assert channel.read(data) == "data1"
    assert hub.timeseries(channel.id, 1) == [(1.0, "data1")]
