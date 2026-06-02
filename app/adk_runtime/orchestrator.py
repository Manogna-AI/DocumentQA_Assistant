"""
Orchestrator Agent — Intent Classification + Routing + Multi-Intent

All agents use: from google.adk.agents import Agent
Multi-intent handled via classify_intents tool on the orchestrator.
"""

import os
import re
from app.config import settings
from google.adk.agents import Agent
from .ingestion_agent import ingestion_agent
from .retrieval_agent import retrieval_agent
from .answering_agent import answering_agent

os.environ.setdefault("OLLAMA_API_BASE", settings.ollama_base_url)
MODEL = f"ollama_chat/{settings.ollama_chat_model}"
#MODEL = "gemini-2.0-flash"

# ═══════════════════════════════════════════════════════
# PRE-COMPILED REGEX PATTERNS (for performance & safety)
# ═══════════════════════════════════════════════════════

# Pattern for QA detection: questions starting with common interrogatives
QA_PATTERN = re.compile(
    r"^(what|why|how|when|where|who|explain|tell me|does|is|are|can|describe|compare|find|show)",
    re.IGNORECASE | re.MULTILINE
)

# Pattern for splitting compound questions on " and "
AND_SPLIT_PATTERN = re.compile(r"\s+and\s+", re.IGNORECASE)

# ✓ Use centralized config for max input length
MAX_USER_MESSAGE_LENGTH = settings.max_user_message_length  # 5KB limit

# ═══════════════════════════════════════════════════════
# ORCHESTRATOR TOOL — Multi-Intent Classification
# This is the ONLY tool the orchestrator has.
# It parses the user message and returns ordered intents.
# ═══════════════════════════════════════════════════════

def classify_intents(user_message: str) -> dict:
    """Analyze the user message and classify it into one or more intents.
    Returns ordered list of intents for sequential execution.

    Intent types:
      - upload: User wants to upload/ingest/process a document
      - summary: User wants a document summary or overview
      - qa: User is asking a specific question about the document
      - doc_context: User wants to select/switch a specific document

    Multi-intent examples:
      'Summarize the document and explain renewal clauses'
        → ['summary', 'qa']
      'Upload this file and then summarize it'
        → ['upload', 'summary']
      'What are payment terms and what is the liability cap?'
        → ['qa', 'qa']

    Args:
        user_message: The raw user input text.

    Returns:
        dict with intents list, sub_queries for each intent, and routing instructions.
        
    Security: Pre-compiled regex patterns prevent DoS. Input length validated.
    """
    
    # ✓ Input validation: Limit message length to prevent regex DoS
    if not user_message:
        return {
            "intent_count": 1,
            "intents": ["qa"],
            "sub_queries": [{"intent": "qa", "query": ""}],
            "routing_plan": ["Step: Transfer to retrieval_agent with query: '' (intent=qa)"],
            "is_multi_intent": False,
        }
    
    if len(user_message) > MAX_USER_MESSAGE_LENGTH:
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(
            "[classify_intents] User message exceeds max length: %d > %d. Truncating.",
            len(user_message), MAX_USER_MESSAGE_LENGTH
        )
        user_message = user_message[:MAX_USER_MESSAGE_LENGTH]
    
    text = user_message.strip().lower()
    intents = []
    sub_queries = []

    # ── Check for UPLOAD intent ──
    upload_keywords = ["upload", "ingest", "process", "index", "add document", "store", "import"]
    if any(k in text for k in upload_keywords):
        intents.append("upload")
        sub_queries.append({"intent": "upload", "query": user_message})

    # ── Check for SUMMARY intent ──
    summary_keywords = ["summary", "summarize", "summarise", "overview", "key points",
                        "brief", "highlights", "main topics", "gist", "outline"]
    if any(k in text for k in summary_keywords):
        intents.append("summary")
        sub_queries.append({"intent": "summary", "query": user_message})

    # ── Check for DOC_CONTEXT intent ──
    doc_ctx_keywords = ["latest document", "selected document", "this document",
                        "use only", "switch to", "current document"]
    if any(k in text for k in doc_ctx_keywords):
        intents.append("doc_context")
        sub_queries.append({"intent": "doc_context", "query": user_message})

    # ── Check for QA intent ──
    # Uses pre-compiled regex pattern (safe from DoS)
    has_question_mark = "?" in text

    if QA_PATTERN.search(text) or has_question_mark or not intents:
        # Check for compound QA ("X and Y")
        # Use pre-compiled split pattern
        parts = AND_SPLIT_PATTERN.split(text)
        
        if len(parts) > 1 and all(len(p.strip()) > 10 for p in parts):
            # Multiple distinct questions
            for part in parts:
                part = part.strip()
                if part and not any(k in part for k in upload_keywords + summary_keywords):
                    intents.append("qa")
                    sub_queries.append({"intent": "qa", "query": part})
        else:
            # Single QA
            if "qa" not in intents:
                intents.append("qa")
                sub_queries.append({"intent": "qa", "query": user_message})

    # If nothing matched, default to QA
    if not intents:
        intents.append("qa")
        sub_queries.append({"intent": "qa", "query": user_message})

    # ── Build routing instructions ──
    routing = []
    for sq in sub_queries:
        if sq["intent"] == "upload":
            routing.append(f"Step: Transfer to ingestion_agent with message: '{sq['query']}'")
        elif sq["intent"] in ("qa", "summary", "doc_context"):
            routing.append(
                f"Step: Transfer to retrieval_agent with query: '{sq['query']}' "
                f"(intent={sq['intent']}), then transfer to answering_agent"
            )

    return {
        "intent_count": len(sub_queries),
        "intents": intents,
        "sub_queries": sub_queries,
        "routing_plan": routing,
        "is_multi_intent": len(sub_queries) > 1,
    }


