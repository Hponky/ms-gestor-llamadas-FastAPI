from functools import lru_cache
from src.infrastructure.llm.openrouter_adapter import OpenRouterLLMAdapter
from src.infrastructure.tts.edge_tts_adapter import EdgeTTSAdapter
from src.infrastructure.embeddings.fastembed_adapter import FastEmbedAdapter
from src.application.services.conversation_orchestrator import ConversationOrchestrator
from src.core.config import settings

@lru_cache()
def get_llm_service():
    """
    Dependency injection for LLM provider.
    Scalable factory to support multiple providers.
    """
    provider = settings.LLM_PROVIDER.lower()
    
    if provider == "openrouter":
        return OpenRouterLLMAdapter()
    elif provider == "openai":
        # Placeholder for future implementation
        # from src.infrastructure.llm.openai_adapter import OpenAIAdapter
        # return OpenAIAdapter()
        raise NotImplementedError("OpenAI provider not yet implemented. Use 'openrouter'.")
    elif provider == "gemini":
        # Placeholder for future implementation
        raise NotImplementedError("Gemini provider not yet implemented. Use 'openrouter'.")
    else:
        raise ValueError(f"Unsupported LLM provider: {provider}")

@lru_cache()
def get_tts_service():
    """Dependency injection for TTS provider."""
    return EdgeTTSAdapter()

@lru_cache()
def get_embedding_service():
    """
    Dependency injection for Embedding provider.
    Scalable factory to support multiple providers.
    """
    provider = settings.EMBEDDING_PROVIDER.lower()
    
    if provider == "fastembed":
        return FastEmbedAdapter()
    elif provider == "openai":
        raise NotImplementedError("OpenAI Embedding provider not yet implemented.")
    else:
        raise ValueError(f"Unsupported Embedding provider: {provider}")

@lru_cache()
def get_orchestrator():
    """Dependency injection for Conversation Orchestrator."""
    return ConversationOrchestrator(
        llm_provider=get_llm_service(),
        tts_provider=get_tts_service()
    )
