from pathlib import Path
from dotenv import load_dotenv

from src.agents.planner import create_plan
from src.agents.retriever_agent import retrieve_information
from src.agents.analyst_agent import analyze_evidence
from src.agents.verifier_agent import verify_answer


BASE_DIR = Path(__file__).resolve().parents[2]
load_dotenv(BASE_DIR / ".env")


def run_workflow(question: str):

    # 1. Planning
    plan = create_plan(question)

    print("\n===== PLAN =====")
    print(plan)

    # 2. Retrieval
    evidence = retrieve_information(question, plan)

    print("\n===== EVIDENCE =====")
    print(evidence)

    # 3. Analysis
    draft_answer = analyze_evidence(
        question,
        evidence
    )

    print("\n===== DRAFT ANSWER =====")
    print(draft_answer)

    # 4. Verification
    verification = verify_answer(
        question,
        evidence,
        draft_answer
    )

    print("\n===== VERIFICATION =====")
    print(verification)

    return {
        "question": question,
        "plan": plan,
        "evidence": evidence,
        "draft_answer": draft_answer,
        "verification": verification
    }


if __name__ == "__main__":

    question = input("\nEnter your question: ")

    run_workflow(question)