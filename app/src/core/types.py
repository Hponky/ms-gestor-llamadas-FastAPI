from dataclasses import dataclass
from enum import Enum

class SessionState(str, Enum):
    LISTENING = "listening"
    PROCESSING = "processing"
    SPEAKING = "speaking"
    IDLE = "idle"

@dataclass
class AudioFrame:
    data: bytes
    sample_rate: int
    num_channels: int
    duration_ms: float
