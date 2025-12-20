import asyncio
import edge_tts
from typing import AsyncGenerator
from src.domain.interfaces import ITTSProvider
from src.core.logger import logger
from src.core.exceptions import TTSError

class EdgeTTSAdapter(ITTSProvider):
    def __init__(self, voice: str = "es-MX-JorgeNeural"):
        self.voice = voice

    async def synthesize_stream(self, text_stream: AsyncGenerator[str, None]) -> AsyncGenerator[bytes, None]:
        """
        Receives text tokens, buffers them into sentences, and synthesizes speech.
        """
        buffer = []
        sentence_endings = {'.', '!', '?', '\n'}
        
        try:
            async for token in text_stream:
                buffer.append(token)
                
                # Check if the token ends a sentence
                if any(char in sentence_endings for char in token):
                    sentence = "".join(buffer).strip()
                    if sentence:
                        async for chunk in self._synthesize_sentence(sentence):
                            yield chunk
                        buffer = []
            
            # Synthesize any remaining text
            remaining = "".join(buffer).strip()
            if remaining:
                async for chunk in self._synthesize_sentence(remaining):
                    yield chunk
                    
        except Exception as e:
            logger.error("Error in EdgeTTS streaming", error=str(e))
            raise TTSError(f"EdgeTTS error: {str(e)}")

    async def _synthesize_sentence(self, text: str) -> AsyncGenerator[bytes, None]:
        """Synthesizes a single sentence."""
        try:
            communicate = edge_tts.Communicate(text, self.voice)
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    yield chunk["data"]
        except Exception as e:
            logger.warning("Failed to synthesize sentence", text=text, error=str(e))
