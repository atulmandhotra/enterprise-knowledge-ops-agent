import json
from pathlib import Path

from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI


# ============================================================
# Project Configuration
# ============================================================

BASE_DIR = Path(__file__).resolve().parents[2]

load_dotenv(
    BASE_DIR / ".env"
)


# ============================================================
# LLM
# ============================================================

llm = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0
)


# ============================================================
# Memory Agent Prompt
# ============================================================

MEMORY_PROMPT = ChatPromptTemplate.from_messages([
    (
        "system",
        """
You are the Memory Agent for an Enterprise Knowledge
Operations system.

Your responsibility is to use previous conversation turns
ONLY to understand conversational context.

You do NOT retrieve enterprise documents.

You do NOT answer the user's question.

You do NOT create enterprise policy facts.

You do NOT treat previous answers as authoritative evidence.

IMPORTANT:

Enterprise documents are the only authoritative source for
enterprise policy facts.

Memory may be used only for:
- understanding references such as "what about contractors?"
- understanding the topic of a follow-up question
- maintaining conversational continuity
- resolving references to previous questions

Memory must NOT be used to establish:
- policy rules
- permissions
- eligibility
- approvals
- limits
- requirements
- exceptions

If the current question is already clear, preserve it.

If the current question refers to previous conversation,
rewrite it as a standalone question using only the relevant
conversation context.

Do not add facts that are not present in the conversation.

Return ONLY valid JSON.

Use exactly this structure:

{{
    "resolved_question": "standalone version of the current question",
    "memory_used": true,
    "memory_summary": "brief description of the contextual information used"
}}

If no previous conversation is available:

{{
    "resolved_question": "original question",
    "memory_used": false,
    "memory_summary": ""
}}
"""
    ),
    (
        "human",
        """
Previous Conversation:
{conversation_history}

Current Question:
{question}

Resolve the current question using conversational context only.
"""
    )
])


# ============================================================
# Memory Agent
# ============================================================

def memory_agent(
    question: str,
    conversation_history: list
):
    """
    Resolve conversational references using previous turns.

    Memory is contextual only and is never treated as
    enterprise evidence.
    """

    if not conversation_history:

        return json.dumps(
            {
                "resolved_question": question,
                "memory_used": False,
                "memory_summary": "",
            }
        )

    messages = MEMORY_PROMPT.format_messages(
        conversation_history=json.dumps(
            conversation_history,
            indent=2
        ),
        question=question,
    )

    response = llm.invoke(
        messages
    )

    return response.content


# ============================================================
# Standalone Test
# ============================================================

if __name__ == "__main__":

    history = [
        {
            "question": (
                "What is the annual leave entitlement "
                "for regular full-time employees?"
            ),
            "answer": (
                "Regular full-time employees receive "
                "20 working days of annual leave."
            ),
        }
    ]

    question = "What about contractors?"

    result = memory_agent(
        question,
        history
    )

    print(
        "\n===== MEMORY AGENT OUTPUT ====="
    )

    print(result)