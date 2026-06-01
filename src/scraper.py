import os
import json
import time
import logging
import requests
from bs4 import BeautifulSoup
from xml.etree import ElementTree as ET

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

RAW_DATA_PATH = os.path.join("data", "raw_pages.json")
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (compatible; GitLabChatbot/1.0; "
        "educational project scraper)"
    )
}

HANDBOOK_SITEMAP = "https://handbook.gitlab.com/sitemap.xml"
DIRECTION_ROOT = "https://about.gitlab.com/direction/"

DIRECTION_SUBPAGES = [
    "https://about.gitlab.com/direction/",
    "https://about.gitlab.com/direction/dev/",
    "https://about.gitlab.com/direction/ops/",
    "https://about.gitlab.com/direction/sec/",
    "https://about.gitlab.com/direction/data-science/",
    "https://about.gitlab.com/direction/configure/",
    "https://about.gitlab.com/direction/enablement/",
    "https://about.gitlab.com/direction/growth/",
    "https://about.gitlab.com/direction/fulfillment/",
    "https://about.gitlab.com/direction/ci-cd/",
    "https://about.gitlab.com/direction/devsecops/",
]

CORE_HANDBOOK_PAGES = [
    "https://handbook.gitlab.com/handbook/values/",
    "https://handbook.gitlab.com/handbook/company/culture/all-remote/asynchronous/",
    "https://handbook.gitlab.com/handbook/hiring/",
    "https://handbook.gitlab.com/handbook/company/culture/all-remote/",
    "https://handbook.gitlab.com/handbook/people-group/performance-assessments-and-succession-planning/",
]

# Max pages to scrape from Handbook sitemap (to avoid >30 min runs)
MAX_HANDBOOK_PAGES = 300


def _get_sitemap_urls(sitemap_url: str, max_pages: int = MAX_HANDBOOK_PAGES) -> list[str]:
    """Parse a sitemap XML and return page URLs."""
    try:
        resp = requests.get(sitemap_url, headers=HEADERS, timeout=15)
        resp.raise_for_status()
    except Exception as e:
        logger.error(f"Failed to fetch sitemap {sitemap_url}: {e}")
        return []

    try:
        root = ET.fromstring(resp.content)
    except ET.ParseError as e:
        logger.error(f"Failed to parse sitemap XML: {e}")
        return []

    ns = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
    urls = []

    # Handle sitemap index (points to child sitemaps)
    child_sitemaps = root.findall("sm:sitemap/sm:loc", ns)
    if child_sitemaps:
        for sm in child_sitemaps:
            child_urls = _get_sitemap_urls(sm.text.strip(), max_pages - len(urls))
            urls.extend(child_urls)
            if len(urls) >= max_pages:
                break
        return urls[:max_pages]

    for url_elem in root.findall("sm:url/sm:loc", ns):
        urls.append(url_elem.text.strip())
        if len(urls) >= max_pages:
            break

    return urls


def _extract_text(url: str) -> dict | None:
    """Fetch a URL and extract clean (title, text) from the HTML body."""
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        if resp.status_code != 200:
            return None
        resp.encoding = "utf-8"
    except Exception as e:
        logger.warning(f"Request error for {url}: {e}")
        return None

    soup = BeautifulSoup(resp.text, "lxml")

    # Remove noise elements
    for tag in soup(["nav", "footer", "header", "script", "style",
                     "aside", "form", ".sidebar", ".toc"]):
        tag.decompose()

    title = soup.title.string.strip() if soup.title else url

    # Get main content
    main = soup.find("main") or soup.find("article") or soup.body
    if not main:
        return None

    text = " ".join(main.get_text(separator=" ").split())

    if len(text) < 100:
        return None

    return {"url": url, "title": title, "text": text}


def scrape_handbook(max_pages: int = MAX_HANDBOOK_PAGES) -> list[dict]:
    """Scrape GitLab Handbook pages."""
    pages = []
    seen_urls = set()

    # 1. Scrape core handbook pages first to ensure guaranteed context
    logger.info("Fetching Core Handbook pages...")
    for url in CORE_HANDBOOK_PAGES:
        page = _extract_text(url)
        if page:
            pages.append(page)
            seen_urls.add(url)
            logger.info(f"  Scraped Core: {url}")
        time.sleep(0.3)

    # 2. Scrape from sitemap
    logger.info(f"Fetching Handbook sitemap: {HANDBOOK_SITEMAP}")
    urls = _get_sitemap_urls(HANDBOOK_SITEMAP, max_pages)
    logger.info(f"Found {len(urls)} Handbook URLs from sitemap to scrape")

    for i, url in enumerate(urls):
        if url in seen_urls:
            continue
        page = _extract_text(url)
        if page:
            pages.append(page)
            seen_urls.add(url)
            if len(pages) % 20 == 0:
                logger.info(f"  Scraped {len(pages)} handbook pages so far...")
        time.sleep(0.3)

    logger.info(f"Handbook: scraped {len(pages)} pages successfully")
    return pages


def scrape_direction() -> list[dict]:
    """Scrape GitLab Direction pages."""
    logger.info("Scraping GitLab Direction pages...")
    pages = []
    seen_urls = set()

    for url in DIRECTION_SUBPAGES:
        if url in seen_urls:
            continue
        seen_urls.add(url)

        page = _extract_text(url)
        if page:
            pages.append(page)
            logger.info(f"  Scraped: {url}")

        # discover internal direction links from the page
        try:
            resp = requests.get(url, headers=HEADERS, timeout=15)
            soup = BeautifulSoup(resp.text, "lxml")
            for a in soup.find_all("a", href=True):
                href = a["href"]
                if href.startswith("/direction/") and not href.endswith(".pdf"):
                    full = "https://about.gitlab.com" + href.split("#")[0].rstrip("/") + "/"
                    if full not in seen_urls and len(pages) < 60:
                        seen_urls.add(full)
                        subpage = _extract_text(full)
                        if subpage:
                            pages.append(subpage)
                            logger.info(f"  Scraped sub: {full}")
                        time.sleep(0.3)
        except Exception:
            pass

        time.sleep(0.5)

    logger.info(f"Direction: scraped {len(pages)} pages successfully")
    return pages


def run_scraper(max_handbook_pages: int = MAX_HANDBOOK_PAGES) -> list[dict]:
    """Run full scraping pipeline and save results."""
    os.makedirs("data", exist_ok=True)

    if os.path.exists(RAW_DATA_PATH):
        logger.info(f"Raw data already exists at {RAW_DATA_PATH}. Loading cache.")
        with open(RAW_DATA_PATH, "r", encoding="utf-8") as f:
            pages = json.load(f)
        logger.info(f"Loaded {len(pages)} cached pages")
        return pages

    handbook_pages = scrape_handbook(max_handbook_pages)
    direction_pages = scrape_direction()

    all_pages = handbook_pages + direction_pages
    logger.info(f"Total pages scraped: {len(all_pages)}")

    with open(RAW_DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(all_pages, f, ensure_ascii=False, indent=2)

    logger.info(f"Saved raw data to {RAW_DATA_PATH}")
    return all_pages


if __name__ == "__main__":
    pages = run_scraper()
    print(f"\nScraped {len(pages)} pages total")
    print(f"Sample: {pages[0]['title']} - {pages[0]['url']}")
