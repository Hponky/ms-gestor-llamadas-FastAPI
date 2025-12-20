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
        Receives text tokens, buffers them into sentences, and synthesizes speech in MP3 format.
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
        """Synthesizes a single sentence in MP3 format."""
        import re
        # JorgeNeural is sensitive to special characters. We allow only alphanumeric,
        # Spanish accents, and basic punctuation. Emojis and others are removed.
        clean_text = re.sub(r'[^a-zA-Z0-9áéíóúÁÉÍÓÚñÑüÜ\s\.,!\?¿¡\(\)":;-]', '', text).strip()
        
        if not clean_text or len(clean_text) < 1:
            return

        try:
            communicate = edge_tts.Communicate(clean_text, self.voice)
            chunk_count = 0
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    chunk_count += 1
                    yield chunk["data"]
            
            if chunk_count > 0:
                logger.info("Sentence synthesis complete", text=clean_text[:30] + "...", chunks=chunk_count)
        except Exception as e:
            # We use repr(e) to avoid potential encoding issues with str(e) in some environments
            logger.warning("Failed to synthesize sentence", error=repr(e))
