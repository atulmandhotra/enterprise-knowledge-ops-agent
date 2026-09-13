from pathlib import Path
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

BASE_DIR = Path(__file__).resolve().parents[2]
load_dotenv(BASE_DIR / ".env")


llm = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0
)


PLANNER_PROMPT = ChatPromptTemplate.from_messages([
    (
        "system",
        """
You are the Planning Agent for an Enterprise Knowledge
Operations system.

Your job is to analyze the user's question and create a
minimal execution plan for answering it using ONLY the
enterprise documents available in the knowledge base.

Do NOT answer the user's question.

Do NOT invent:
- document names
- policy names
- section names
- rules
- requirements
- eligibility criteria
- exceptions
- facts not explicitly known from the question

Do NOT use or request:
- Internet searches
- External websites
- Labor laws
- Industry benchmarks
- General knowledge
- Information outside the enterprise knowledge base

Describe required documents only by their topic or the
information that needs to be retrieved.

Do not assume that a particular section, rule, exception,
or variation exists unless it is explicitly indicated by
the user's question.

For simple questions, create only the minimum steps needed.

For complex questions involving multiple topics or policies,
identify the separate information that must be retrieved and
the reasoning/comparison that may be required.

Return a numbered list of concise execution steps.
"""
    ),
    (
        "human",
        """
User Question:
{question}

Create the execution plan.
"""
    )
])


def create_plan(question: str):
    messages = PLANNER_PROMPT.format_messages(
        question=question
    )

    response = llm.invoke(messages)

    return response.content


if __name__ == "__main__":
    question = input("Enter your question: ")

    plan = create_plan(question)

    print("\nExecution Plan:\n")
    print(plan)