class BaseAppException(Exception):
    """Base exception for all application errors."""
    pass

class LLMError(BaseAppException):
    """Raised when there's an error with the LLM provider."""
    pass

class TTSError(BaseAppException):
    """Raised when there's an error with the TTS provider."""
    pass

class STTError(BaseAppException):
    """Raised when there's an error with the STT provider."""
    pass

class VADError(BaseAppException):
    """Raised when there's an error in voice activity detection."""
    pass

class AudioProcessingError(BaseAppException):
    """Raised when there's an error processing audio signals."""
    pass
