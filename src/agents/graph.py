import json
from typing import TypedDict

from langgraph.graph import StateGraph, START, END

from src.agents.memory_agent import memory_agent
from src.agents.planner import create_plan
from src.agents.retriever_agent import retrieve_information
from src.agents.analyst_agent import analyze_evidence
from src.agents.verifier_agent import verify_answer
from src.agents.finalizer_agent import finalize_answer


# ============================================================
# Configuration
# ============================================================

MAX_RETRIES = 2


# ============================================================
# Agent State
# ============================================================

class AgentState(TypedDict):

    question: str

    conversation_history: list

    memory_result: str

    resolved_question: str

    plan: str

    evidence: str

    analyst_result: str

    verification: str

    verification_feedback: str

    retry_count: int

    final_answer: str

    trace: list


# ============================================================
# Memory Node
# ============================================================

def memory_node(state: AgentState):

    result = memory_agent(
        state["question"],
        state.get(
            "conversation_history",
            []
        )
    )

    try:

        memory_result = json.loads(
            result
        )

        resolved_question = memory_result.get(
            "resolved_question",
            state["question"]
        )

    except json.JSONDecodeError:

        memory_result = {
            "resolved_question": state["question"],
            "memory_used": False,
            "memory_summary": "",
        }

        resolved_question = state["question"]

    trace_entry = (
        "Memory Agent → completed"
    )

    return {
        "memory_result": json.dumps(
            memory_result
        ),
        "resolved_question": resolved_question,
        "trace": state.get("trace", []) + [
            trace_entry
        ],
    }


# ============================================================
# Planner Node
# ============================================================

def planner_node(state: AgentState):

    plan = create_plan(
        state["resolved_question"]
    )

    return {
        "plan": plan,
        "retry_count": 0,
        "verification_feedback": "",
        "trace": state.get("trace", []) + [
            "Planner Agent → completed"
        ],
    }


# ============================================================
# Retriever Node
# ============================================================

def retriever_node(state: AgentState):

    evidence = retrieve_information(
        state["resolved_question"],
        state["plan"],
        state["verification_feedback"]
    )

    return {
        "evidence": evidence,
        "trace": state.get("trace", []) + [
            "Retriever Agent → completed"
        ],
    }


# ============================================================
# Analyst Node
# ============================================================

def analyst_node(state: AgentState):

    analyst_result = analyze_evidence(
        state["resolved_question"],
        state["evidence"]
    )

    return {
        "analyst_result": analyst_result,
        "trace": state.get("trace", []) + [
            "Analyst Agent → completed"
        ],
    }


# ============================================================
# Verifier Node
# ============================================================

def verifier_node(state: AgentState):

    analyst_result = json.loads(
        state["analyst_result"]
    )

    claims = json.dumps(
        analyst_result["claims"]
    )

    limitation = analyst_result.get(
        "limitation",
        ""
    )

    verification = verify_answer(
        state["resolved_question"],
        claims,
        limitation,
        state["evidence"]
    )

    return {
        "verification": verification,
        "verification_feedback": verification,
        "trace": state.get("trace", []) + [
            "Verifier Agent → completed"
        ],
    }


# ============================================================
# Verification Router
# ============================================================

def verification_router(state: AgentState):

    verification = json.loads(
        state["verification"]
    )

    action = verification.get(
        "action",
        "REJECT"
    ).upper()

    retry_count = state["retry_count"]

    if action == "COMPLETE":

        return "complete"

    if (
        action == "RETRY"
        and retry_count < MAX_RETRIES
    ):

        return "retry"

    return "reject"


# ============================================================
# Retry Node
# ============================================================

def retry_node(state: AgentState):

    new_count = (
        state["retry_count"] + 1
    )

    print(
        f"\n===== RETRY {new_count} ====="
    )

    return {
        "retry_count": new_count,
        "trace": state.get("trace", []) + [
            f"Retry → retrieval attempt {new_count}"
        ],
    }


# ============================================================
# Finalizer Node
# ============================================================

def finalizer_node(state: AgentState):

    analyst_result = json.loads(
        state["analyst_result"]
    )

    claims = json.dumps(
        analyst_result["claims"]
    )

    limitation = analyst_result.get(
        "limitation",
        ""
    )

    final_answer = finalize_answer(
        claims,
        limitation,
        state["verification"],
        state["evidence"]
    )

    return {
        "final_answer": final_answer,
        "trace": state.get("trace", []) + [
            "Finalizer Agent → completed"
        ],
    }


# ============================================================
# Build Graph
# ============================================================

builder = StateGraph(
    AgentState
)


builder.add_node(
    "memory",
    memory_node
)

builder.add_node(
    "planner",
    planner_node
)

builder.add_node(
    "retriever",
    retriever_node
)

builder.add_node(
    "analyst",
    analyst_node
)

builder.add_node(
    "verifier",
    verifier_node
)

builder.add_node(
    "retry",
    retry_node
)

builder.add_node(
    "finalizer",
    finalizer_node
)


# ============================================================
# Graph Flow
# ============================================================

builder.add_edge(
    START,
    "memory"
)

builder.add_edge(
    "memory",
    "planner"
)

builder.add_edge(
    "planner",
    "retriever"
)

builder.add_edge(
    "retriever",
    "analyst"
)

builder.add_edge(
    "analyst",
    "verifier"
)


builder.add_conditional_edges(
    "verifier",
    verification_router,
    {
        "complete": "finalizer",
        "retry": "retry",
        "reject": "finalizer",
    }
)


builder.add_edge(
    "retry",
    "retriever"
)

builder.add_edge(
    "finalizer",
    END
)


# ============================================================
# Compile
# ============================================================

graph = builder.compile()


# ============================================================
# Standalone Test
# ============================================================

if __name__ == "__main__":

    initial_state = {

        "question": (
            "What about contractors?"
        ),

        "conversation_history": [
            {
                "question": (
                    "What is the annual leave "
                    "entitlement for regular "
                    "full-time employees?"
                ),
                "answer": (
                    "Regular full-time employees "
                    "receive 20 working days of "
                    "annual leave."
                ),
            }
        ],

        "memory_result": "",

        "resolved_question": "",

        "plan": "",

        "evidence": "",

        "analyst_result": "",

        "verification": "",

        "verification_feedback": "",

        "retry_count": 0,

        "final_answer": "",

        "trace": [],
    }

    final_state = graph.invoke(
        initial_state
    )

    print(
        "\n===== MEMORY ====="
    )

    print(
        final_state["memory_result"]
    )

    print(
        "\n===== RESOLVED QUESTION ====="
    )

    print(
        final_state["resolved_question"]
    )

    print(
        "\n===== PLAN ====="
    )

    print(
        final_state["plan"]
    )

    print(
        "\n===== TRACE ====="
    )

    for item in final_state["trace"]:

        print(
            f"✓ {item}"
        )

    print(
        "\n===== FINAL ANSWER ====="
    )

    print(
        final_state["final_answer"]
    )