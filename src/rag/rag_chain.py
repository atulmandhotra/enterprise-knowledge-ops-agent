from pathlib import Path

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

from retriever import search_documents


BASE_DIR = Path(__file__).resolve().parents[2]
load_dotenv(BASE_DIR / ".env")


llm = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0
)


PROMPT = ChatPromptTemplate.from_messages([
    (
        "system",
        """
You are an Enterprise Knowledge Assistant.

Your job is to answer questions using ONLY the information
contained in the provided enterprise document context.

Rules:
1. Do not use your general knowledge.
2. Do not invent or assume information.
3. Every factual statement must be supported by the context.
4. If the context does not contain enough information to answer
   the question, respond exactly:

"I don't have enough information in the provided enterprise
documents to answer this question."

5. Include the source document name for your answer.
"""
    ),
    (
        "human",
        """
Question:
{question}

Enterprise Document Context:
{context}

Answer:
"""
    )
])


def answer_question(question: str):

    results = search_documents(question, k=4)

    context_parts = []

    for document, score in results:
        source = document.metadata.get("source", "Unknown")
        page = document.metadata.get("page", "Unknown")

        context_parts.append(
            f"""
Source: {source}
Page: {page}
Retrieval Score: {score}

Content:
{document.page_content}
"""
        )

    context = "\n---\n".join(context_parts)

    messages = PROMPT.format_messages(
        question=question,
        context=context
    )

    response = llm.invoke(messages)

    return response.content, results


if __name__ == "__main__":

    question = input("Enter your question: ")

    answer, results = answer_question(question)

    print("\nAnswer:")
    print(answer)

    print("\nSources:")

    for document, score in results:
        print(
            f"- {document.metadata.get('source')} "
            f"(Page {document.metadata.get('page')})"
        )