import asyncio
import os
import sys
from pathlib import Path

# Add app to path
sys.path.append(str(Path(__file__).parent.parent / "app"))

from src.infrastructure.llm.openrouter_adapter import OpenRouterLLMAdapter
from src.infrastructure.tts.edge_tts_adapter import EdgeTTSAdapter
from src.core.config import settings

async def test_llm():
    print("\n--- Testing OpenRouter LLM ---")
    if not settings.OPENROUTER_API_KEY or "sk-or" not in settings.OPENROUTER_API_KEY:
        print("❌ Skip: OPENROUTER_API_KEY not set correctly.")
        return

    adapter = OpenRouterLLMAdapter()
    messages = [{"role": "user", "content": "Hola, ¿quién eres?"}]
    print("AI Response: ", end="", flush=True)
    async for chunk in adapter.generate_stream(messages, "Di que eres HAR-228."):
        print(chunk, end="", flush=True)
    print("\n✅ LLM check complete.")

async def test_tts():
    print("\n--- Testing Edge-TTS ---")
    adapter = EdgeTTSAdapter()
    async def mock_text_stream():
        yield "Hola, soy una prueba de voz."
        yield " El sistema funciona correctamente."

    print("Synthesizing...")
    audio_received = False
    async for chunk in adapter.synthesize_stream(mock_text_stream()):
        if len(chunk) > 0:
            audio_received = True
            break
    
    if audio_received:
        print("✅ TTS check complete. Received audio data.")
    else:
        print("❌ TTS check failed. No audio received.")

async def main():
    print("Starting integration tests for HAR-228 adapters...")
    await test_llm()
    await test_tts()
    print("\nTests finished.")

if __name__ == "__main__":
    asyncio.run(main())
