import os
import sys
import html
import time
import asyncio
import datetime
import streamlit as st
from dotenv import load_dotenv

if sys.platform == "win32":
    import warnings
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", DeprecationWarning)
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

load_dotenv()
sys.path.insert(0, os.path.dirname(__file__))

# Page Config (MUST be first Streamlit call)
st.set_page_config(
    page_title="GitLab Assistant",
    page_icon="◆",
    layout="centered",
    initial_sidebar_state="collapsed",
)

DEFAULT_SUGGESTIONS = [
    "What are GitLab's CREDIT values and how do teams use them?",
    "How does GitLab Duo fit into the current product direction?",
    "What does the handbook say about async communication and meetings?",
    "Summarize GitLab's approach to security, compliance, and incident response",
]

# GitLab-inspired theme
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

:root {
    --gl-orange: #FC6D26;
    --gl-orange-dark: #E24329;
    --gl-purple: #6B4FBB;
    --gl-purple-dark: #380D75;
    --gl-navy: #171321;
    --gl-surface: #FFFFFF;
    --gl-bg: #F4F0FA;
    --gl-bg-accent: linear-gradient(160deg, #FFF8F5 0%, #F4F0FA 45%, #EDE8F8 100%);
    --gl-text: #2D2640;
    --gl-muted: #6B6280;
    --gl-border: #E2DCEF;
    --gl-success: #108548;
    --gl-warning: #C17D00;
    --gl-danger: #C91C1C;
    --shadow-sm: 0 2px 8px rgba(23, 19, 33, 0.06);
    --shadow-md: 0 8px 28px rgba(107, 79, 187, 0.12);
    --radius: 14px;
}

html, body, [class*="css"], .stApp, .stApp * {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
}

.stApp {
    background: var(--gl-bg-accent) !important;
    color: var(--gl-text) !important;
}

.main .block-container {
    max-width: 920px !important;
    padding-top: 1.25rem !important;
    padding-bottom: 130px !important;
}

.main, .main > div, section[data-testid="stMain"] {
    background: transparent !important;
}

[data-testid="stSidebar"],
[data-testid="collapsedControl"] {
    display: none !important;
}

/* Top hero card */
.hero-card {
    background: var(--gl-surface);
    border: 1px solid var(--gl-border);
    border-radius: 20px;
    padding: 1.35rem 1.5rem 1.1rem;
    margin-bottom: 1.5rem;
    box-shadow: var(--shadow-md);
    animation: fadeInDown 0.45s ease-out;
    position: relative;
    overflow: hidden;
}
.hero-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 4px;
    background: linear-gradient(90deg, var(--gl-orange), var(--gl-purple));
}
.hero-row {
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    gap: 1rem;
    flex-wrap: wrap;
}
.hero-brand {
    display: flex;
    align-items: center;
    gap: 14px;
}
.hero-logo {
    width: 48px;
    height: 48px;
    border-radius: 14px;
    background: linear-gradient(135deg, var(--gl-orange) 0%, var(--gl-purple) 100%);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 0.8rem;
    font-weight: 700;
    color: #fff;
    letter-spacing: -0.04em;
    box-shadow: 0 4px 14px rgba(252, 109, 38, 0.35);
}
.main-header {
    color: var(--gl-navy) !important;
    font-size: 1.65rem !important;
    font-weight: 700 !important;
    letter-spacing: -0.03em;
    margin: 0 !important;
    line-height: 1.2 !important;
}
.sub-header {
    color: var(--gl-muted) !important;
    font-size: 0.92rem !important;
    margin: 4px 0 0 !important;
    font-weight: 400 !important;
}
.status-pill {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    padding: 6px 14px;
    border-radius: 999px;
    font-size: 0.78rem;
    font-weight: 600;
    letter-spacing: 0.02em;
}
.status-ready {
    background: #E3F5EC;
    color: var(--gl-success);
}
.status-offline {
    background: #FDECEC;
    color: var(--gl-danger);
}
.status-dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: currentColor;
    animation: pulse 2s ease-in-out infinite;
}
@keyframes pulse {
    0%, 100% { opacity: 1; transform: scale(1); }
    50% { opacity: 0.55; transform: scale(0.85); }
}

