from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, Query, status, File, UploadFile, Form
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
from src.api.dependencies import get_orchestrator, get_kb_service
from src.api.websockets import router as ws_router
from src.application.services.conversation_orchestrator import ConversationOrchestrator
from src.application.services.knowledge_base_service import KnowledgeBaseService
from src.core.logger import setup_logging, logger

@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    logger.info("Initializing HAR-228 Text-to-Voice Service...")
    yield
    logger.info("Shutting down service...")

app = FastAPI(
    title="HAR-228 Voice AI",
    version="1.0.0",
    description="Microservicio profesional para conversión de texto a voz con IA delegada.",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(ws_router)

# --- Schemas ---

class ChatRequest(BaseModel):
    text: str
    company_id: str = "default"
    session_id: str = "default"
    response_format: str = "audio"

class IngestRequest(BaseModel):
    text: str
    company_id: str
    metadata: dict = {}

# --- Helper Functions ---

async def _process_rag_to_audio(request: ChatRequest, orchestrator: ConversationOrchestrator):
    text_stream = await orchestrator.get_chat_response_stream(
        text=request.text, 
        company_id=request.company_id, 
        session_id=request.session_id
    )
    
    if request.response_format == "text":
        return StreamingResponse(text_stream, media_type="text/plain")

    audio_stream = orchestrator.tts.synthesize_stream(text_stream)
    return StreamingResponse(audio_stream, media_type="audio/mpeg")

# --- Endpoints ---

@app.post("/chat", tags=["Voz"])
async def chat_to_voice_post(request: ChatRequest, orch: ConversationOrchestrator = Depends(get_orchestrator)):
    return await _process_rag_to_audio(request, orch)

@app.get("/chat", tags=["Voz"])
async def chat_to_voice_get(
    text: str = Query(...),
    company_id: str = Query("default"),
    session_id: str = Query("default"),
    orch: ConversationOrchestrator = Depends(get_orchestrator)
):
    return await _process_rag_to_audio(ChatRequest(text=text, company_id=company_id, session_id=session_id), orch)

@app.post("/ingest", tags=["Admin"])
async def ingest_knowledge(request: IngestRequest, kb: KnowledgeBaseService = Depends(get_kb_service)):
    point_id = await kb.ingest_text(request.text, request.company_id, request.metadata)
    if point_id:
        return {"status": "success", "id": point_id, "message": "Conocimiento guardado."}
    return {"status": "error", "message": "Fallo al guardar."}

@app.post("/ingest/file", tags=["Admin"])
async def ingest_file(
    company_id: str = Form(...),
    source_id: str = Form(None),
    file: UploadFile = File(...),
    kb: KnowledgeBaseService = Depends(get_kb_service)
):
    content = await file.read()
    success = await kb.ingest_file(content, file.filename, company_id, source_id)
    if success:
        return {"status": "success", "message": f"Archivo {file.filename} indexado."}
    return {"status": "error", "message": "Fallo al procesar archivo."}

@app.post("/ingest/bulk", tags=["Admin"])
async def ingest_bulk(
    company_id: str = Form(...),
    source_id: str = Form(None),
    files: List[UploadFile] = File(...),
    kb: KnowledgeBaseService = Depends(get_kb_service)
):
    results = []
    for f in files:
        content = await f.read()
        success = await kb.ingest_file(content, f.filename, company_id, source_id)
        results.append({"file": f.filename, "success": success})
    return {"status": "completed", "results": results}

@app.delete("/knowledge/{company_id}", tags=["Admin"])
async def delete_knowledge(
    company_id: str,
    point_id: str = Query(None),
    source_id: str = Query(None),
    source: str = Query(None),
    kb: KnowledgeBaseService = Depends(get_kb_service)
):
    success = await kb.delete_knowledge(company_id, point_id, source_id, source)
    return {"status": "success" if success else "error"}

@app.get("/health", tags=["Sistema"])
async def health_check():
    return {"status": "online", "service": "HAR-228"}

@app.get("/", include_in_schema=False)
async def root():
    return {"message": "HAR-228 API. Visit /docs"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
