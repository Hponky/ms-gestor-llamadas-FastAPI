from dataclasses import dataclass, field
from datetime import datetime

@dataclass
class DomainEvent:
    timestamp: datetime = field(default_factory=datetime.now)

@dataclass
class TextGenerated(DomainEvent):
    session_id: str
    text: str
    role: str
