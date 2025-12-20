from functools import lru_cache
from src.infrastructure.llm.openrouter_adapter import OpenRouterLLMAdapter
from src.infrastructure.tts.edge_tts_adapter import EdgeTTSAdapter
from src.infrastructure.stt.mock_stt_adapter import MockSTTAdapter
from src.infrastructure.vad.silero_helper import get_vad_model
from src.core.config import settings

@lru_cache()
def get_llm_service():
    """Dependency injection for LLM provider."""
    return OpenRouterLLMAdapter()

@lru_cache()
def get_tts_service():
    """Dependency injection for TTS provider."""
    return EdgeTTSAdapter()

@lru_cache()
def get_stt_service():
    """Dependency injection for STT provider."""
    # Choice between providers can be based on settings
    if settings.STT_PROVIDER == "mock":
        return MockSTTAdapter()
    # Placeholder for WhisperAPI / Groq
    return MockSTTAdapter()

@lru_cache()
def get_vad_service():
    """Dependency injection for VAD helper."""
    return get_vad_model()
