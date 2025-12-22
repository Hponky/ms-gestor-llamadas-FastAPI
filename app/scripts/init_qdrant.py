import requests
from src.core.config import settings
from src.core.logger import logger

def init_qdrant():
    """
    Checks if the Qdrant collection exists, if not, creates it.
    Required for the first run.
    """
    # Multilingual-e5-small has 384 dimensions
    VECTOR_SIZE = 384 
    
    url = f"{settings.QDRANT_URL}/collections/{settings.QDRANT_COLLECTION}"
    
    logger.info("Checking Qdrant collection...", url=url)
    
    try:
        # Check if exists
        response = requests.get(url)
        if response.status_code == 200:
            logger.info("Qdrant collection already exists.")
            return

        # If not, create it
        logger.info("Creating Qdrant collection...")
        create_url = f"{settings.QDRANT_URL}/collections/{settings.QDRANT_COLLECTION}"
        payload = {
            "vectors": {
                "size": VECTOR_SIZE,
                "distance": "Cosine"
            }
        }
        resp = requests.put(create_url, json=payload)
        if resp.status_code == 200:
            logger.info("Qdrant collection created successfully.")
        else:
            logger.error("Failed to create collection", status=resp.status_code, text=resp.text)
            
    except Exception as e:
        logger.error("Could not connect to Qdrant for initialization", error=str(e))

if __name__ == "__main__":
    from src.core.logger import setup_logging
    setup_logging()
    init_qdrant()
