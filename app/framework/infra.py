from dataclasses import dataclass

from .hub import Channel, Hub
from .model import Eeg, MedianEeg, Packet, Quality, Raw
from .pool import ActorPool
from .timer import Timer


@dataclass
class ActorInfrastructure:
    hub: Hub
    pool: ActorPool
    timer: Timer
    raw_channel: Channel[Raw]
    eeg_channel: Channel[Eeg]
    quality_channel: Channel[Quality]
    packet_channel: Channel[Packet]
    median_eeg_channel: Channel[MedianEeg]
