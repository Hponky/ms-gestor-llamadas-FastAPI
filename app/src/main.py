from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, Query, status, File, UploadFile, Form
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
from src.api.dependencies import get_orchestrator
from src.application.services.conversation_orchestrator import ConversationOrchestrator
from src.application.services.document_processor import DocumentProcessor
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
    session_id: str = "default"
    response_format: str = "audio"  # "audio" or "text"

@app.post("/chat", tags=["Voz"], summary="Convertir JSON a Voz")
async def chat_to_voice_post(
    request: ChatRequest, 
    orchestrator: ConversationOrchestrator = Depends(get_orchestrator)
):
    """
    Recibe texto, company_id y session_id. Realiza búsqueda RAG y mantiene contexto de sesión.
    """
    logger.info("Received POST request", text=request.text, company_id=request.company_id, session_id=request.session_id)
    return await _process_rag_to_audio(request, orchestrator)

@app.get("/chat", tags=["Voz"], summary="Convertir Parámetro a Voz")
async def chat_to_voice_get(
    text: str = Query(..., description="Texto a convertir en voz"),
    company_id: str = Query("default", description="ID de la empresa para RAG"),
    session_id: str = Query("default", description="ID de sesión para mantener contexto"),
    orchestrator: ConversationOrchestrator = Depends(get_orchestrator)
):
    """
    Versión GET para pruebas rápidas. Soporta company_id y session_id.
    """
    logger.info("Received GET request", text=text, company_id=company_id)
    request = ChatRequest(text=text, company_id=company_id, session_id=session_id)
    return await _process_rag_to_audio(request, orchestrator)

async def _process_rag_to_audio(request: ChatRequest, orchestrator: ConversationOrchestrator):
    # Get unified Text Stream from Orchestrator (Handles RAG + Session Memory)
    text_stream = await orchestrator.get_chat_response_stream(
        text=request.text, 
        company_id=request.company_id, 
        session_id=request.session_id
    )
    
    if request.response_format == "text":
        return StreamingResponse(text_stream, media_type="text/plain")

    # Generate Audio Stream (TTS)
    audio_stream = orchestrator.tts.synthesize_stream(text_stream)
    return StreamingResponse(audio_stream, media_type="audio/mpeg")

class IngestRequest(BaseModel):
    text: str
    company_id: str
    metadata: dict = {}

@app.post("/ingest", tags=["Admin"], summary="Añadir Conocimiento a la RAG")
async def ingest_knowledge(
    request: IngestRequest,
    orchestrator: ConversationOrchestrator = Depends(get_orchestrator)
):
    """
    Convierte texto en vectores y lo guarda en la base de datos de la empresa.
    Si envías un 'id' en el metadata, se realizará un Upsert (Actualización).
    """
    import uuid
    point_id = request.metadata.get("id", str(uuid.uuid4()))
    
    # 1. Generar Vector
    vector = orchestrator.embedding_provider.embed_text(request.text)
    
    # 2. Preparar Payload
    payload = request.metadata.copy()
    payload["text"] = request.text
    payload["company_id"] = request.company_id
    
    # 3. Guardar en Vector Store
    success = await orchestrator.vector_store.upsert([{
        "id": point_id,
        "vector": vector,
        "payload": payload
    }])
    
    if success:
        return {"status": "success", "id": point_id, "message": "Conocimiento guardado/actualizado."}
    return {"status": "error", "message": "No se pudo guardar el conocimiento."}

