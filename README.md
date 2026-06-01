# GitLab Handbook Assistant

An AI-powered chatbot to explore GitLab's Handbook and Product Direction through natural language — built with Google Gemini, RAG, and Streamlit.

---

## What's Built in the UI

### 1. Hero Header with Live Status Badge
- GitLab-branded header card with an orange-to-purple gradient accent bar
- Animated status pill that shows **"Knowledge base ready"** (green) or **"Index not built"** (red) in real time

### 2. Conversational Chat Interface
- **User messages** — right-aligned speech bubbles with an orange gradient and timestamp
- **Bot messages** — left-aligned bubbles with a `GA` avatar, markdown rendering, and smooth fade-in animation
- **Typing indicator** — three bouncing dots shown while the AI is generating a response

### 3. Confidence Badge
- Every AI response displays a **High / Medium / Low** confidence badge
- Color-coded (green / amber / red) and computed from retrieval similarity scores

### 4. Source Citations Panel
- Expandable accordion below each answer showing all retrieved GitLab pages
- Each source card displays: page title, URL link, relevance percentage, and a text excerpt
- Cards highlight on hover with a left-border colour shift

### 5. Suggestion Chips
- **Starter questions** shown on the empty state to help new users get going
- **Follow-up questions** auto-generated after each answer to continue the conversation
- Pill-shaped clickable buttons that pre-fill and submit the chat input

### 6. Token Usage Display
- Shown below each response: prompt tokens and output tokens used per query

### 7. Fixed Chat Input Bar
- Pinned to the bottom of the viewport at all times
- Focuses with a purple glow border; send button uses the GitLab orange gradient

### 8. Clear Chat Button
- One-click button to reset the conversation, visible only when chat history exists

---

## Quick Start

### Prerequisites
- Python 3.11
- A **free** Gemini API key from [Google AI Studio](https://aistudio.google.com)

### 1. Clone and Install

```bash
git clone <your-repo-url>
cd GitBot
pip install -r requirements.txt
```

### 2. Configure Environment

```env
GEMINI_API_KEY=your_key_here
```

### 3. Build the Knowledge Index

```bash
python scripts/build_index.py
```

### 4. Run the App

```bash
python -m streamlit run app.py
```

Opens at **http://localhost:8501**

---

*Built with Google Gemini, ChromaDB, and Streamlit*
