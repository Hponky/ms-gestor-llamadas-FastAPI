from typing import List
from fastembed import TextEmbedding
from src.domain.interfaces import IEmbeddingProvider
from src.core.config import settings

class FastEmbedAdapter(IEmbeddingProvider):
    def __init__(self, model_name: str = None):
        """
        Initializes the FastEmbed model.
        Model: intfloat/multilingual-e5-small (optimizado para múltiples idiomas)
        """
        model_name = model_name or settings.EMBEDDING_MODEL
        try:
            logger.info("Initializing FastEmbed model...", model=model_name)
            self.model = TextEmbedding(model_name=model_name)
            logger.info("FastEmbed model initialized successfully")
        except Exception as e:
            logger.error("Failed to initialize FastEmbed model", error=str(e))
            raise

    def embed_text(self, text: str) -> List[float]:
        """Generates embedding for a single string."""
        # FastEmbed returns an iterator of numpy arrays
        embeddings = list(self.model.embed([text]))
        return embeddings[0].tolist()

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Generates embeddings for a list of strings."""
        embeddings_iter = self.model.embed(texts)
        return [emb.tolist() for emb in embeddings_iter]
