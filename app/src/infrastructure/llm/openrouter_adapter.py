from typing import AsyncGenerator, List, Dict
import openai
import json
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

    async def generate_stream(
        self, 
        messages: List[Dict[str, str]], 
        system_prompt: str,
        tools: List[Dict] = None
    ) -> AsyncGenerator[str, None]:
        full_messages = [{"role": "system", "content": system_prompt}] + messages
        
        try:
            params = {
                "model": self.model,
                "messages": full_messages,
                "stream": True,
            }
            if tools:
                params["tools"] = tools

            stream = await self.client.chat.completions.create(**params)

            async for chunk in stream:
                if not chunk.choices:
                    continue
                
                delta = chunk.choices[0].delta
                
                # Check for Tool Calls (Non-streaming content)
                if hasattr(delta, 'tool_calls') and delta.tool_calls:
                    # For simplicity in this streaming context, we yield the tool call info
                    # The orchestrator will detect this and execute the tool.
                    yield f"__TOOL_CALL__:{json.dumps([tc.model_dump() for tc in delta.tool_calls])}"
                
                # Normal Text Content
                if delta.content:
                    yield delta.content
                    
        except Exception as e:
            logger.error("Error generating stream from OpenRouter", error=str(e))
            raise LLMError(f"OpenRouter error: {str(e)}")