@app.post("/ingest/file", tags=["Admin"], summary="Subir Documento (PDF, TXT, Excel, Imagen)")
async def ingest_file(
    company_id: str = Form(...),
    file: UploadFile = File(...),
    orchestrator: ConversationOrchestrator = Depends(get_orchestrator)
):
    """
    Sube un archivo, extrae su texto (con OCR si es necesario) y lo indexa para una empresa.
    """
    try:
        content = await file.read()
        text = DocumentProcessor.extract_text(content, file.filename)
        
        if not text.strip():
            return {"status": "error", "message": "No se pudo extraer texto del archivo."}

        # 1. Chunking (Fragmentación del texto para mejor RAG)
        # Cortamos en pedazos de ~1000 caracteres con solapamiento
        chunks = [text[i:i+1000] for i in range(0, len(text), 800)]
        
        points = []
        import uuid
        for i, chunk in enumerate(chunks):
            point_id = str(uuid.uuid4())
            vector = orchestrator.embedding_provider.embed_text(chunk)
            points.append({
                "id": point_id,
                "vector": vector,
                "payload": {
                    "text": chunk,
                    "company_id": company_id,
                    "source": file.filename,
                    "chunk_index": i
                }
            })

        # 2. Guardar en Bloque (Mucho más eficiente que uno por uno)
        success = await orchestrator.vector_store.upsert(points)
        
        if success:
            return {
                "status": "success", 
                "company_id": company_id,
                "chunks": len(chunks),
                "message": f"Archivo '{file.filename}' procesado e indexado."
            }
        return {"status": "error", "message": "Fallo al indexar en la base vectorial."}
        
    except Exception as e:
        logger.error("Error in file ingestion", error=str(e))
        return {"status": "error", "message": str(e)}

@app.post("/ingest/bulk", tags=["Admin"], summary="Subir Múltiples Archivos")
async def ingest_bulk(
    company_id: str = Form(...),
    files: List[UploadFile] = File(...),
    orchestrator: ConversationOrchestrator = Depends(get_orchestrator)
):
    """
    Versión masiva para cargar múltiples documentos a la vez.
    """
    total_chunks = 0
    errors = []
    
    for file in files:
        try:
            content = await file.read()
            text = DocumentProcessor.extract_text(content, file.filename)
            if not text.strip():
                errors.append(f"No text in {file.filename}")
                continue
                
            chunks = [text[i:i+1000] for i in range(0, len(text), 800)]
            points = []
            import uuid
            for i, chunk in enumerate(chunks):
                vector = orchestrator.embedding_provider.embed_text(chunk)
                points.append({
                    "id": str(uuid.uuid4()),
                    "vector": vector,
                    "payload": {"text": chunk, "company_id": company_id, "source": file.filename}
                })
            
            await orchestrator.vector_store.upsert(points)
            total_chunks += len(chunks)
        except Exception as e:
            errors.append(f"Error in {file.filename}: {str(e)}")

    return {
        "status": "partial_success" if errors else "success",
        "total_files": len(files),
        "total_chunks": total_chunks,
        "errors": errors
    }

@app.delete("/knowledge/{company_id}", tags=["Admin"], summary="Eliminar Conocimiento de la Empresa")
async def delete_knowledge(
    company_id: str,
    point_id: str = Query(None, description="ID específico del punto a eliminar"),
    source: str = Query(None, description="Filtrar por origen (metadata.source)"),
    orchestrator: ConversationOrchestrator = Depends(get_orchestrator)
):
    """
    Elimina información de una empresa. 
    - Si no envías parámetros extra, borra TODO lo de la empresa.
    - Si envías point_id, borra solo ese fragmento.
    - Si envías source, borra todo lo relacionado a ese origen técnico.
    """
    filters = {}
    if point_id:
        # Nota: En Qdrant el ID del punto puede usarse como filtro en el payload 
        # o directamente por su ID de estructura. Aquí lo manejamos como metadato.
        filters["id"] = point_id
    if source:
        filters["source"] = source

    success = await orchestrator.vector_store.delete(company_id, filter_metadata=filters if filters else None)
    
    if success:
        detail = "Todo el conocimiento" if not filters else f"Conocimiento filtrado por {list(filters.keys())}"
        return {"status": "success", "message": f"{detail} de {company_id} eliminado."}
    return {"status": "error", "message": "No se pudo eliminar el conocimiento."}

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
