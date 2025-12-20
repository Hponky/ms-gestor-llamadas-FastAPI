from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastrtc import Stream, WebRTCConfig
from src.api.dependencies import get_orchestrator
from src.infrastructure.webrtc.stream_handler import create_handler
from src.core.logger import setup_logging, logger

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup logic
    setup_logging()
    logger.info("Initializing HAR-228 Voice AI Service...")
    yield
    # Shutdown logic
    logger.info("Shutting down service...")

app = FastAPI(
    title="HAR-228 Voice AI",
    description="Microservicio de voz a voz en tiempo real usando WebRTC",
    lifespan=lifespan
)

# Initialize the Stream
# FastRTC handles most of the WebRTC complexity
stream = Stream(
    handler=create_handler(get_orchestrator()),
    mode="send-receive",  # Full duplex: send audio, receive audio
    modality="audio",
    additional_outputs_per_input=10, # Allow multiple output frames per input frame
)

# Mount the stream to FastAPI
# This adds the WebRTC endpoints and a built-in UI at the mount path
stream.mount(path="/conversation", app=app)

@app.get("/")
async def health_check():
    return {
        "status": "online",
        "service": "HAR-228",
        "endpoints": {
            "webrtc": "/conversation",
            "docs": "/docs"
        }
    }

if __name__ == "__main__":
    import uvicorn
    # En desarrollo local: uvicorn src.main:app --reload
    uvicorn.run(app, host="0.0.0.0", port=8000)
