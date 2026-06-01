import os
import streamlit as st
import logging
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

try:
    GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
except Exception:
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
LLM_MODEL      = "gemini-2.5-flash"

SYSTEM_PROMPT = """You are GitLab Assistant, an expert AI assistant specializing exclusively in GitLab's Handbook and Direction pages. You help GitLab employees and candidates understand GitLab's culture, processes, values, strategy, and product direction.

Guidelines:
- Answer ONLY based on the provided context. If the context doesn't contain enough information, say so clearly.
- Be concise, structured, and professional.
- When referencing specific policies or strategies, mention which section they come from.
- Always be helpful and encouraging to users learning about GitLab.

CRITICAL FORMATTING RULES:
You must format every single answer like this:
1. Start with a direct introductory sentence summarizing the topic.
2. Use a bulleted list for the main points. Start each bullet with a **Bolded Key Concept:** followed by the explanation.
3. End with a short concluding sentence summarizing the overall goal or outcome.

IMPORTANT: After your concluding sentence, you must provide EXACTLY 3 suggested follow-up questions enclosed in <SUGGESTED> tags, separated by newlines:

<SUGGESTED>
Follow up question 1?
Follow up question 2?
Follow up question 3?
</SUGGESTED>
"""

RAG_PROMPT_TEMPLATE = """\
CONTEXT FROM GITLAB HANDBOOK & DIRECTION:
{context}

---
USER QUESTION: {question}

Please answer the question based solely on the context above. \
If the context is insufficient, acknowledge what you know from context and note the gaps.\
"""


def _get_client() -> genai.Client:
    if not GEMINI_API_KEY:
        raise ValueError(
            "GEMINI_API_KEY is not set. Please add it to your .env file. "
            "Get a free key at https://aistudio.google.com"
        )
    return genai.Client(api_key=GEMINI_API_KEY)


def generate_response(
    question: str,
    context_chunks: list[dict],
    temperature: float = 0.3,
    conversation_history: list[dict] | None = None,
) -> dict:
    """
    Generate a grounded response using Gemini.

    Returns:
        { "answer": str, "prompt_tokens": int, "output_tokens": int, "model": str }
    """
    from src.rate_limit import retry_on_rate_limit

    client = _get_client()

    # Build context string with source labels
    context_parts = []
    for i, chunk in enumerate(context_chunks, 1):
        label = f"[Source {i}: {chunk.get('title', 'GitLab')} — {chunk.get('url', '')}]"
        context_parts.append(f"{label}\n{chunk['text']}")
    context_str = "\n\n".join(context_parts)

    user_message = RAG_PROMPT_TEMPLATE.format(context=context_str, question=question)

    # Build the contents list (multi-turn history + current message)
    contents: list[types.Content] = []
    if conversation_history:
        for turn in conversation_history[-6:]:   
            role = "user" if turn["role"] == "user" else "model"
            contents.append(
                types.Content(role=role, parts=[types.Part(text=turn["content"])])
            )
    contents.append(
        types.Content(role="user", parts=[types.Part(text=user_message)])
    )

    @retry_on_rate_limit
    def _call_gemini():
        return client.models.generate_content(
            model=LLM_MODEL,
            contents=contents,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                temperature=temperature,
                max_output_tokens=4096,
            ),
        )

    response = _call_gemini()
    
    text = response.text.strip()
    
    # Robustly parse the answer and the suggested questions using regex
    import re
    answer = text
    suggested = []
    
    match = re.search(r'(?s)<SUGGESTED>(.*?)</SUGGESTED>', text)
    if match:
        sugg_block = match.group(1).strip()
        # Extract individual questions by simple newline splitting
        suggested = [q.strip() for q in sugg_block.split('\n') if q.strip()]
        # Remove the <SUGGESTED> block from the main answer
        answer = text[:match.start()].strip()
    else:
        # Fallback: if model failed to format, keep answer as is
        answer = text
        suggested = []

    usage  = response.usage_metadata
    prompt_tokens  = usage.prompt_token_count      if usage else 0
    output_tokens  = usage.candidates_token_count  if usage else 0

    return {
        "answer":              answer,
        "suggested_questions": suggested,
        "prompt_tokens":       prompt_tokens,
        "output_tokens":       output_tokens,
        "model":               LLM_MODEL,
    }
