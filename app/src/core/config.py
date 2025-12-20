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
    
    # OpenRouter (LLM)
    OPENROUTER_API_KEY: str
    OPENROUTER_MODEL: str = "mistralai/devstral-2512:free"
    OPENROUTER_BASE_URL: str = "https://openrouter.ai/api/v1"
    
    # Provider Settings
    STT_PROVIDER: str = "mock"
    TTS_PROVIDER: str = "edge_tts"
    
    # Audio Settings
    SAMPLE_RATE_VAD: int = 16000
    SAMPLE_RATE_WEBRTC: int = 48000
    
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

settings = Settings()
