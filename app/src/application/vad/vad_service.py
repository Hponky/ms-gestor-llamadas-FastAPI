from src.core.logger import logger
from src.infrastructure.vad.silero_helper import SileroVADHelper
from src.core.config import settings

class VADService:
    def __init__(self, vad_helper: SileroVADHelper):
        self.vad_helper = vad_helper
        self.silence_threshold_ms = 600  # Time to wait before triggering STT
        self.frame_duration_ms = 20    # Standard WebRTC frame duration
        self.silence_counter = 0

    def is_speech_detected(self, audio_chunk: bytes) -> bool:
        """
        Determines if there is speech and updates the silence counter.
        """
        is_speech = self.vad_helper.is_speech(audio_chunk)
        
        if is_speech:
            self.silence_counter = 0
            return True
        else:
            self.silence_counter += self.frame_duration_ms
            return False

    def should_trigger_response(self) -> bool:
        """
        Returns True if the accumulated silence exceeds the threshold.
        """
        return self.silence_counter >= self.silence_threshold_ms

    def reset(self):
        """Resets the silence counter."""
        self.silence_counter = 0
