from typing import AsyncGenerator, List, Dict
import openai
from src.domain.interfaces import ILLMProvider
from src.core.config import settings
from src.core.logger import logger
from src.core.exceptions import LLMError

class OpenRouterLLMAdapter(ILLMProvider):
    def __init__(self):
        self.client = openai.AsyncOpenAI(
            base_url=settings.OPENROUTER_BASE_URL,
            api_key=settings.OPENROUTER_API_KEY,
            default_headers={
                "HTTP-Referer": "https://github.com/Hponky/ms-gestor-llamadas",
                "X-Title": "HAR-228 Voice AI"
            }
        )
        self.model = settings.OPENROUTER_MODEL

    async def generate_stream(self, messages: List[Dict[str, str]], system_prompt: str) -> AsyncGenerator[str, None]:
        full_messages = [{"role": "system", "content": system_prompt}] + messages
        
        try:
            stream = await self.client.chat.completions.create(
                model=self.model,
                messages=full_messages,
                stream=True
            )

            async for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
        except Exception as e:
            logger.error("Error generating stream from OpenRouter", error=str(e))
            raise LLMError(f"OpenRouter error: {str(e)}")
