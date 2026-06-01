# Project Write-Up: GitLab Assistant

## 1. Project Overview

GitLab Assistant is a Generative AI-powered chatbot built to help users quickly navigate and understand GitLab's extensive Handbook and Product Direction pages. These resources are incredibly detailed but also quite large and unstructured, which makes finding specific information time-consuming.

The idea behind GitLab Assistant was simple: let users ask questions in plain English and get precise, relevant answers instantly - along with proper source references, confidence indicators, and safeguards to keep the conversation focused on GitLab-related topics.

**Live App:** https://gitbot-vre2lxvgauezzadpxafcwc.streamlit.app/

**GitHub Repo:** https://github.com/Manjeet2001/GitBot

## 2. Technical Stack and Key Decisions

### A. Frontend/UI - Streamlit

I chose Streamlit mainly because of its simplicity and speed when building AI-focused applications in Python. Compared to frameworks like React or even Gradio, Streamlit allowed me to quickly prototype and iterate without worrying about frontend complexity.

For the UI:
* I used `session_state` to manage chat history and maintain conversation flow.
* Added custom CSS for a clean minimal corporate theme.
* Integrated fonts (Inter) and UI elements like confidence badges and typing indicators to make the app feel more polished and interactive.

### B. Core LLM - Google Gemini 2.5 Flash

Gemini 2.5 Flash was selected primarily for its speed and large context window.

Since the project relies on Retrieval-Augmented Generation (RAG), I needed a model that could handle large chunks of contextual data without slowing down too much. Gemini performed well in:
* Following structured system instructions
* Maintaining conversation context across multiple turns
* Generating accurate responses grounded in provided data

It also offered a good balance between performance and latency compared to heavier models.

### C. Vector Database - ChromaDB

Instead of using cloud-based vector databases like Pinecone or Weaviate, I went with ChromaDB running locally.

Why this decision:
* No dependency on external services
* Lower latency (no network calls)
* Easy deployment on free-tier platforms like Streamlit Cloud

The database is stored locally in SQLite format, which keeps the architecture simple and portable.

## 3. Data Processing and Retrieval (RAG)

To make the chatbot useful, the biggest challenge was handling GitLab's large and complex documentation.

Here's how I approached it:
* **Data Extraction:** Built a custom Python pipeline to scrape content directly from GitLab's Handbook.
* **Chunking:** Since the pages are very large, I split them into smaller overlapping chunks. This helps preserve context while improving retrieval accuracy.
* **Embeddings:** Each chunk is converted into vector embeddings for semantic search.
* **Retrieval:** When a user asks a question, the system fetches the top relevant chunks from ChromaDB.
* **Generation:** These chunks are passed into the Gemini prompt so that responses are grounded in actual data rather than hallucinated.

## 4. Advanced Features and Challenges

### Multi-Layer Guardrails

To keep the chatbot focused only on GitLab-related queries, I implemented a three-layer filtering system:
* **Keyword Matching:** Quick checks against a predefined list of GitLab-specific terms
* **Regex Filtering:** Catches clearly irrelevant or malformed queries
* **LLM-Based Classification:** For ambiguous inputs, a lightweight Gemini call classifies whether the query is relevant before running the full pipeline

### Dynamic Confidence Scoring

To make responses more transparent, I added a confidence scoring system:
* Based on similarity scores of retrieved chunks
* Mapped into visual indicators:
  * High (green)
  * Medium (yellow)
  * Low (red)

This gives users a quick sense of how reliable the answer might be.

### Error Handling and Rate Limits

Handling API limits was another practical challenge. When the Gemini API returns a rate limit error (429), instead of crashing:
* The system retries automatically
* If retries fail, it shows a user-friendly message asking them to wait

This ensures the app remains stable and doesn't lose the conversation state.
