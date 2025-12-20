import numpy as np
from scipy import signal
from src.core.exceptions import AudioProcessingError

def float32_to_int16(audio_float32: np.ndarray) -> bytes:
    """
    Converts audio from WebRTC (float -1.0 to 1.0) to PCM 16-bit bytes.
    """
    try:
        # Clip to ensure it's within range before conversion
        audio_int16 = (np.clip(audio_float32, -1.0, 1.0) * 32767).astype(np.int16)
        return audio_int16.tobytes()
    except Exception as e:
        raise AudioProcessingError(f"Error converting float32 to int16: {str(e)}")

def int16_to_float32(audio_bytes: bytes) -> np.ndarray:
    """
    Converts PCM 16-bit bytes to float32 (-1.0 to 1.0).
    """
    try:
        audio_int16 = np.frombuffer(audio_bytes, dtype=np.int16)
        return audio_int16.astype(np.float32) / 32767.0
    except Exception as e:
        raise AudioProcessingError(f"Error converting int16 to float32: {str(e)}")

def resample_audio(audio_data: np.ndarray, orig_sr: int, target_sr: int) -> np.ndarray:
    """
    Resamples audio from orig_sr to target_sr.
    """
    if orig_sr == target_sr:
        return audio_data
    
    try:
        num_samples = int(len(audio_data) * target_sr / orig_sr)
        return signal.resample(audio_data, num_samples)
    except Exception as e:
        raise AudioProcessingError(f"Error resampling audio: {str(e)}")
