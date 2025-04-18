import threading
from queue import Empty, Queue
from typing import Any, Generic, TypeVar

from .timer import Timer, Timestamp

SubscriberID = str
ChannelID = str
DataPoint = tuple[Timestamp, Any]
TimeSeries = list[DataPoint]


class Hub:
    def __init__(self, timer: Timer) -> None:
        self._lock = threading.Lock()
        self._timer = timer
        self._data: dict[ChannelID, TimeSeries] = {}
        self._subscribers: dict[ChannelID, set[SubscriberID]] = {}
        self._read_queues: dict[SubscriberID, Queue[tuple[ChannelID, DataPoint]]] = {}

    def subscribe(self, subscriber: SubscriberID, channels: list[ChannelID]) -> None:
        if len(channels) == 0:
            return

        with self._lock:
            if subscriber in self._read_queues:
                raise ValueError(f"Subscriber {subscriber} is already subscribed to channels")

            for channel in channels:
                if channel not in self._data:
                    self._data[channel] = []

                self._subscribers.setdefault(channel, set()).add(subscriber)

            self._read_queues[subscriber] = Queue()

    def publish(self, channel: ChannelID, data: Any) -> None:
        with self._lock:
            data_point = (self._timer.elapsed(), data)
            self._data.setdefault(channel, []).append(data_point)
            for subscriber in self._subscribers.get(channel, []):
                self._read_queues[subscriber].put((channel, data_point))

    def read(self, subscriber: SubscriberID) -> tuple[ChannelID, DataPoint] | None:
        with self._lock:
            if subscriber not in self._read_queues:
                raise ValueError(f"Subscriber {subscriber} is not subscribed to any channels")

            queue = self._read_queues[subscriber]

        try:
            return queue.get(block=True, timeout=0.1)
        except Empty:
            return None

    def timeseries(self, channel: ChannelID, number_of_points: int | None = None) -> TimeSeries:
        with self._lock:
            if channel not in self._data:
                return []
            if number_of_points is None:
                return self._data[channel]
            else:
                return self._data[channel][-number_of_points:]


T = TypeVar("T")


class Channel(Generic[T]):
    """A channel for publishing and subscribing to data.

    It's main job is to provide static typing for the data that is managed by the channel.
    """

    def __init__(self, id: ChannelID, hub: Hub):
        self._id = id
        self._hub = hub

    @property
    def id(self) -> ChannelID:
        return self._id

    def publish(self, data: T) -> None:
        self._hub.publish(self._id, data)

    def read(self, data: Any) -> T:
        return data
