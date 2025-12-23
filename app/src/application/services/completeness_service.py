from typing import Dict
from src.domain.interfaces import ILLMProvider
from src.core.logger import logger

class CompletenessService:
    """
    Analyzes if a text input represents a complete thought or an interrupted phrase.
    Crucial for slow speakers in voice calls.
    """
    def __init__(self, llm: ILLMProvider):
        self.llm = llm

    async def check_completeness(self, text: str) -> Dict[str, any]:
        """
        Asks a fast model if the phrase is complete.
        Returns: { 'is_complete': bool, 'suggestion': str }
        """
        if len(text.split()) > 15: # Heuristic: Long phrases are likely complete enough
            return {"is_complete": True, "suggestion": None}

        prompt = (
            "Analiza si la siguiente frase de un usuario en una llamada está incompleta o si tiene sentido por sí sola.\n"
            "Frase: \"{text}\"\n"
            "Responde únicamente en formato JSON: {{\"completa\": bool, \"confirmacion\": \"frase para confirmar si eso era lo que quería decir\"}}\n"
            "Si está completa, confirmacion debe ser null."
        ).format(text=text)

        try:
            # We use a non-streaming call for this small analysis
            response_gen = self.llm.generate_stream([], prompt)
            response_text = ""
            async for chunk in response_gen:
                response_text += chunk
            
            import json
            # Basic cleaning in case of markdown blocks
            clean_json = response_text.replace("```json", "").replace("```", "").strip()
            data = json.loads(clean_json)
            
            return {
                "is_complete": data.get("completa", True),
                "suggestion": data.get("confirmacion")
            }
        except Exception as e:
            logger.error("Error checking completeness", error=str(e))
            return {"is_complete": True, "suggestion": None}
