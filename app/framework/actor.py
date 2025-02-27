import logging
import threading
import traceback
from typing import Any

from .hub import ChannelID, SubscriberID, Timestamp
from .infra import ActorInfrastructure
from .types import ActorState

logger = logging.getLogger(__name__)


class Actor:
    """Encapsulates a thread for running background tasks."""

    def __init__(
        self,
        infra: ActorInfrastructure,
        name: SubscriberID,
        channels: list[ChannelID],
        capture_thread: bool,
        run_to_completion: bool,
    ):
        self._infra = infra
        self._name = name
        self._channels = channels
        self._run_to_completion = run_to_completion
        self._thread: threading.Thread | None = None
        self._state = ActorState.INIT
        self._state_lock = threading.Lock()

        self._stop_event = self._infra.pool.add(self, capture_thread)
        self._infra.hub.subscribe(self._name, channels)

    @property
    def state(self) -> ActorState:
        """Get the current state of the actor."""
        with self._state_lock:
            return self._state

    @property
    def name(self) -> SubscriberID:
        """Get the name of the actor."""
        return self._name

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            logger.warning("Thread %s already running", self._name)
            return

        self._thread = threading.Thread(target=self.setup, daemon=True)
        self._thread.start()
        logger.debug("Actor %s started in new thread", self._name)

    def join(self) -> None:
        if self._thread is None:
            return

        logger.debug("Waiting for thread for actor %s to stop", self._name)
        self._thread.join()
        self._thread = None
        logger.debug("Thread for actor %s stopped", self._name)

    def run(self) -> None:
        self._set_state(ActorState.RUNNING)
        try:
            while True:
                if len(self._channels) != 0:
                    data = self._infra.hub.read(self._name)
                    if data is not None:
                        channel, (timestamp, item) = data
                        self.handle(channel, timestamp, item)

                if not self.act():
                    break

                if not self._run_to_completion and self._stop_event.is_set():
                    break

            self._set_state(ActorState.SHUTTING_DOWN)
            self.shutdown()

        except Exception as e:
            logger.error("Actor %s failed with error: %s\n%s", self._name, e, traceback.format_exc())

        finally:
            self._set_state(ActorState.COMPLETED)
            self._stop_event.set()

    def setup(self) -> None:
        """
        Override this method to setup the actor by acquiring resources and then starting the main loop.
        """
        self.run()

    def handle(self, channel: ChannelID, timestamp: Timestamp, data: Any) -> None:
        """Override this method to handle the data from the subscribed channels."""
        return

    def act(self) -> bool:
        """Override this method to perform additional operations that are not triggered by any channel data.

        Return True if the actor should continue running, False if it should stop.
        """
        # the default behavior of an actor should not be to run endlessly
        if self._run_to_completion:
            return False
        return True

    def shutdown(self) -> None:
        """Override this method to perform any cleanup when the actor is shutting down."""
        pass

    def _set_state(self, new_state: ActorState) -> None:
        """Set the actor state in a thread-safe way."""
        with self._state_lock:
            self._state = new_state
