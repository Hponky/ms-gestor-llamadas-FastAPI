from src.domain.interfaces import ISTTProvider
from src.core.logger import logger

class MockSTTAdapter(ISTTProvider):
    async def transcribe(self, audio: bytes) -> str:
        """
        Returns a mock transcription for testing purposes.
        """
        logger.info("Mock STT received audio", size=len(audio))
        return "Hola, esta es una transcripción de prueba."
