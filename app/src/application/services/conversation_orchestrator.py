import asyncio
from typing import Optional, List
from src.domain.interfaces import ILLMProvider, ITTSProvider, IVectorStore, IEmbeddingProvider, IPromptRepository, ISessionRepository
from src.domain.entities import ChatMessage, ConversationSession, SessionState
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
        system_prompt: str = "Eres HAR-228, un asistente de voz avanzado. Responde de forma concisa y natural.",
        memory_window: int = 10
    ):
        self.llm = llm_provider
        self.tts = tts_provider
        self.vector_store = vector_store
        self.embedding_provider = embedding_provider
        self.prompt_repository = prompt_repository
        self.session_repository = session_repository
        self.system_prompt = system_prompt
        self.memory_window = memory_window
        
        # Local state for streaming (if used via handle_text_input)
        self.response_queue = asyncio.Queue()
        self.is_processing = False
        self._current_task: Optional[asyncio.Task] = None

    async def get_chat_response_stream(self, text: str, company_id: str, session_id: str):
        """
        Unified method to get a RAG-enhanced response stream with memory.
        """
        # 1. Load or Create Session
        session = self.session_repository.get_session(session_id) or ConversationSession()
        
        # 2. Get Dynamic Prompt
        base_prompt = self.prompt_repository.get_prompt_for_company(company_id, self.system_prompt)
        
        # 3. RAG Search
        context = ""
        try:
            query_vector = self.embedding_provider.embed_text(text)
            search_results = await self.vector_store.search(query_vector, company_id, limit=3)
            if search_results:
                context = "\n".join([res.get("text", "") for res in search_results])
        except Exception as e:
            logger.error("RAG search error", error=str(e))

        # 4. Final Prompt Composition
        full_system_prompt = base_prompt
        if context:
            full_system_prompt += f"\n\nContexto de la empresa:\n{context}"
        
        # 5. Prepare History (Memory Window)
        session.history.append(ChatMessage(role="user", content=text))
        history_to_send = [{"role": m.role, "content": m.content} for m in session.history[-self.memory_window:]]
        
        # 6. Generate LLM Stream
        full_response_text = []

        async def track_response_stream():
            async for chunk in self.llm.generate_stream(history_to_send, full_system_prompt):
                full_response_text.append(chunk)
                yield chunk
            
            # 7. Update and Save Session after stream completion
            complete_text = "".join(full_response_text)
            session.history.append(ChatMessage(role="assistant", content=complete_text))
            self.session_repository.save_session(session_id, session)

        return track_response_stream()

    async def handle_text_input(self, text: str, company_id: str = "default", session_id: str = "default"):
        """
        Legacy/Streaming handler using the unified logic.
        """
        if self.is_processing:
            await self.interrupt()
        
        self.is_processing = True
        self._current_task = asyncio.create_task(self._process_turn_v2(text, company_id, session_id))

    async def _process_turn_v2(self, text: str, company_id: str, session_id: str):
        try:
            text_stream = await self.get_chat_response_stream(text, company_id, session_id)
            audio_stream = self.tts.synthesize_stream(text_stream)
            
            async for audio_chunk in audio_stream:
                await self.response_queue.put(audio_chunk)
        except Exception as e:
            logger.error("Turn processing error", error=str(e))
        finally:
            self.is_processing = False

    async def interrupt(self):
        """
        Stops current processing and clears response queue.
        """
        logger.info("Interrupting current process...")
        if self._current_task and not self._current_task.done():
            self._current_task.cancel()
            await self._current_task
        
        # Clear the response queue
        while not self.response_queue.empty():
            try:
                self.response_queue.get_nowait()
            except asyncio.QueueEmpty:
                break
        
        self.is_processing = False
