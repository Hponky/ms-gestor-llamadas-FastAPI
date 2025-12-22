from typing import Optional, Dict
from src.domain.interfaces import ISessionRepository
from src.domain.entities import ConversationSession
from src.core.logger import logger

class InMemorySessionRepository(ISessionRepository):
    def __init__(self):
        # Dict mapping session_id to ConversationSession object
        self._sessions: Dict[str, ConversationSession] = {}

    def get_session(self, session_id: str) -> Optional[ConversationSession]:
        session = self._sessions.get(session_id)
        if session:
            logger.debug("Session retrieved from memory", session_id=session_id)
        return session

    def save_session(self, session_id: str, session: ConversationSession) -> None:
        self._sessions[session_id] = session
        logger.debug("Session saved to memory", session_id=session_id)

    def delete_session(self, session_id: str) -> None:
        if session_id in self._sessions:
            del self._sessions[session_id]
            logger.info("Session deleted from memory", session_id=session_id)
