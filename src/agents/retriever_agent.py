from pathlib import Path

from dotenv import load_dotenv
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI

from src.rag.retriever import search_documents


# ---------------------------------------------------------
# Environment
# ---------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parents[2]
load_dotenv(BASE_DIR / ".env")


# ---------------------------------------------------------
# LLM
# ---------------------------------------------------------

llm = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0
)


# ---------------------------------------------------------
# Enterprise Document Search Tool
# ---------------------------------------------------------

@tool
def search_enterprise_documents(query: str) -> list:
    """
    Search the enterprise knowledge base for documents
    relevant to the given query.

    Returns raw evidence containing:
    - source document
    - page
    - retrieval score
    - document content
    """

    results = search_documents(
        query,
        k=4
    )

    if not results:
        return []

    evidence = []

    for document, score in results:

        source = document.metadata.get(
            "source",
            "Unknown"
        )

        page = document.metadata.get(
            "page",
            "Unknown"
        )

        evidence.append(
            {
                "source": source,
                "page": page,
                "score": score,
                "content": document.page_content
            }
        )

    return evidence


# ---------------------------------------------------------
# Bind Tool to LLM
# ---------------------------------------------------------

tools = [
    search_enterprise_documents
]

llm_with_tools = llm.bind_tools(tools)


# ---------------------------------------------------------
# Retriever Agent
# ---------------------------------------------------------

def retrieve_information(
    question: str,
    plan: str,
    verification_feedback: str = ""
):

    response = llm_with_tools.invoke(
        f"""
You are the Retriever Agent.

Your responsibility is to retrieve evidence from the
enterprise knowledge base.

User Question:
{question}

Execution Plan:
{plan}

Verification Feedback:
{verification_feedback}

Follow the execution plan.

If verification feedback is provided, use it to identify
what evidence was missing, insufficient, or incorrect
and retrieve better evidence.

You may call the search_enterprise_documents tool multiple
times when different pieces of evidence are required.

Do not answer the user's question.

Do not perform verification yourself.

Only retrieve evidence.
"""
    )

    # -----------------------------------------------------
    # No tool calls
    # -----------------------------------------------------

    if not response.tool_calls:
        return "No enterprise evidence was retrieved."


    # -----------------------------------------------------
    # Collect evidence from all tool calls
    # -----------------------------------------------------

    all_evidence = []

    for tool_call in response.tool_calls:

        tool_result = search_enterprise_documents.invoke(
            tool_call["args"]
        )

        all_evidence.extend(
            tool_result
        )


    # -----------------------------------------------------
    # Remove duplicate evidence
    # -----------------------------------------------------

    unique_evidence = []
    seen = set()

    for item in all_evidence:

        evidence_key = (
            item["source"],
            item["page"],
            item["content"].strip()
        )

        if evidence_key not in seen:

            seen.add(evidence_key)

            unique_evidence.append(
                item
            )


    # -----------------------------------------------------
    # Assign Evidence IDs
    # -----------------------------------------------------

    evidence = []

    for index, item in enumerate(
        unique_evidence,
        start=1
    ):

        evidence.append(
            f"""
Evidence ID: E{index}

Source: {item["source"]}
Page: {item["page"]}
Retrieval Score: {item["score"]}

Content:
{item["content"]}
"""
        )


    # -----------------------------------------------------
    # Return formatted evidence
    # -----------------------------------------------------

    if not evidence:
        return "No enterprise evidence was retrieved."

    return "\n---\n".join(
        evidence
    )


# ---------------------------------------------------------
# Standalone Test
# ---------------------------------------------------------

if __name__ == "__main__":

    question = (
        "Can contractors work remotely while handling "
        "restricted information?"
    )

    plan = """
1. Retrieve policies regarding contractor access to restricted information.
2. Retrieve remote work requirements.
3. Retrieve security requirements for restricted information.
"""

    result = retrieve_information(
        question,
        plan
    )

    print("\n===== RETRIEVED EVIDENCE =====")
    print(result)