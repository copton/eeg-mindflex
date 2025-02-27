import threading
from typing import TYPE_CHECKING

from .hub import SubscriberID
from .types import ActorState

if TYPE_CHECKING:
    from .actor import Actor


class ActorPool:
    def __init__(self) -> None:
        self._actors: list[Actor] = []
        self._stop_event = threading.Event()
        self._main_thread_actor: Actor | None = None

    def add(self, actor: "Actor", capture_thread: bool) -> threading.Event:
        self._actors.append(actor)
        if capture_thread:
            if self._main_thread_actor:
                raise ValueError(
                    "Cannot have more than one main thread actor: "
                    f"{self._main_thread_actor.name} and {actor.name}"
                )
            self._main_thread_actor = actor

        return self._stop_event

    def start(self) -> None:
        self._stop_event.clear()
        for actor in self._actors:
            actor.start()

        if self._main_thread_actor:
            self._main_thread_actor.start()

    def stop(self) -> None:
        self._stop_event.set()
        for actor in self._actors:
            actor.join()

        if self._main_thread_actor:
            self._main_thread_actor.join()

    def wait(self) -> None:
        self._stop_event.wait()

    def get_state(self, actor_name: SubscriberID) -> ActorState:
        for actor in self._actors:
            if actor.name == actor_name:
                return actor.state
        raise ValueError(f"Actor {actor_name} not found")