/* Primary action buttons in main area */
div[data-testid="column"] .stButton > button[kind="secondary"],
.main .stButton > button {
    background: var(--gl-surface) !important;
    border: 1.5px solid var(--gl-border) !important;
    color: var(--gl-purple) !important;
    border-radius: 10px !important;
    font-weight: 500 !important;
    transition: all 0.2s ease !important;
}
.main .stButton > button:hover {
    border-color: var(--gl-purple) !important;
    background: #F8F5FF !important;
    box-shadow: var(--shadow-sm) !important;
    transform: translateY(-1px);
}

/* Suggestion chip buttons */
div[data-testid="stHorizontalBlock"] .stButton > button {
    background: #fff !important;
    border: 1.5px solid var(--gl-border) !important;
    color: var(--gl-text) !important;
    border-radius: 999px !important;
    font-size: 0.82rem !important;
    padding: 0.45rem 0.9rem !important;
    text-align: left !important;
    white-space: normal !important;
    height: auto !important;
    min-height: 2.4rem !important;
    line-height: 1.35 !important;
    transition: all 0.2s ease !important;
}
div[data-testid="stHorizontalBlock"] .stButton > button:hover {
    border-color: var(--gl-orange) !important;
    color: var(--gl-orange-dark) !important;
    background: #FFF8F5 !important;
    box-shadow: 0 4px 12px rgba(252, 109, 38, 0.15) !important;
}

.suggestions-label {
    font-size: 0.8rem;
    font-weight: 600;
    color: var(--gl-muted);
    text-transform: uppercase;
    letter-spacing: 0.06em;
    margin: 0 0 10px 2px;
}

/* Chat */
.chat-thread { margin-bottom: 0.5rem; }
.user-message {
    display: flex;
    justify-content: flex-end;
    margin: 0.85rem 0;
    animation: fadeInUp 0.35s ease-out;
}
.user-bubble-wrap { max-width: 78%; text-align: right; }
.user-bubble {
    display: inline-block;
    background: linear-gradient(135deg, var(--gl-orange) 0%, var(--gl-orange-dark) 100%);
    color: #fff;
    padding: 12px 18px;
    border-radius: 18px 18px 4px 18px;
    font-size: 0.94rem;
    line-height: 1.55;
    box-shadow: 0 6px 20px rgba(252, 109, 38, 0.28);
    text-align: left;
}
.msg-time {
    font-size: 0.7rem;
    color: var(--gl-muted);
    margin-top: 4px;
    padding-right: 4px;
}

.bot-message {
    display: flex;
    justify-content: flex-start;
    gap: 12px;
    margin: 0.85rem 0;
    animation: fadeInUp 0.35s ease-out;
}
.bot-avatar {
    width: 42px;
    height: 42px;
    border-radius: 12px;
    background: linear-gradient(145deg, var(--gl-purple) 0%, var(--gl-purple-dark) 100%);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 0.75rem;
    font-weight: 700;
    flex-shrink: 0;
    color: #fff;
    box-shadow: 0 4px 12px rgba(107, 79, 187, 0.35);
    letter-spacing: -0.02em;
}
.bot-bubble {
    background: var(--gl-surface);
    border: 1px solid var(--gl-border);
    color: var(--gl-text);
    padding: 14px 18px;
    border-radius: 4px 18px 18px 18px;
    max-width: calc(100% - 54px);
    font-size: 0.94rem;
    line-height: 1.65;
    box-shadow: var(--shadow-sm);
}
.bot-bubble .stMarkdown p { color: var(--gl-text) !important; }

