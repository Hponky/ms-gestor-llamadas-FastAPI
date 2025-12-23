import uuid
from typing import List, Dict, Optional
from src.domain.interfaces import IVectorStore, IEmbeddingProvider
from src.application.services.document_processor import DocumentProcessor
from src.core.logger import logger

class KnowledgeBaseService:
    """
    Application service to manage the knowledge base (RAG).
    Handles chunking, embedding, and indexing.
    """
    def __init__(self, vector_store: IVectorStore, embedding_provider: IEmbeddingProvider):
        self.vector_store = vector_store
        self.embedding_provider = embedding_provider

    async def ingest_text(self, text: str, company_id: str, metadata: Dict = None) -> str:
        """Indexes a single block of text."""
        point_id = metadata.get("id", str(uuid.uuid4())) if metadata else str(uuid.uuid4())
        vector = self.embedding_provider.embed_text(text)
        
        payload = metadata.copy() if metadata else {}
        payload.update({"text": text, "company_id": company_id})
        
        success = await self.vector_store.upsert([{
            "id": point_id,
            "vector": vector,
            "payload": payload
        }])
        return point_id if success else None

    async def ingest_file(self, content: bytes, filename: str, company_id: str, source_id: str = None) -> bool:
        """Processes a file, chunks it, and indexes it."""
        text = DocumentProcessor.extract_text(content, filename)
        if not text.strip():
            return False

        # Professional Chunking Logic
        chunks = [text[i:i+1000] for i in range(0, len(text), 800)]
        effective_source = source_id or filename
        
        points = []
        for i, chunk in enumerate(chunks):
            vector = self.embedding_provider.embed_text(chunk)
            points.append({
                "id": str(uuid.uuid4()),
                "vector": vector,
                "payload": {
                    "text": chunk,
                    "company_id": company_id,
                    "source": filename,
                    "source_id": effective_source,
                    "chunk_index": i
                }
            })
        
        return await self.vector_store.upsert(points)

    async def delete_knowledge(self, company_id: str, point_id: str = None, source_id: str = None, source: str = None) -> bool:
        """Granular deletion of knowledge."""
        filters = {}
        if point_id: filters["id"] = point_id
        if source_id: filters["source_id"] = source_id
        if source: filters["source"] = source
        
        return await self.vector_store.delete(company_id, filter_metadata=filters if filters else None)
