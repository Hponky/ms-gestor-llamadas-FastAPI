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

    async def search(self, query_vector: List[float], company_id: str, limit: int = 5, score_threshold: float = 0.7) -> List[Dict]:
        """
        Performs a vector search filtering strictly by company_id.
        This ensures isolation between different tenants.
        score_threshold helps filtering irrelevant results.
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
                score_threshold=score_threshold
            )
            
            # Extract payload (metadata) from results
            results = [hit.payload for hit in search_result]
            logger.debug("Vector search completed", company_id=company_id, matches=len(results))
            return results
        except Exception as e:
            logger.error("Error searching in Qdrant", error=str(e), company_id=company_id)
            return []

    async def upsert(self, points: List[Dict]) -> bool:
        """
        Add or update information fragments in Qdrant.
        Expects a list of dicts with: id, vector, and payload.
        """
        try:
            q_points = [
                models.PointStruct(
                    id=p["id"],
                    vector=p["vector"],
                    payload=p["payload"]
                ) for p in points
            ]
            self.client.upsert(
                collection_name=self.collection_name,
                points=q_points
            )
            logger.info("Upserted points successfully", count=len(points))
            return True
        except Exception as e:
            logger.error("Failed to upsert points in Qdrant", error=str(e))
            return False

    async def delete(self, company_id: str, filter_metadata: Dict = None) -> bool:
        """
        Deletes knowledge blocks for a specific company.
        Can optionally filter by other metadata (e.g. source_id).
        """
        try:
            must_filters = [
                models.FieldCondition(
                    key="company_id",
                    match=models.MatchValue(value=company_id)
                )
            ]
            
            if filter_metadata:
                for key, value in filter_metadata.items():
                    must_filters.append(
                        models.FieldCondition(
                            key=key,
                            match=models.MatchValue(value=value)
                        )
                    )

            self.client.delete(
                collection_name=self.collection_name,
                points_selector=models.Filter(must=must_filters)
            )
            logger.info("Deleted points in Qdrant", company_id=company_id)
            return True
        except Exception as e:
            logger.error("Failed to delete points in Qdrant", error=str(e), company_id=company_id)
            return False
