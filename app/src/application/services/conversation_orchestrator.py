import asyncio
from typing import Optional, List
from src.domain.interfaces import ILLMProvider, ITTSProvider, IVectorStore, IEmbeddingProvider, IPromptRepository
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
        system_prompt: str = "Eres HAR-228, un asistente de voz avanzado. Responde de forma concisa y natural."
    ):
        self.llm = llm_provider
        self.tts = tts_provider
        self.vector_store = vector_store
        self.embedding_provider = embedding_provider
        self.prompt_repository = prompt_repository
        self.system_prompt = system_prompt
        
        self.session = ConversationSession()
        self.response_queue = asyncio.Queue()
        self.is_processing = False
        self._current_task: Optional[asyncio.Task] = None

    async def handle_text_input(self, text: str):
        """
        Receives text, generates LLM response and synthesizes it to the queue.
        Suitable for WebRTC / WebSocket streaming output.
        """
        if self.is_processing:
            await self.interrupt()
        
        self.is_processing = True
        self.session.state = SessionState.PROCESSING
        
        # Add to history
        self.session.history.append(ChatMessage(role="user", content=text))
        
        # Start the processing turn
        self._current_task = asyncio.create_task(self._process_turn())

    async def _process_turn(self):
        """
        Internal loop: LLM -> TTS -> Queue
        """
        try:
            self.session.state = SessionState.SPEAKING
            
            # Convert history to LLM format
            llm_history = [{"role": msg.role, "content": msg.content} for msg in self.session.history]
            
            # Prepare streaming pipeline
            text_stream = self.llm.generate_stream(llm_history, self.system_prompt)
            audio_stream = self.tts.synthesize_stream(text_stream)
            
            async for audio_chunk in audio_stream:
                await self.response_queue.put(audio_chunk)
            
        except asyncio.CancelledError:
            logger.info("Turn cancelled.")
            raise
        except Exception as e:
            logger.error("Error in orchestrator processing", error=str(e))
        finally:
            self.is_processing = False
            self.session.state = SessionState.IDLE

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
        self.session.state = SessionState.IDLE
