from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional
from uuid import UUID, uuid4
from enum import Enum

class SessionState(str, Enum):
    IDLE = "idle"
    LISTENING = "listening"
    PROCESSING = "processing"
    SPEAKING = "speaking"
    ERROR = "error"

@dataclass
class ChatMessage:
    """Represents a message in the conversation history."""
    role: str  # "user", "assistant", "system"
    content: str
    timestamp: datetime = field(default_factory=datetime.now)

@dataclass
class ConversationSession:
    """Represents an active AI conversation session."""
    id: UUID = field(default_factory=uuid4)
    state: SessionState = SessionState.IDLE
    history: List[ChatMessage] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)
