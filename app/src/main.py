from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, Query, status
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from src.api.dependencies import get_orchestrator
from src.application.services.conversation_orchestrator import ConversationOrchestrator
from src.core.logger import setup_logging, logger

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup logic
    setup_logging()
    logger.info("Initializing HAR-228 Text-to-Voice Service...")
    yield
    # Shutdown logic
    logger.info("Shutting down service...")

app = FastAPI(
    title="HAR-228 Voice AI",
    version="1.0.0",
    description="Microservicio profesional para conversión de texto a voz con IA delegada.",
    lifespan=lifespan
)

# Enable CORS for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    text: str
    company_id: str = "default"
    response_format: str = "audio"  # "audio" or "text"

@app.post("/chat", tags=["Voz"], summary="Convertir JSON a Voz")
async def chat_to_voice_post(
    request: ChatRequest, 
    orchestrator: ConversationOrchestrator = Depends(get_orchestrator)
):
    """
    Recibe texto y company_id, realiza búsqueda RAG y devuelve audio MP3.
    """
    logger.info("Received POST request", text=request.text, company_id=request.company_id)
    return await _process_rag_to_audio(request, orchestrator)

@app.get("/chat", tags=["Voz"], summary="Convertir Parámetro a Voz")
async def chat_to_voice_get(
    text: str = Query(..., description="Texto a convertir en voz"),
    company_id: str = Query("default", description="ID de la empresa para RAG"),
    orchestrator: ConversationOrchestrator = Depends(get_orchestrator)
):
    """
    Versión GET para pruebas rápidas. Soporta company_id.
    """
    logger.info("Received GET request", text=text, company_id=company_id)
    request = ChatRequest(text=text, company_id=company_id)
    return await _process_rag_to_audio(request, orchestrator)

async def _process_rag_to_audio(request: ChatRequest, orchestrator: ConversationOrchestrator):
    # 1. Obtener prompt dinámico por empresa
    system_prompt = orchestrator.prompt_repository.get_prompt_for_company(
        request.company_id, 
        orchestrator.system_prompt
    )

    # 2. Búsqueda RAG (Búsqueda semántica con filtro de empresa)
    context = ""
    try:
        query_vector = orchestrator.embedding_provider.embed_text(request.text)
        search_results = await orchestrator.vector_store.search(
            query_vector=query_vector, 
            company_id=request.company_id,
            limit=3
        )
        if search_results:
            context = "\n".join([res.get("content", "") for res in search_results])
            logger.info("RAG Context retrieved", matches=len(search_results))
    except Exception as e:
        logger.error("RAG search failed", error=str(e))

    # 3. Enriquecer Prompt con contexto
    full_prompt = system_prompt
    if context:
        full_prompt += f"\n\nContexto relevante para esta empresa:\n{context}"

    # 4. Generar flujo LLM
    llm_history = [{"role": "user", "content": request.text}]
    text_stream = orchestrator.llm.generate_stream(llm_history, full_prompt)
    
    if request.response_format == "text":
        async def text_generator():
            async for chunk in text_stream:
                yield chunk
        return StreamingResponse(text_generator(), media_type="text/plain")

    # 5. Generar flujo Audio (TTS)
    audio_stream = orchestrator.tts.synthesize_stream(text_stream)
    return StreamingResponse(audio_stream, media_type="audio/mpeg")

@app.get("/health", tags=["Sistema"])
async def health_check():
    """Verifica el estado de salud del microservicio y sus proveedores."""
    return {
        "status": "online",
        "service": "HAR-228",
        "version": "1.0.0",
        "configurations": {
            "llm": "active",
            "tts": "active"
        }
    }

@app.get("/", include_in_schema=False)
async def root():
    return {"message": "HAR-228 Text-to-Voice API. Visit /docs for documentation."}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
