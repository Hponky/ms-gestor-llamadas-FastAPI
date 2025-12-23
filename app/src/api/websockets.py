import json
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from src.api.dependencies import get_orchestrator
from src.application.services.conversation_orchestrator import ConversationOrchestrator
from src.core.logger import logger

router = APIRouter()

@router.websocket("/ws/chat/{session_id}")
async def websocket_endpoint(
    websocket: WebSocket, 
    session_id: str,
    company_id: str = "default",
    orch: ConversationOrchestrator = Depends(get_orchestrator)
):
    """
    Real-time WebSocket for Voice/Chat.
    Protocol:
    - Receive: { "type": "text", "content": "..." } or { "type": "interrupt" }
    - Send: { "type": "text", "content": "..." } or Binary (Audio)
    """
    await websocket.accept()
    logger.info(f"WebSocket connected: {session_id}")
    
    try:
        while True:
            # Wait for message from client
            message = await websocket.receive_text()
            data = json.loads(message)
            
            msg_type = data.get("type")
            
            if msg_type == "interrupt":
                orch.interrupt()
                await websocket.send_json({"type": "info", "content": "Assistant interrupted"})
                continue
            
            if msg_type == "text":
                content = data.get("content", "")
                
                # Start processing the response
                # Note: For real calls, we stream the audio back as binary chunks
                text_stream = await orch.get_chat_response_stream(
                    text=content,
                    company_id=company_id,
                    session_id=session_id
                )
                
                audio_stream = orch.tts.synthesize_stream(text_stream)
                
                async for audio_chunk in audio_stream:
                    # Check if client disconnected or interrupted during generation
                    # (Simplified for this version)
                    await websocket.send_bytes(audio_chunk)
                
                await websocket.send_json({"type": "end_of_stream"})

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected: {session_id}")
    except Exception as e:
        logger.error("WebSocket error", error=str(e))
        await websocket.close()
