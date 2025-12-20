from fastrtc import Stream, ReplyOnPause
import numpy as np
from src.application.services.conversation_orchestrator import ConversationOrchestrator
from src.infrastructure.audio.processor import float32_to_int16, int16_to_float32
from src.core.logger import logger

def create_handler(orchestrator: ConversationOrchestrator):
    """
    Creates an async generator that handles the WebRTC audio stream.
    """
    async def handler(audio_stream):
        """
        Consumes audio from the user and produces audio from the AI.
        """
        async for audio_frame in audio_stream:
            # audio_frame is (sample_rate, audio_data_as_numpy_float32)
            orig_sr, audio_float32 = audio_frame
            
            # 1. Convert WebRTC float32 to PCM int16 for internal processing
            audio_int16_bytes = float32_to_int16(audio_float32)
            
            # 2. Pass frame to orchestrator
            await orchestrator.process_input_frame(audio_int16_bytes)
            
            # 3. Check if there is audio in the response queue to send back
            while not orchestrator.response_queue.empty():
                try:
                    ai_audio_bytes = orchestrator.response_queue.get_nowait()
                    
                    # Convert back to float32 for WebRTC (FastRTC expectation)
                    # We assume AI audio is already at a handled sample rate or we use fixed
                    ai_audio_float32 = int16_to_float32(ai_audio_bytes)
                    
                    # Yield as (sample_rate, data)
                    # Note: We use the same sample rate as input or a consistent one
                    yield (orig_sr, ai_audio_float32)
                except Exception as e:
                    logger.warning("Error yielding AI audio frame", error=str(e))
                    break
                    
    return handler
