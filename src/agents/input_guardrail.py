import json
from pathlib import Path

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI


# ============================================================
# Environment Configuration
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
    temperature=0,
)


# ============================================================
# Guardrail Prompt
# ============================================================

SYSTEM_PROMPT = """
You are an input guardrail for an enterprise knowledge assistant.

Classify the user's message into exactly one category:

GREETING
- Simple greetings or casual conversation.
- Examples: hi, hello, hey, good morning, thanks.

ENTERPRISE_QUERY
- A question that could reasonably be answered using enterprise
  policies, procedures, rules, approvals, eligibility, security,
  leave, remote work, contractor, expense, or similar organizational
  knowledge.

OUT_OF_SCOPE
- Questions clearly unrelated to the enterprise knowledge base.
- Examples: general trivia, geography, entertainment, recipes,
  programming questions unrelated to this application, etc.

AMBIGUOUS
- The message is not clearly a greeting, enterprise question,
  or unrelated question.

Return JSON only:

{
  "category": "GREETING | ENTERPRISE_QUERY | OUT_OF_SCOPE | AMBIGUOUS",
  "reason": "short explanation"
}

Do not answer the user's question.
Only classify it.
"""


# ============================================================
# Input Classification
# ============================================================

def classify_input(question: str) -> dict:

    if not question or not question.strip():

        return {
            "category": "AMBIGUOUS",
            "reason": "The user input is empty.",
        }

    response = llm.invoke(
        [
            (
                "system",
                SYSTEM_PROMPT
            ),
            (
                "human",
                question.strip()
            ),
        ]
    )

    try:

        result = json.loads(
            response.content
        )

    except (
        json.JSONDecodeError,
        TypeError
    ):

        return {
            "category": "AMBIGUOUS",
            "reason": (
                "Input classification could not "
                "be parsed safely."
            ),
        }

    category = result.get(
        "category",
        "AMBIGUOUS"
    )

    if category not in {
        "GREETING",
        "ENTERPRISE_QUERY",
        "OUT_OF_SCOPE",
        "AMBIGUOUS",
    }:

        category = "AMBIGUOUS"

    return {
        "category": category,
        "reason": result.get(
            "reason",
            "No classification reason was provided.",
        ),
    }