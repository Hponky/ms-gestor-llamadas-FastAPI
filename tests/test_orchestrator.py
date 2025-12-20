import pytest
from unittest.mock import AsyncMock, MagicMock
from src.application.services.conversation_orchestrator import ConversationOrchestrator
from src.domain.entities import SessionState

@pytest.mark.asyncio
async def test_orchestrator_handle_text_input():
    # Mock LLM and TTS
    llm_mock = MagicMock()
    # generate_stream is an async generator
    async def mock_gen(*args, **kwargs):
        yield "Respuesta"
        yield " de"
        yield " prueba"
    llm_mock.generate_stream.side_effect = mock_gen
    
    tts_mock = MagicMock()
    # synthesize_stream is an async generator
    async def mock_tts_gen(*args, **kwargs):
        yield b"audio_chunk_1"
        yield b"audio_chunk_2"
    tts_mock.synthesize_stream.side_effect = mock_tts_gen
    
    orchestrator = ConversationOrchestrator(llm_provider=llm_mock, tts_provider=tts_mock)
    
    # Execute handle text input
    await orchestrator.handle_text_input("Hola")
    
    # Wait a bit for the background task to finish (since orchestrator uses asyncio.create_task)
    # In a real scenario we might want to await the task or use a more synchronous approach for tests
    if orchestrator._current_task:
        await orchestrator._current_task
    
    # Assertions
    assert len(orchestrator.session.history) == 1
    assert orchestrator.session.history[0].content == "Hola"
    
    # Check if we got audio in the queue
    assert orchestrator.response_queue.qsize() == 2
    chunk1 = await orchestrator.response_queue.get()
    assert chunk1 == b"audio_chunk_1"

@pytest.mark.asyncio
async def test_orchestrator_interrupt():
    llm_mock = MagicMock()
    tts_mock = MagicMock()
    orchestrator = ConversationOrchestrator(llm_provider=llm_mock, tts_provider=tts_mock)
    
    # Mock a running task
    mock_task = AsyncMock()
    orchestrator._current_task = mock_task
    orchestrator.is_processing = True
    
    # Fill queue
    await orchestrator.response_queue.put(b"data")
    
    await orchestrator.interrupt()
    
    assert orchestrator.response_queue.empty()
    assert orchestrator.is_processing is False
    assert orchestrator.session.state == SessionState.IDLE
    mock_task.cancel.assert_called_once()
