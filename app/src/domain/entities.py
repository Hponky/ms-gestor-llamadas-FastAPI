from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional
from uuid import UUID, uuid4
from src.core.types import SessionState

@dataclass
class AudioChunk:
    """Represents a segment of audio data."""
    content: bytes
    sample_rate: int
    timestamp: datetime = field(default_factory=datetime.now)

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

@dataclass
class AIResponse:
    """Represents the output from the LLM."""
    text: str
    model: str
    usage: Optional[dict] = None
