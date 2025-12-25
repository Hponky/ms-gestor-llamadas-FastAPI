import asyncio
import json
from typing import Optional, List, Dict
from src.domain.interfaces import (
    ILLMProvider, ITTSProvider, IVectorStore, 
    IEmbeddingProvider, IPromptRepository, ISessionRepository
)
from src.domain.entities import ChatMessage, ConversationSession
from src.application.services.tool_service import tool_manager, ToolService
from src.application.services.completeness_service import CompletenessService
from src.application.services.security_service import SecurityService
from src.core.logger import logger

class ConversationOrchestrator:
    def __init__(
        self,
        llm_provider: ILLMProvider,
        tts_provider: ITTSProvider,
        vector_store: IVectorStore,
        embedding_provider: IEmbeddingProvider,
        prompt_repository: IPromptRepository,
        session_repository: ISessionRepository,
        tool_service: ToolService = tool_manager,
        completeness_service: Optional[CompletenessService] = None,
        security_service: Optional[SecurityService] = None,
        system_prompt: str = "Eres HAR-228, un asistente de voz avanzado. Responde de forma concisa y natural.",
        memory_window: int = 10
    ):
        self.llm = llm_provider
        self.tts = tts_provider
        self.vector_store = vector_store
        self.embedding_provider = embedding_provider
        self.prompt_repository = prompt_repository
        self.session_repository = session_repository
        self.tool_service = tool_service
        self.completeness_service = completeness_service
        self.security_service = security_service
        self.system_prompt = system_prompt
        self.memory_window = memory_window
        
        self.is_processing = False
        self._current_task: Optional[asyncio.Task] = None

    async def get_chat_response_stream(self, text: str, company_id: str, session_id: str):
        """Unified method with memory, tools, and security checks."""
        
        # 0. Security Input Validation
        if self.security_service:
            is_safe, reason = self.security_service.validate_input(text)
            if not is_safe:
                async def security_rejection_stream():
                    yield reason
                return security_rejection_stream()

        # 1. Check completeness
        if self.completeness_service:
            stream = await self._handle_completeness(text)
            if stream: return stream

        # 1. Setup Session and Prompts
        session = self.session_repository.get_session(session_id) or ConversationSession()
        full_system_prompt = await self._build_full_prompt(text, company_id)
        
        # 2. Prepare History
        session.history.append(ChatMessage(role="user", content=text))
        history = [{"role": m.role, "content": m.content} for m in session.history[-self.memory_window:]]
        
        # 3. Stream logic
        return self._generate_tracked_stream(history, full_system_prompt, session, session_id)

    async def _handle_completeness(self, text: str):
        analysis = await self.completeness_service.check_completeness(text)
        if not analysis["is_complete"] and analysis["suggestion"]:
            async def clarification_stream():
                yield analysis["suggestion"]
            return clarification_stream()
        return None

    async def _build_full_prompt(self, text: str, company_id: str) -> str:
        base_prompt = self.prompt_repository.get_prompt_for_company(company_id, self.system_prompt)
        context = await self._get_rag_context(text, company_id)
        
        if self.security_service:
            # Use structured XML prompting for defense
            return self.security_service.secure_prompt_construction(base_prompt, text, context)
            
        return base_prompt if not context else f"{base_prompt}\n\nContexto:\n{context}"

    def _generate_tracked_stream(self, history: List[Dict], system_prompt: str, session: ConversationSession, session_id: str):
        tools = self.tool_service.get_tools_schema()
        
        async def track_response_stream():
            full_response_text = []
            
            async for chunk in self.llm.generate_stream(history, system_prompt, tools=tools):
                if chunk.startswith("__TOOL_CALL__:"):
                    async for sub_chunk in self._handle_tool_calls(chunk, history, system_prompt):
                        full_response_text.append(sub_chunk)
                        yield sub_chunk
                    break
                
                full_response_text.append(chunk)
                yield chunk
            
            complete_text = "".join(full_response_text)
            
            # Security: Redact PII before saving to history
            if self.security_service:
                complete_text = self.security_service.sanitize_content(complete_text)

            session.history.append(ChatMessage(role="assistant", content=complete_text))
            self.session_repository.save_session(session_id, session)

        return track_response_stream()

    async def _handle_tool_calls(self, tool_chunk: str, history: List[Dict], system_prompt: str):
        calls_data = json.loads(tool_chunk.replace("__TOOL_CALL__:", ""))
        for call in calls_data:
            name = call["function"]["name"]
            args = json.loads(call["function"]["arguments"])
            result = await self.tool_service.execute_tool(name, args)
            
            history.append({"role": "assistant", "content": None, "tool_calls": [call]})
            history.append({"role": "tool", "tool_call_id": call["id"], "name": name, "content": result})
        
        async for chunk in self.llm.generate_stream(history, system_prompt):
            yield chunk

    async def _get_rag_context(self, text: str, company_id: str) -> str:
        try:
            query_vector = self.embedding_provider.embed_text(text)
            search_results = await self.vector_store.search(query_vector, company_id, limit=3)
            return "\n".join([res.get("text", "") for res in search_results]) if search_results else ""
        except Exception as e:
            logger.error("RAG search error", error=str(e))
            return ""

    def interrupt(self):
        """Stops current processing."""
        if self._current_task and not self._current_task.done():
            self._current_task.cancel()
        self.is_processing = False
