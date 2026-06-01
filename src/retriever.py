import logging
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

class Retriever:
    """
    Retriever that works with local ChromaDB.
    """

    def __init__(self, top_k: int = 5):
        self.top_k = top_k
        self._collection = None
        self._loaded = False

    def _load(self):
        if self._loaded:
            return

        from src.embeddings import _get_chroma_collection
        logger.info("Retriever: using ChromaDB backend")
        self._collection = _get_chroma_collection()
        self._loaded = True

    def retrieve(self, query: str, top_k: int | None = None) -> list[dict]:
        """
        Retrieve the most relevant chunks for a query.

        Returns list of dicts:
          { id, url, title, text, similarity }
        Similarity is a float 0-1 (higher = more relevant).
        """
        self._load()
        k = top_k or self.top_k

        from src.embeddings import embed_query
        query_vec = embed_query(query)

        results = self._collection.query(
            query_embeddings=[query_vec],
            n_results=k
        )

        output = []
        if results and results["ids"] and results["ids"][0]:
            for i in range(len(results["ids"][0])):
                # Calculate similarity from cosine distance (1 - distance)
                distance = results["distances"][0][i] if "distances" in results and results["distances"] else 0.5
                output.append({
                    "id": results["ids"][0][i],
                    "url": results["metadatas"][0][i]["url"],
                    "title": results["metadatas"][0][i]["title"],
                    "text": results["documents"][0][i],
                    "similarity": 1.0 - distance
                })

        return output

    def reload(self):
        """Force reload (e.g., after re-indexing)."""
        self._loaded = False
        self._collection = None
        self._load()
