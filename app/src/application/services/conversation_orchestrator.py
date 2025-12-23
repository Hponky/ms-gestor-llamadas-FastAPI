import asyncio
import json
from typing import Optional
from src.domain.interfaces import (
    ILLMProvider, ITTSProvider, IVectorStore, 
    IEmbeddingProvider, IPromptRepository, ISessionRepository
)
from src.domain.entities import ChatMessage, ConversationSession
from src.application.services.tool_service import tool_manager, ToolService
from src.application.services.completeness_service import CompletenessService
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
        self.system_prompt = system_prompt
        self.memory_window = memory_window
        
        self.is_processing = False
        self._current_task: Optional[asyncio.Task] = None

    async def get_chat_response_stream(self, text: str, company_id: str, session_id: str):
        """
        Unified method with memory, tools, and completeness check.
        """
        # 0. Check for completeness (if service available)
        if self.completeness_service:
            analysis = await self.completeness_service.check_completeness(text)
            if not analysis["is_complete"] and analysis["suggestion"]:
                # If incomplete, we return a clarification stream
                async def clarification_stream():
                    yield analysis["suggestion"]
                return clarification_stream()

        # 1. Load Session and dynamic prompt
        session = self.session_repository.get_session(session_id) or ConversationSession()
        base_prompt = self.prompt_repository.get_prompt_for_company(company_id, self.system_prompt)
        
        # 2. RAG Search
        context = await self._get_rag_context(text, company_id)
        
        # 3. Final Prompt Composition
        full_system_prompt = base_prompt if not context else f"{base_prompt}\n\nContexto:\n{context}"
        
        # 4. Prepare History
        session.history.append(ChatMessage(role="user", content=text))
        history = [{"role": m.role, "content": m.content} for m in session.history[-self.memory_window:]]
        
        # 5. Get Tools Schema
        tools = self.tool_service.get_tools_schema()

        # 6. Generate Stream with Tool Handling
        async def track_response_stream():
            full_response_text = []
            
            async for chunk in self.llm.generate_stream(history, full_system_prompt, tools=tools):
                # Detect if the LLM is calling a tool
                if chunk.startswith("__TOOL_CALL__:"):
                    calls_data = json.loads(chunk.replace("__TOOL_CALL__:", ""))
                    
                    # Execute Tools and get results
                    for call in calls_data:
                        name = call["function"]["name"]
                        args = json.loads(call["function"]["arguments"])
                        result = await self.tool_service.execute_tool(name, args)
                        
                        # Add tool interaction to history
                        history.append({"role": "assistant", "content": None, "tool_calls": [call]})
                        history.append({"role": "tool", "tool_call_id": call["id"], "name": name, "content": result})
                    
                    # Get final response from LLM using tool results
                    async for sub_chunk in self.llm.generate_stream(history, full_system_prompt):
                        full_response_text.append(sub_chunk)
                        yield sub_chunk
                    break
                
                full_response_text.append(chunk)
                yield chunk
            
            # 7. Update Session
            complete_text = "".join(full_response_text)
            session.history.append(ChatMessage(role="assistant", content=complete_text))
            self.session_repository.save_session(session_id, session)

        return track_response_stream()

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
