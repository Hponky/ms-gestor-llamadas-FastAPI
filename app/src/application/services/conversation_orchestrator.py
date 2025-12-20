import asyncio
from typing import Optional, List
from src.domain.interfaces import ILLMProvider, ISTTProvider, ITTSProvider
from src.application.vad.vad_service import VADService
from src.domain.entities import ChatMessage, ConversationSession
from src.core.logger import logger
from src.core.types import SessionState

class ConversationOrchestrator:
    def __init__(
        self,
        llm_provider: ILLMProvider,
        stt_provider: ISTTProvider,
        tts_provider: ITTSProvider,
        vad_service: VADService,
        system_prompt: str = "Eres HAR-228, un asistente de voz avanzado. Responde de forma concisa y natural."
    ):
        self.llm = llm_provider
        self.stt = stt_provider
        self.tts = tts_provider
        self.vad = vad_service
        self.system_prompt = system_prompt
        
        self.session = ConversationSession()
        self.audio_buffer = bytearray()
        self.response_queue = asyncio.Queue()
        self.is_processing = False
        self._current_task: Optional[asyncio.Task] = None

    async def process_input_frame(self, audio_frame: bytes):
        """
        Main entry point for audio frames from WebRTC.
        """
        # 1. Check for speech
        is_speech = self.vad.is_speech_detected(audio_frame)
        
        if is_speech:
            # If the user speaks while the AI is responding, interrupt the AI
            if self.session.state == SessionState.SPEAKING or self.is_processing:
                await self.interrupt()
            
            self.session.state = SessionState.LISTENING
            self.audio_buffer.extend(audio_frame)
        else:
            # If we were listening and silence is detected, check if we should trigger response
            if self.session.state == SessionState.LISTENING:
                if self.vad.should_trigger_response():
                    if len(self.audio_buffer) > 0:
                        # Start background task to handle the turn
                        self.is_processing = True
                        task_buffer = bytes(self.audio_buffer)
                        self.audio_buffer.clear()
                        self.vad.reset()
                        self._current_task = asyncio.create_task(self._handle_turn(task_buffer))
                    else:
                        self.session.state = SessionState.IDLE

    async def _handle_turn(self, audio_data: bytes):
        """
        Orchestrates STT -> LLM -> TTS in a background task.
        """
        try:
            self.session.state = SessionState.PROCESSING
            logger.info("Processing speech turn...")
            
            # 1. STT
            text_in = await self.stt.transcribe(audio_data)
            if not text_in or len(text_in.strip()) < 2:
                logger.info("No valid text transcribed, ignoring turn.")
                return

            logger.info("User said:", text=text_in)
            self.session.history.append(ChatMessage(role="user", content=text_in))
            
            # 2. LLM -> TTS Pipe
            self.session.state = SessionState.SPEAKING
            
            # Convert history to LLM format
            llm_history = [{"role": msg.role, "content": msg.content} for msg in self.session.history]
            
            # Prepare streaming pipeline
            text_stream = self.llm.generate_stream(llm_history, self.system_prompt)
            audio_stream = self.tts.synthesize_stream(text_stream)
            
            async for audio_chunk in audio_stream:
                await self.response_queue.put(audio_chunk)
            
        except asyncio.CancelledError:
            logger.info("Conversation turn cancelled (Interruption).")
            raise
        except Exception as e:
            logger.error("Error in conversation orchestrator", error=str(e))
        finally:
            self.is_processing = False
            if self.session.state != SessionState.IDLE:
                 self.session.state = SessionState.IDLE

    def interrupt(self):
        """
        Stops current processing and clears response queue.
        """
        logger.info("Interrupting current AI response...")
        if self._current_task and not self._current_task.done():
            self._current_task.cancel()
        
        # Clear the response queue
        while not self.response_queue.empty():
            try:
                self.response_queue.get_nowait()
            except asyncio.QueueEmpty:
                break
        
        self.is_processing = False
        self.session.state = SessionState.IDLE
        self.audio_buffer.clear()
        self.vad.reset()
