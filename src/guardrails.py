import os
import re
import logging
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


GITLAB_KEYWORDS = {
    "gitlab", "handbook", "direction", "values", "async", "remote", "iteration",
    "transparency", "collaboration", "efficiency", "merge request", "devops",
    "ci/cd", "pipeline", "runner", "issue", "milestone", "epics", "roadmap",
    "okr", "kpi", "engineering", "product", "design", "ux", "data", "security",
    "compliance", "hiring", "onboarding", "offboarding", "manager", "team",
    "review", "feedback", "career", "promotion", "compensation", "benefits",
    "diversity", "inclusion", "equity", "dei", "all-remote", "contribute",
    "open source", "community", "documentation", "strategy", "vision", "mission",
    "culture", "process", "workflow", "deploy", "release", "feature", "bug",
    "customer", "sales", "marketing", "finance", "legal", "revenue", "tier",
    "premium", "ultimate", "freemium", "pricing", "saas", "self-managed",
    "infrastructure", "reliability", "sre", "observability", "monitoring",
    "kubernetes", "docker", "terraform", "ansible", "aws", "gcp", "azure",
}

OFF_TOPIC_PATTERNS = [
    r"\b(joke|meme|recipe|weather|sports|game|movie|music|celebrity)\b",
    r"\b(stock price|crypto|bitcoin|ethereum|nft)\b",
    r"\b(write me a (poem|story|essay|code(?! review)))\b",
    r"\b(who is (the president|the prime minister|elon musk|jeff bezos))\b",
]

CONFIDENCE_THRESHOLDS = {"high": 0.75, "medium": 0.50, "low": 0.0}


def _quick_keyword_check(query: str) -> bool:
    q = query.lower()
    return any(kw in q for kw in GITLAB_KEYWORDS)


def _off_topic_pattern_check(query: str) -> bool:
    q = query.lower()
    return any(re.search(p, q) for p in OFF_TOPIC_PATTERNS)


def check_query(query: str) -> dict:
    """Guard the incoming user query. Returns {allowed, reason, method}."""
    query = query.strip()
    if not query:
        return {"allowed": False, "reason": "Empty query.", "method": "empty"}
    if len(query) > 2000:
        return {"allowed": False,
                "reason": "Query too long. Please keep it under 2000 characters.",
                "method": "length"}
    if _off_topic_pattern_check(query):
        return {
            "allowed": False,
            "reason": (
                "This assistant is specifically designed to answer questions about GitLab's "
                "Handbook and product direction. Your question appears to be off-topic. "
                "Please try asking about GitLab's values, processes, or product strategy."
            ),
            "method": "pattern",
        }
    if _quick_keyword_check(query):
        return {"allowed": True, "reason": "On-topic (keyword match).", "method": "keyword"}

    allowed, reason = _llm_topic_check(query)
    return {"allowed": allowed, "reason": reason, "method": "llm"}


def _llm_topic_check(query: str) -> tuple[bool, str]:
    """Use Gemini to classify ambiguous queries."""
    if not GEMINI_API_KEY:
        return True, "Permissive (no API key for guardrail)."
    try:
        from src.rate_limit import retry_on_rate_limit

        client = genai.Client(api_key=GEMINI_API_KEY)
        prompt = (
            f"Is the following question related to GitLab (the company), "
            f"its Handbook, processes, values, culture, product direction, "
            f"or DevOps topics? Answer only YES or NO.\n\nQuestion: {query}"
        )

        @retry_on_rate_limit
        def _call_gemini():
            return client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.0,
                    max_output_tokens=5,
                ),
            )

        response = _call_gemini()
        answer = response.text.strip().upper()
        if "YES" in answer:
            return True, "On-topic (LLM classification)."
        return False, (
            "This assistant is built to answer questions about GitLab's Handbook and Direction pages. "
            "Your question does not appear to be related to GitLab. "
            "Please ask about GitLab's culture, values, processes, or product direction."
        )
    except Exception as e:
        logger.warning(f"LLM guardrail check failed: {e}. Allowing query.")
        return True, "Guardrail check skipped (API error)."


def get_confidence_label(similarity_scores: list[float]) -> dict:
    """Return a confidence assessment based on retrieval similarity scores."""
    if not similarity_scores:
        return {"label": "Low", "score": 0.0,
                "explanation": "No relevant sources found.", "color": "#e74c3c"}

    top_score = max(similarity_scores)
    avg_score = sum(similarity_scores) / len(similarity_scores)
    combined  = 0.7 * top_score + 0.3 * avg_score

    if combined >= CONFIDENCE_THRESHOLDS["high"]:
        return {"label": "High", "score": round(combined, 3),
                "explanation": "Strong source match found in GitLab Handbook/Direction.",
                "color": "#27ae60"}
    elif combined >= CONFIDENCE_THRESHOLDS["medium"]:
        return {"label": "Medium", "score": round(combined, 3),
                "explanation": "Partial source match. Answer may be incomplete.",
                "color": "#f39c12"}
    return {"label": "Low", "score": round(combined, 3),
            "explanation": "Weak source match. Please verify with official GitLab docs.",
            "color": "#e74c3c"}


def check_output(answer: str) -> dict:
    """Basic output safety check. Returns {safe, reason}."""
    if not answer or len(answer.strip()) < 5:
        return {"safe": False, "reason": "Empty response generated."}
    return {"safe": True, "reason": "Output OK."}
