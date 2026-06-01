import os
import json
import logging
import re

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

RAW_DATA_PATH = os.path.join("data", "raw_pages.json")
CHUNKS_PATH = os.path.join("data", "chunks.json")

CHUNK_SIZE = 600       # ~600 words per chunk
CHUNK_OVERLAP = 80     # ~80 words overlap between consecutive chunks


def _split_into_chunks(text: str, chunk_size: int, overlap: int) -> list[str]:
    """
    Split text into overlapping word-based chunks.
    Uses natural paragraph/sentence boundaries where possible.
    """
    # Split on double newlines (paragraphs) first
    paragraphs = [p.strip() for p in re.split(r"\n{2,}", text) if p.strip()]

    chunks = []
    current_words: list[str] = []

    for para in paragraphs:
        words = para.split()
        if not words:
            continue

        current_words.extend(words)

        # Flush when we hit chunk_size
        while len(current_words) >= chunk_size:
            chunk_text = " ".join(current_words[:chunk_size])
            chunks.append(chunk_text)
            # Keep overlap
            current_words = current_words[chunk_size - overlap:]

    # Flush remainder (must have at least 50 words to be useful)
    if len(current_words) >= 50:
        chunks.append(" ".join(current_words))

    return chunks


def chunk_pages(pages: list[dict]) -> list[dict]:
    """Chunk all pages and return flat list of chunk dicts."""
    all_chunks = []
    chunk_id = 0

    for page in pages:
        title = page.get("title", "")
        url = page.get("url", "")
        text = page.get("text", "")

        if not text.strip():
            continue

        text_chunks = _split_into_chunks(text, CHUNK_SIZE, CHUNK_OVERLAP)

        for chunk_text in text_chunks:
            all_chunks.append({
                "id": chunk_id,
                "url": url,
                "title": title,
                "text": chunk_text,
            })
            chunk_id += 1

    return all_chunks


def run_chunker() -> list[dict]:
    """Load raw pages, chunk them, save and return chunks."""
    os.makedirs("data", exist_ok=True)

    if os.path.exists(CHUNKS_PATH):
        logger.info(f"Chunks already exist at {CHUNKS_PATH}. Loading cache.")
        with open(CHUNKS_PATH, "r", encoding="utf-8") as f:
            chunks = json.load(f)
        logger.info(f"Loaded {len(chunks)} cached chunks")
        return chunks

    if not os.path.exists(RAW_DATA_PATH):
        raise FileNotFoundError(
            f"Raw data not found at {RAW_DATA_PATH}. "
            "Run the scraper first: python scripts/build_index.py"
        )

    with open(RAW_DATA_PATH, "r", encoding="utf-8") as f:
        pages = json.load(f)

    logger.info(f"Loaded {len(pages)} pages → chunking...")
    chunks = chunk_pages(pages)
    logger.info(f"Created {len(chunks)} chunks")

    with open(CHUNKS_PATH, "w", encoding="utf-8") as f:
        json.dump(chunks, f, ensure_ascii=False, indent=2)

    logger.info(f"Saved chunks to {CHUNKS_PATH}")
    return chunks


if __name__ == "__main__":
    chunks = run_chunker()
    print(f"\nTotal chunks: {len(chunks)}")
    print(f"Sample chunk:\n  URL: {chunks[0]['url']}")
    print(f"  Text: {chunks[0]['text'][:200]}...")
