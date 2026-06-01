import sys
import os
import argparse
import logging
import shutil

# Ensure project root is on path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from dotenv import load_dotenv
load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(description="Build GitLab chatbot vector index")
    parser.add_argument(
        "--rebuild", action="store_true",
        help="Delete cached data and rebuild from scratch"
    )
    parser.add_argument(
        "--max-pages", type=int, default=300,
        help="Max handbook pages to scrape (default: 300)"
    )
    args = parser.parse_args()

    logger.info(f"Vector store backend: ChromaDB")

    # Clean cache if rebuild requested
    if args.rebuild:
        logger.info("--rebuild: removing cached data...")
        for path in ["data/raw_pages.json", "data/chunks.json"]:
            if os.path.exists(path):
                os.remove(path)
                logger.info(f"  Removed {path}")
        if os.path.exists("vectorstore"):
            shutil.rmtree("vectorstore", ignore_errors=True)
            logger.info("  Removed vectorstore/")

    # ── Step 1: Scrape ──────────────────────────────────────────────────────
    print("\n" + "═" * 60)
    print(" STEP 1/3  —  Scraping GitLab pages")
    print("═" * 60)
    from src.scraper import run_scraper
    pages = run_scraper(max_handbook_pages=args.max_pages)
    print(f"  Pages collected: {len(pages)}")

    # ── Step 2: Chunk ───────────────────────────────────────────────────────
    print("\n" + "═" * 60)
    print(" STEP 2/3  —  Chunking text")
    print("═" * 60)
    from src.chunker import run_chunker
    chunks = run_chunker()
    print(f"  Chunks created: {len(chunks)}")

    # ── Step 3: Embed + Index ───────────────────────────────────────────────
    print("\n" + "═" * 60)
    print(f" STEP 3/3  —  Embedding & indexing (CHROMADB)")
    print("═" * 60)

    from src.embeddings import build_index, index_exists
    if index_exists():
        print("  Index already exists. Use --rebuild to rebuild.")
    else:
        build_index(chunks)

    print("\n" + "=" * 60)
    print("  Index build complete!")
    print(f"  Backend : ChromaDB")
    print(f"  Pages   : {len(pages)}")
    print(f"  Chunks  : {len(chunks)}")
    print("  Run the app with:  streamlit run app.py")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
