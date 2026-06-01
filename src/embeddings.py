import os
import json
import logging
import time
import numpy as np
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

import streamlit as st

try:
    GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
except Exception:
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
EMBED_MODEL      = "gemini-embedding-001"   # 3072-dim (replaces deprecated text-embedding-004)
# Use absolute path so this works regardless of working directory (e.g. Streamlit Cloud)
CHROMA_DB_DIR    = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "vectorstore")
CHROMA_COLLECTION= "gitlab_chunks"
BATCH_SIZE       = 50


def _get_client() -> genai.Client:
    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY is not set. Check your .env file.")
    return genai.Client(api_key=GEMINI_API_KEY)


def embed_texts(
    texts: list[str],
    task_type: str = "RETRIEVAL_DOCUMENT",
) -> list[list[float]]:
    """Embed a list of texts using Gemini embedding model."""
    from src.rate_limit import retry_on_rate_limit

    client = _get_client()
    all_embeddings = []

    @retry_on_rate_limit
    def _embed_batch(batch, use_config=True):
        if use_config:
            return client.models.embed_content(
                model=EMBED_MODEL,
                contents=batch,
                config=types.EmbedContentConfig(task_type=task_type),
            )
        return client.models.embed_content(
            model=EMBED_MODEL,
            contents=batch,
        )

    for i in range(0, len(texts), BATCH_SIZE):
        batch = texts[i : i + BATCH_SIZE]
        try:
            try:
                response = _embed_batch(batch, use_config=True)
            except Exception as config_err:
                if "404" in str(config_err) or "not found" in str(config_err).lower():
                    logger.warning("Config-based embed failed, retrying without config...")
                    response = _embed_batch(batch, use_config=False)
                else:
                    raise

            all_embeddings.extend([e.values for e in response.embeddings])

        except Exception as e:
            logger.error(f"Embedding failed for batch {i // BATCH_SIZE}: {e}")
            all_embeddings.extend([[0.0] * 3072] * len(batch))

        if i + BATCH_SIZE < len(texts):
            time.sleep(0.5)

        if (i // BATCH_SIZE + 1) % 5 == 0:
            logger.info(f"  Embedded {min(i + BATCH_SIZE, len(texts))}/{len(texts)} chunks...")

    return all_embeddings


def embed_query(query: str) -> list[float]:
    """Embed a single search query (uses RETRIEVAL_QUERY task type)."""
    return embed_texts([query], task_type="RETRIEVAL_QUERY")[0]



def _get_chroma_collection():
    import chromadb
    client = chromadb.PersistentClient(path=CHROMA_DB_DIR)
    return client.get_or_create_collection(
        name=CHROMA_COLLECTION,
        metadata={"hnsw:space": "cosine"}
    )

def build_index(chunks: list[dict]) -> None:
    collection = _get_chroma_collection()
    texts = [c["text"] for c in chunks]
    
    logger.info(f"Embedding {len(texts)} chunks with Gemini...")
    embeddings = embed_texts(texts)

    logger.info("Adding to ChromaDB...")
    
    # Chroma DB batch size limits
    batch_size = 100
    for i in range(0, len(chunks), batch_size):
        batch_chunks = chunks[i:i + batch_size]
        batch_embeddings = embeddings[i:i + batch_size]
        
        collection.upsert(
            ids=[str(c["id"]) for c in batch_chunks],
            embeddings=batch_embeddings,
            metadatas=[{"url": c["url"], "title": c["title"]} for c in batch_chunks],
            documents=[c["text"] for c in batch_chunks]
        )
        logger.info(f"  Upserted rows {i}–{i + len(batch_chunks)}")

    logger.info(f"ChromaDB index saved ({collection.count()} total chunks).")

def index_exists() -> bool:
    try:
        import chromadb
        logger.info(f"Checking index at: {CHROMA_DB_DIR}")
        client = chromadb.PersistentClient(path=CHROMA_DB_DIR)
        collections = client.list_collections()
        # Newer chromadb list_collections returns objects, older ones strings
        for c in collections:
            if getattr(c, "name", c) == CHROMA_COLLECTION:
                count = client.get_collection(CHROMA_COLLECTION).count()
                logger.info(f"Collection '{CHROMA_COLLECTION}' found with {count} embeddings")
                return count > 0
        logger.warning(f"Collection '{CHROMA_COLLECTION}' not found. Available: {[getattr(c,'name',c) for c in collections]}")
        return False
    except Exception as e:
        logger.error(f"index_exists() failed: {e}", exc_info=True)
        return False