.confidence-badge {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 5px 12px;
    border-radius: 999px;
    font-size: 0.72rem;
    font-weight: 600;
    margin-top: 10px;
}
.badge-high   { background: #E3F5EC; color: var(--gl-success); }
.badge-medium { background: #FFF4E0; color: var(--gl-warning); }
.badge-low    { background: #FDECEC; color: var(--gl-danger); }

.token-info {
    font-size: 0.7rem;
    color: var(--gl-muted);
    margin-top: 8px;
    font-family: 'JetBrains Mono', monospace !important;
}

/* Chat input — one cohesive bar (outer + inner must match; dark theme targets textarea) */
[data-testid="stChatInput"] {
    position: fixed;
    bottom: 0;
    left: 50%;
    transform: translateX(-50%);
    width: calc(100% - 2.5rem);
    max-width: 920px;
    padding: 1rem 0 1.5rem;
    background: #F4F0FA !important;
    z-index: 999;
    color-scheme: light;
}
[data-testid="stChatInput"] > div {
    background: #ffffff !important;
    border: 2px solid var(--gl-border) !important;
    border-radius: 18px !important;
    box-shadow: var(--shadow-md) !important;
    overflow: hidden !important;
    transition: border-color 0.2s, box-shadow 0.2s !important;
}
[data-testid="stChatInput"] > div:focus-within {
    border-color: var(--gl-purple) !important;
    box-shadow: 0 8px 32px rgba(107, 79, 187, 0.2) !important;
}
/* Inner wrappers Streamlit/Baseweb add in dark mode */
[data-testid="stChatInput"] > div > div,
[data-testid="stChatInput"] [data-baseweb="base-input"],
[data-testid="stChatInput"] [data-baseweb="textarea"] {
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
    border-radius: 0 !important;
}
[data-testid="stChatInput"] textarea,
[data-testid="stChatInput"] input {
    background: transparent !important;
    color: var(--gl-text) !important;
    border: none !important;
    border-radius: 0 !important;
    box-shadow: none !important;
    caret-color: var(--gl-purple) !important;
    font-size: 0.95rem !important;
    padding: 12px 14px !important;
    min-height: 44px !important;
}
[data-testid="stChatInput"] textarea::placeholder,
[data-testid="stChatInput"] input::placeholder {
    color: var(--gl-muted) !important;
    opacity: 1 !important;
}
[data-testid="stChatInput"] button {
    background: linear-gradient(135deg, var(--gl-orange), var(--gl-orange-dark)) !important;
    border: none !important;
    border-radius: 12px !important;
    margin: 4px !important;
}
[data-testid="stChatInput"] button:hover {
    transform: scale(1.05);
    box-shadow: 0 4px 14px rgba(252, 109, 38, 0.45) !important;
}
[data-testid="stChatInput"] button svg { fill: #ffffff !important; }

/* Typing */
.typing-dot {
    width: 8px; height: 8px;
    background: var(--gl-purple);
    border-radius: 50%;
    display: inline-block;
    animation: typingBounce 1.4s infinite ease-in-out;
}
.typing-dot:nth-child(2) { animation-delay: 0.15s; }
.typing-dot:nth-child(3) { animation-delay: 0.3s; }
@keyframes typingBounce {
    0%, 60%, 100% { transform: translateY(0); opacity: 0.35; }
    30% { transform: translateY(-7px); opacity: 1; }
}

/* Sources */
.source-card {
    background: #FAFAFE;
    border: 1px solid var(--gl-border);
    border-left: 3px solid var(--gl-purple);
    border-radius: 10px;
    padding: 12px 14px;
    margin: 8px 0;
    font-size: 0.84rem;
    transition: all 0.2s ease;
}
.source-card:hover {
    border-left-color: var(--gl-orange);
    box-shadow: var(--shadow-sm);
    transform: translateX(4px);
}
.source-card a { color: var(--gl-purple) !important; font-weight: 600; }

div[data-testid="stExpander"] {
    background: #fff !important;
    border: 1px solid var(--gl-border) !important;
    border-radius: 12px !important;
}
div[data-testid="stExpander"] summary {
    color: var(--gl-purple) !important;
    font-weight: 600 !important;
}

/* Empty state */
.empty-state {
    text-align: center;
    padding: 2.5rem 1rem 1rem;
    animation: fadeIn 0.5s ease-out;
}
.empty-state-icon {
    width: 72px; height: 72px;
    margin: 0 auto 1rem;
    border-radius: 20px;
    background: linear-gradient(135deg, rgba(252,109,38,0.15), rgba(107,79,187,0.15));
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 0.85rem;
    font-weight: 700;
    color: var(--gl-purple);
    letter-spacing: 0.04em;
}
.empty-state-title {
    color: var(--gl-navy);
    font-size: 1.15rem;
    font-weight: 600;
    margin-bottom: 6px;
}
.empty-state-text {
    color: var(--gl-muted);
    font-size: 0.92rem;
    max-width: 420px;
    margin: 0 auto 1.25rem;
    line-height: 1.5;
}

.followup-section {
    margin: 1.25rem 0 0.5rem;
    padding: 1rem 0 0;
    border-top: 1px dashed var(--gl-border);
    animation: fadeIn 0.4s ease-out;
}

.stAlert {
    border-radius: 12px !important;
    border: 1px solid #FFE0B2 !important;
    background: #FFF8F0 !important;
}

@keyframes fadeInDown {
    from { opacity: 0; transform: translateY(-12px); }
    to { opacity: 1; transform: translateY(0); }
}
@keyframes fadeInUp {
    from { opacity: 0; transform: translateY(10px); }
    to { opacity: 1; transform: translateY(0); }
}
@keyframes fadeIn {
    from { opacity: 0; }
    to { opacity: 1; }
}

::-webkit-scrollbar { width: 7px; }
::-webkit-scrollbar-thumb {
    background: #C4B8E0;
    border-radius: 4px;
}
::-webkit-scrollbar-thumb:hover { background: var(--gl-purple); }

a { color: var(--gl-purple) !important; }
a:hover { color: var(--gl-orange) !important; }

header[data-testid="stHeader"] {
    background: transparent !important;
}
footer,
[data-testid="stFooter"],
[data-testid="stStatusWidget"] {
    display: none !important;
    height: 0 !important;
    min-height: 0 !important;
    padding: 0 !important;
    visibility: hidden !important;
}
.stApp,
section[data-testid="stAppViewContainer"],
section[data-testid="stMain"] {
    background: var(--gl-bg-accent) !important;
}
</style>
""", unsafe_allow_html=True)


# Session Initialisation
def init_session():
    defaults = {
        "messages":        [],    # {role, content, sources, confidence, tokens, timestamp}
        "retriever":       None,
        "index_ready":     False,
        "top_k":           5,
        "temperature":     0.3,
        "show_sources":    True,
        "show_tokens":     True,
        "pending_query":   None,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_session()


# Load Retriever (cached)
@st.cache_resource(show_spinner=False)
def load_retriever():
    """Load the FAISS or Supabase retriever once and cache it."""
    from src.retriever import Retriever
    r = Retriever()
    r._load()
    return r

def check_index_ready() -> bool:
    from src.embeddings import index_exists
    return index_exists()


def format_timestamp() -> str:
    return datetime.datetime.now().strftime("%H:%M")

def render_confidence_badge(confidence: dict) -> str:
    label = confidence.get("label", "Low")
    score = confidence.get("score", 0)
    css   = {"High": "badge-high", "Medium": "badge-medium", "Low": "badge-low"}
    return (
        f'<span class="confidence-badge {css.get(label, "badge-low")}">'
        f'{label} confidence ({score:.0%})'
        f'</span>'
    )


def export_chat() -> str:
    lines = [f"GitLab Assistant - Chat Export - {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}\n"]
    lines.append("=" * 60)
    for msg in st.session_state.messages:
        role = "You" if msg["role"] == "user" else "Assistant"
        ts   = msg.get("timestamp", "")
        lines.append(f"\n[{ts}] {role}:")
        lines.append(msg["content"])
        if msg["role"] == "assistant" and msg.get("sources"):
            lines.append("\nSources:")
            for s in msg["sources"]:
                lines.append(f"  - {s['title']}: {s['url']}")
    return "\n".join(lines)


def render_suggestion_chips(questions: list[str], key_prefix: str) -> None:
    """Render clickable follow-up / starter question chips."""
    if not questions:
        return
    for i, q in enumerate(questions[:4]):
        if st.button(q, key=f"{key_prefix}_{i}", use_container_width=True):
            st.session_state.pending_query = q
            st.rerun()


# Initialize index and retriever
if check_index_ready():
    st.session_state.index_ready = True
    if st.session_state.retriever is None:
        st.session_state.retriever = load_retriever()
else:
    st.session_state.index_ready = False


# Hero header
status_class = "status-ready" if st.session_state.index_ready else "status-offline"
status_label = "Knowledge base ready" if st.session_state.index_ready else "Index not built"

st.markdown(
    f'''<div class="hero-card">
        <div class="hero-row">
            <div class="hero-brand">
                <div class="hero-logo">GL</div>
                <div>
                    <div class="main-header">GitLab Assistant</div>
                    <div class="sub-header">Handbook &amp; Product Direction · RAG-powered answers with citations</div>
                </div>
            </div>
            <span class="status-pill {status_class}">
                <span class="status-dot"></span>{status_label}
            </span>
        </div>
    </div>''',
    unsafe_allow_html=True,
)

_, hdr_right = st.columns([5, 1])
with hdr_right:
    if st.session_state.messages and st.button("Clear chat", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

st.markdown('<div class="chat-thread">', unsafe_allow_html=True)

# Empty state + starter suggestions
if not st.session_state.messages:
    st.markdown(
        '''<div class="empty-state">
            <div class="empty-state-icon">ASK</div>
            <div class="empty-state-title">What would you like to explore?</div>
            <div class="empty-state-text">
                Ask about GitLab policies, product direction, security, or culture.
                Pick a suggestion below or type your own question.
            </div>
        </div>''',
        unsafe_allow_html=True,
    )
    if st.session_state.index_ready:
        st.markdown('<p class="suggestions-label">Try asking</p>', unsafe_allow_html=True)
        s1, s2 = st.columns(2)
        with s1:
            render_suggestion_chips(DEFAULT_SUGGESTIONS[:2], "starter")
        with s2:
            render_suggestion_chips(DEFAULT_SUGGESTIONS[2:], "starter_b")

# Chat History
for msg in st.session_state.messages:
    if msg["role"] == "user":
        safe_content = html.escape(msg["content"]).replace("\n", "<br>")
        ts = html.escape(msg.get("timestamp", ""))
        st.markdown(
            f'<div class="user-message">'
            f'  <div class="user-bubble-wrap">'
            f'    <div class="user-bubble">{safe_content}</div>'
            f'    <div class="msg-time">{ts}</div>'
            f'  </div>'
            f'</div>',
            unsafe_allow_html=True,
        )
    else:
        ts = msg.get("timestamp", "")
        conf = msg.get("confidence", {})
        tokens = msg.get("tokens", {})
        sources = msg.get("sources", [])

        badge_html = render_confidence_badge(conf) if conf else ""
        token_html = ""
        if st.session_state.show_tokens and tokens:
            tp = tokens.get("prompt_tokens", 0)
            to = tokens.get("output_tokens", 0)
            token_html = f'<div class="token-info">Tokens - Prompt: {tp} | Output: {to}</div>'

        st.markdown(
            f'''<div class="bot-message">
                <div class="bot-avatar">GA</div>
                <div class="bot-bubble">''',
            unsafe_allow_html=True
        )
        
        st.markdown(msg["content"])
        
        st.markdown(
            f'''{badge_html}
                {token_html}
                </div>
            </div>''', 
            unsafe_allow_html=True
        )

        # Sources accordion
        if st.session_state.show_sources and sources:
            with st.expander(f"{len(sources)} Sources Used", expanded=False):
                for i, src in enumerate(sources, 1):
                    sim = src.get("similarity", 0)
                    text_preview = src.get("text", "")[:280].replace("\n", " ")
                    title = html.escape(src.get("title") or src["url"])
                    url = html.escape(src["url"])
                    st.markdown(
                        f'<div class="source-card">'
                        f'  <strong>Source {i}</strong> · '
                        f'  <a href="{url}" target="_blank" rel="noopener">{title}</a>'
                        f'  <span style="float:right; color:var(--gl-muted)">Relevance: {sim:.0%}</span>'
                        f'  <br><span style="color:var(--gl-muted)">{html.escape(text_preview)}…</span>'
                        f'</div>',
                        unsafe_allow_html=True,
                    )

st.markdown("</div>", unsafe_allow_html=True)

# Follow-up suggestions from last assistant reply
if st.session_state.messages:
    last = st.session_state.messages[-1]
    if last["role"] == "assistant" and st.session_state.index_ready:
        followups = last.get("suggested_questions") or []
        if followups:
            st.markdown(
                '<div class="followup-section">'
                '<p class="suggestions-label">Continue exploring</p></div>',
                unsafe_allow_html=True,
            )
            f1, f2 = st.columns(2)
            with f1:
                render_suggestion_chips(followups[:2], "followup")
            with f2:
                if len(followups) > 2:
                    render_suggestion_chips(followups[2:4], "followup_b")

# Chat Input
# Handle suggested question click
if st.session_state.pending_query:
    user_input = st.session_state.pending_query
    st.session_state.pending_query = None
else:
    user_input = st.chat_input(
        "Ask anything about GitLab's Handbook or Direction...",
        disabled=not st.session_state.index_ready,
    )

if not st.session_state.index_ready and not user_input:
    st.warning(
        "The knowledge base isn't built yet. "
        "Run `python scripts/build_index.py` first, then restart the app.",
    )


# Process Query
if user_input and st.session_state.index_ready:
    st.session_state.messages.append({
        "role":      "user",
        "content":   user_input,
        "timestamp": format_timestamp(),
    })
    st.rerun()

# Check if last message is from user (needs response)
if (
    st.session_state.messages
    and st.session_state.messages[-1]["role"] == "user"
    and st.session_state.index_ready
):
    query = st.session_state.messages[-1]["content"]

    with st.spinner(""):
        # Typing indicator
        typing_placeholder = st.empty()
        typing_placeholder.markdown(
            '<div class="bot-message">'
            '  <div class="bot-avatar">GA</div>'
            '  <div class="bot-bubble">'
            '    <div class="typing-indicator">'
            '      <span class="typing-dot"></span>'
            '      <span class="typing-dot"></span>'
            '      <span class="typing-dot"></span>'
            '    </div>'
            '  </div>'
            '</div>',
            unsafe_allow_html=True,
        )

        try:
            # 1. Guardrail check
            from src.guardrails import check_query, get_confidence_label, check_output
            guard = check_query(query)

            if not guard["allowed"]:
                typing_placeholder.empty()
                st.session_state.messages.append({
                    "role":      "assistant",
                    "content":   guard["reason"],
                    "timestamp": format_timestamp(),
                    "sources":   [],
                    "confidence": {"label": "Low", "score": 0},
                    "tokens":    {},
                })
                st.rerun()

            # 2. Retrieve relevant chunks
            retriever = st.session_state.retriever
            chunks = retriever.retrieve(query, top_k=st.session_state.top_k)

            # 3. Confidence scoring
            similarities = [c.get("similarity", 0) for c in chunks]
            confidence   = get_confidence_label(similarities)

            # 4. Build conversation history for multi-turn context
            history = []
            for m in st.session_state.messages[-8:]:
                if m["role"] == "user":
                    history.append({"role": "user", "content": m["content"]})
                elif m["role"] == "assistant":
                    history.append({"role": "model", "content": m["content"]})

            # 5. Generate response
            from src.llm import generate_response
            result = generate_response(
                question=query,
                context_chunks=chunks,
                temperature=st.session_state.temperature,
                conversation_history=history[:-1],  # exclude current turn
            )

            answer = result["answer"]

            # 6. Output safety check
            safety = check_output(answer)
            if not safety["safe"]:
                answer = "I encountered an issue generating a response. Please try rephrasing your question."

            typing_placeholder.empty()

            st.session_state.messages.append({
                "role":       "assistant",
                "content":    answer,
                "timestamp":  format_timestamp(),
                "sources":    chunks,
                "confidence": confidence,
                "suggested_questions": result.get("suggested_questions", []),
                "tokens": {
                    "prompt_tokens":  result.get("prompt_tokens", 0),
                    "output_tokens":  result.get("output_tokens", 0),
                },
            })

        except Exception as e:
            typing_placeholder.empty()
            error_msg = str(e)
            if "API_KEY" in error_msg.upper() or "api_key" in error_msg:
                response_text = (
                    "**API Key Error**: Please set your `GEMINI_API_KEY` in the `.env` file. "
                    "Get a free key at https://aistudio.google.com"
                )
            elif "quota" in error_msg.lower() or "429" in error_msg or "resource_exhausted" in error_msg.lower():
                response_text = (
                    "**Rate Limit Hit** - The Gemini API free tier allows 30 requests/minute. "
                    "Automatic retries were exhausted.\n\n"
                    "**Wait 60 seconds and try again** - the limit resets per minute "
                    "and normal chatting uses very few requests."
                )
            else:
                response_text = f"**Error**: {error_msg}\n\nPlease try again or restart the app."

            st.session_state.messages.append({
                "role":       "assistant",
                "content":    response_text,
                "timestamp":  format_timestamp(),
                "sources":    [],
                "confidence": {"label": "Low", "score": 0},
                "tokens":     {},
            })

    st.rerun()
