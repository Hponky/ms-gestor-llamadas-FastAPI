import json
import redis
from typing import Optional
from src.domain.interfaces import ISessionRepository
from src.domain.entities import ConversationSession, ChatMessage
from src.core.config import settings
from src.core.logger import logger

class RedisSessionRepository(ISessionRepository):
    def __init__(self):
        try:
            self.client = redis.Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                password=settings.REDIS_PASSWORD,
                decode_responses=True
            )
            self.ttl = settings.REDIS_TTL
            logger.info("Redis Session Repository initialized", host=settings.REDIS_HOST)
        except Exception as e:
            logger.error("Failed to connect to Redis", error=str(e))
            raise

    def get_session(self, session_id: str) -> Optional[ConversationSession]:
        try:
            data = self.client.get(f"session:{session_id}")
            if not data:
                return None
            
            # Reconstruct session from JSON
            session_dict = json.loads(data)
            session = ConversationSession()
            session.history = [
                ChatMessage(role=m["role"], content=m["content"]) 
                for m in session_dict.get("history", [])
            ]
            return session
        except Exception as e:
            logger.error("Error retrieving session from Redis", error=str(e))
            return None

    def save_session(self, session_id: str, session: ConversationSession) -> None:
        try:
            # Prepare data for JSON serialization
            data = {
                "history": [
                    {"role": m.role, "content": m.content} 
                    for m in session.history
                ]
            }
            self.client.setex(
                f"session:{session_id}",
                self.ttl,
                json.dumps(data)
            )
        except Exception as e:
            logger.error("Error saving session to Redis", error=str(e))

    def delete_session(self, session_id: str) -> None:
        try:
            self.client.delete(f"session:{session_id}")
        except Exception as e:
            logger.error("Error deleting session from Redis", error=str(e))
