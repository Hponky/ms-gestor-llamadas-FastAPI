from enum import Enum
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict

class AppEnv(str, Enum):
    DEVELOPMENT = "development"
    PRODUCTION = "production"
    TESTING = "testing"

class Settings(BaseSettings):
    # App
    APP_ENV: AppEnv = AppEnv.DEVELOPMENT
    LOG_LEVEL: str = "INFO"
    
    # Provider Settings
    LLM_PROVIDER: str = "openrouter"  # options: openrouter, openai, gemini, deepseek
    TTS_PROVIDER: str = "edge_tts"
    EMBEDDING_PROVIDER: str = "fastembed"  # options: fastembed, openai
    VECTOR_STORE_PROVIDER: str = "qdrant"  # options: qdrant, pgvector (future)
    
    # Qdrant Settings
    QDRANT_URL: str = "http://localhost:6333"
    QDRANT_API_KEY: Optional[str] = None
    QDRANT_COLLECTION: str = "kb_har_228"
    
    # Embedding Model Settings
    EMBEDDING_MODEL: str = "intfloat/multilingual-e5-small"
    
    # OpenRouter Settings
    OPENROUTER_API_KEY: Optional[str] = None
    OPENROUTER_MODEL: str = "mistralai/devstral-2512:free"
    OPENROUTER_BASE_URL: str = "https://openrouter.ai/api/v1"
    
    # OpenAI Settings (Direct)
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_MODEL: str = "gpt-4o"
    
    # Gemini Settings (Direct)
    GEMINI_API_KEY: Optional[str] = None
    GEMINI_MODEL: str = "gemini-3-pro"
    
    model_config = SettingsConfigDict(
        env_file=".env", 
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
