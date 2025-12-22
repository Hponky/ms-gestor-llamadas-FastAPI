from typing import List, Dict
from qdrant_client import QdrantClient, models
from src.domain.interfaces import IVectorStore
from src.core.config import settings
from src.core.logger import logger

class QdrantVectorStoreAdapter(IVectorStore):
    def __init__(self):
        """
        Initializes the Qdrant client.
        Supports both local development and cloud (via API Key).
        """
        try:
            self.client = QdrantClient(
                url=settings.QDRANT_URL,
                api_key=settings.QDRANT_API_KEY
            )
            self.collection_name = settings.QDRANT_COLLECTION
            logger.info("Qdrant client initialized", url=settings.QDRANT_URL, collection=self.collection_name)
        except Exception as e:
            logger.error("Failed to initialize Qdrant client", error=str(e))
            raise

    async def search(self, query_vector: List[float], company_id: str, limit: int = 5) -> List[Dict]:
        """
        Performs a vector search filtering strictly by company_id.
        This ensures isolation between different tenants.
        """
        try:
            search_result = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_vector,
                query_filter=models.Filter(
                    must=[
                        models.FieldCondition(
                            key="company_id",
                            match=models.MatchValue(value=company_id),
                        )
                    ]
                ),
                limit=limit,
            )
            
            # Extract payload (metadata) from results
            results = [hit.payload for hit in search_result]
            logger.debug("Vector search completed", company_id=company_id, matches=len(results))
            return results
            
        except Exception as e:
            logger.error("Error searching in Qdrant", error=str(e), company_id=company_id)
            return []
