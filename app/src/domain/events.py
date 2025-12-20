from dataclasses import dataclass
from datetime import datetime

@dataclass
class DomainEvent:
    timestamp: datetime = datetime.now()

@dataclass
class AudioReceived(DomainEvent):
    session_id: str
    duration_ms: float

@dataclass
class TextGenerated(DomainEvent):
    session_id: str
    text: str
    role: str