# ═══════════════════════════════════════════════════════
# ORCHESTRATOR AGENT
# ═══════════════════════════════════════════════════════

orchestrator = Agent(
    name="orchestrator",
    model=MODEL,
    description=(
        "Document Q&A Orchestrator — Handles greetings and general queries directly. "
        "Classifies document-related intents (UPLOAD, QA, SUMMARY, DOC_CONTEXT) "
        "and routes to task-specific agents. Handles multi-intent prompts sequentially."
    ),
    instruction=(
        "/n no think\n"
        "You are the Orchestrator for the Document Q&A Assistant.\n\n"

        "════════════════════════════════════════\n"
        "STEP 0: HANDLE GREETINGS & GENERAL QUERIES DIRECTLY\n"
        "════════════════════════════════════════\n\n"

        "For these types of messages, respond DIRECTLY — do NOT call any tools "
        "or transfer to any agent:\n\n"

        "- Greetings: hi, hello, hey, good morning, good evening, thanks, thank you\n"
        "  → Respond warmly. Example: 'Hello! I'm the Document Q&A Assistant. "
        "You can upload documents (PDF, DOCX, PPTX) and ask me questions about them. "
        "How can I help you today?'\n\n"

        "- About yourself: who are you, what can you do, help, what are your capabilities\n"
        "  → Explain your capabilities:\n"
        "    • Upload and index documents (PDF, DOCX, PPTX)\n"
        "    • Answer questions grounded in uploaded documents\n"
        "    • Summarize documents with citations\n"
        "    • Handle multiple documents\n\n"

        "- General conversation: how are you, what's up, goodbye, bye\n"
        "  → Respond naturally and briefly.\n\n"

        "- Simple factual questions NOT about uploaded documents:\n"
        "  → Politely redirect: 'I specialize in answering questions about your "
        "uploaded documents. Would you like to upload a document or ask about "
        "one you've already uploaded?'\n\n"

        "════════════════════════════════════════\n"
        "STEP 1: For DOCUMENT-RELATED queries, call classify_intents tool\n"
        "════════════════════════════════════════\n\n"

        "For any message about documents, uploads, questions about content, "
        "or summaries — call the classify_intents tool first.\n\n"

        "════════════════════════════════════════\n"
        "STEP 2: EXECUTE the routing plan\n"
        "════════════════════════════════════════\n\n"

        "Follow the routing_plan from classify_intents:\n\n"

        "For 'upload' intent:\n"
        "  → Transfer to ingestion_agent\n\n"

        "For 'qa' or 'summary' intent:\n"
        "  → Transfer to retrieval_agent FIRST\n"
        "  → After retrieval completes, transfer to answering_agent\n"
        "  → CRITICAL: retrieval_agent MUST run before answering_agent\n\n"

        "For 'doc_context' intent:\n"
        "  → Acknowledge, then transfer to retrieval_agent\n\n"

        "════════════════════════════════════════\n"
        "MULTI-INTENT HANDLING\n"
        "════════════════════════════════════════\n\n"

        "When multiple intents detected, execute EACH sequentially.\n\n"

        "Example: 'Summarize the document and explain renewal clauses'\n"
        "  1. retrieval_agent (broad) → answering_agent (summary)\n"
        "  2. retrieval_agent (focused) → answering_agent (renewal clauses)\n"
        "  3. Combine both results\n\n"

        "════════════════════════════════════════\n"
        "AMBIGUITY HANDLING\n"
        "════════════════════════════════════════\n\n"

        "- Multiple documents: Ask user to specify which one\n"
        "- Content not found: Say 'Not found in the document.'\n"
        "- Unclear intent: Ask clarifying question\n"
        "- NEVER hallucinate missing information\n\n"

        "════════════════════════════════════════\n"
        "RULES\n"
        "════════════════════════════════════════\n\n"

        "1. Greetings & general chat → respond DIRECTLY (no tools, no transfer)\n"
        "2. Document-related queries → call classify_intents, then route\n"
        "3. For QA/SUMMARY → retrieval_agent FIRST, then answering_agent\n"
        "4. For UPLOAD → ingestion_agent\n"
        "5. NEVER hallucinate document content\n"
        "6. Be friendly, concise, and helpful"
    ),
    tools=[classify_intents],
    sub_agents=[ingestion_agent, retrieval_agent, answering_agent],
)