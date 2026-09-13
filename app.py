import json
import re

import streamlit as st

from src.agents.graph import graph


# ============================================================
# Page Configuration
# ============================================================

st.set_page_config(
    page_title="Enterprise Knowledge Ops Agent",
    page_icon="📚",
    layout="wide",
)


# ============================================================
# Session Memory
# ============================================================

if "conversation_history" not in st.session_state:
    st.session_state.conversation_history = []


# ============================================================
# Helper Functions
# ============================================================

def parse_verification(verification_text):
    try:
        return json.loads(verification_text)

    except (json.JSONDecodeError, TypeError):
        return {
            "overall_verdict": "UNKNOWN",
            "action": "UNKNOWN",
            "claims": [],
            "limitation": {},
            "reason": "Verification output could not be interpreted.",
        }


def extract_sources(evidence):
    """
    Extract unique source documents and pages from
    Retriever evidence.
    """

    if not evidence:
        return []

    pattern = re.compile(
        r"Evidence ID:\s*(E\d+).*?"
        r"Source:\s*(.*?)\s*"
        r"Page:\s*(.*?)\s*"
        r"Retrieval Score:",
        re.DOTALL,
    )

    matches = pattern.findall(evidence)

    sources = []
    seen = set()

    for evidence_id, source, page in matches:

        source = source.strip()
        page = page.strip()

        key = (source, page)

        if key not in seen:

            seen.add(key)

            sources.append(
                {
                    "evidence_id": evidence_id,
                    "source": source,
                    "page": page,
                }
            )

    return sources


def get_verification_status(verification):

    verdict = verification.get(
        "overall_verdict",
        "UNKNOWN",
    )

    action = verification.get(
        "action",
        "UNKNOWN",
    )

    if verdict == "PASS" and action == "COMPLETE":
        return "GROUNDED"

    if action == "REJECT":
        return "NOT ESTABLISHED"

    return "REVIEW"


# ============================================================
# Header
# ============================================================

st.title("📚 Enterprise Knowledge Ops Agent")

st.caption(
    "Agentic enterprise knowledge assistant with "
    "retrieval, reasoning, verification, memory, "
    "and source attribution."
)

st.divider()


# ============================================================
# Conversation History
# ============================================================

if st.session_state.conversation_history:

    with st.expander(
        "💬 Conversation Memory"
    ):

        for index, turn in enumerate(
            st.session_state.conversation_history,
            start=1,
        ):

            st.markdown(
                f"**Turn {index}**"
            )

            st.write(
                f"**Question:** {turn['question']}"
            )

            st.write(
                f"**Answer:** {turn['answer']}"
            )

            st.divider()


# ============================================================
# Question
# ============================================================

st.subheader("Ask a Question")

question = st.text_area(
    "Enterprise Policy Question",
    placeholder=(
        "Example: What is the annual leave entitlement "
        "for regular full-time employees?"
    ),
    height=110,
    label_visibility="collapsed",
)


# ============================================================
# Execute Agent
# ============================================================

if st.button(
    "🔍 Ask Agent",
    type="primary",
):

    if not question.strip():

        st.warning(
            "Please enter a question."
        )

    else:

        # Keep a copy of the history before adding
        # the current question.
        previous_history = (
            st.session_state.conversation_history.copy()
        )

        with st.spinner(
            "Running the enterprise knowledge agent..."
        ):

            initial_state = {
                "question": question,

                "conversation_history": previous_history,

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

        # ====================================================
        # Extract State
        # ====================================================

        final_answer = final_state.get(
            "final_answer",
            "",
        )

        plan = final_state.get(
            "plan",
            "",
        )

        evidence = final_state.get(
            "evidence",
            "",
        )

        analyst_result = final_state.get(
            "analyst_result",
            "",
        )

        verification_text = final_state.get(
            "verification",
            "",
        )

        memory_result = final_state.get(
            "memory_result",
            "",
        )

        resolved_question = final_state.get(
            "resolved_question",
            question,
        )

        retry_count = final_state.get(
            "retry_count",
            0,
        )

        trace = final_state.get(
            "trace",
            [],
        )

        verification = parse_verification(
            verification_text
        )

        sources = extract_sources(
            evidence
        )

        status = get_verification_status(
            verification
        )

        # ====================================================
        # Save Conversation Memory
        # ====================================================

        st.session_state.conversation_history.append(
            {
                "question": question,
                "answer": final_answer,
            }
        )

        # ====================================================
        # Answer
        # ====================================================

        st.divider()

        st.subheader("Answer")

        if status == "GROUNDED":

            st.success(
                "✓ Grounded and verified against enterprise evidence"
            )

        elif status == "NOT ESTABLISHED":

            st.warning(
                "⚠ The requested information is not established "
                "by the available enterprise evidence."
            )

        else:

            st.info(
                "The result requires review."
            )

        st.write(
            final_answer
        )

        # ====================================================
        # Execution Summary
        # ====================================================

        st.subheader(
            "Execution Summary"
        )

        col1, col2, col3, col4 = st.columns(4)

        with col1:

            st.metric(
                "Verification",
                verification.get(
                    "overall_verdict",
                    "UNKNOWN",
                ),
            )

        with col2:

            st.metric(
                "Action",
                verification.get(
                    "action",
                    "UNKNOWN",
                ),
            )

        with col3:

            st.metric(
                "Retries",
                retry_count,
            )

        with col4:

            st.metric(
                "Sources",
                len(sources),
            )

        # ====================================================
        # Memory
        # ====================================================

        st.subheader(
            "🧠 Memory"
        )

        try:

            memory = json.loads(
                memory_result
            )

            memory_used = memory.get(
                "memory_used",
                False,
            )

            memory_summary = memory.get(
                "memory_summary",
                "",
            )

            if memory_used:

                st.info(
                    f"Memory used: {memory_summary}"
                )

                st.write(
                    "**Resolved Question:**"
                )

                st.write(
                    resolved_question
                )

            else:

                st.write(
                    "No previous conversation context was required."
                )

        except (json.JSONDecodeError, TypeError):

            st.write(
                "Memory result could not be interpreted."
            )

        # ====================================================
        # Sources
        # ====================================================

        st.subheader(
            "📖 Sources"
        )

        if sources:

            for source in sources:

                with st.expander(
                    f"{source['source']} — Page {source['page']}"
                ):

                    st.write(
                        f"**Evidence ID:** "
                        f"{source['evidence_id']}"
                    )

                    st.write(
                        "This source contributed evidence "
                        "used during analysis and verification."
                    )

        else:

            st.info(
                "No enterprise sources were identified."
            )

        # ====================================================
        # Agent Flow
        # ====================================================

        st.subheader(
            "🤖 Agent Execution"
        )

        flow_cols = st.columns(6)

        agents = [
            ("1", "Memory", "Context"),
            ("2", "Planner", "Plan"),
            ("3", "Retriever", "Retrieve"),
            ("4", "Analyst", "Analyze"),
            ("5", "Verifier", "Verify"),
            ("6", "Finalizer", "Answer"),
        ]

        for column, (
            number,
            name,
            description,
        ) in zip(
            flow_cols,
            agents,
        ):

            with column:

                st.markdown(
                    f"**{number}. {name}**"
                )

                st.caption(
                    description
                )

        # ====================================================
        # Detailed Trace
        # ====================================================

        with st.expander(
            "🔎 View Detailed Agent Trace"
        ):

            st.markdown(
                "### Execution Order"
            )

            for item in trace:

                st.write(
                    f"✓ {item}"
                )

            st.divider()

            st.markdown(
                "### Memory Agent"
            )

            st.code(
                memory_result,
                language="json",
            )

            st.markdown(
                "### Planner Agent"
            )

            st.code(
                plan,
                language="text",
            )

            st.markdown(
                "### Retriever Agent"
            )

            st.code(
                evidence,
                language="text",
            )

            st.markdown(
                "### Analyst Agent"
            )

            st.code(
                analyst_result,
                language="json",
            )

            st.markdown(
                "### Verifier Agent"
            )

            st.code(
                verification_text,
                language="json",
            )

            st.markdown(
                "### Finalizer"
            )

            st.write(
                "Constructed the final response using "
                "verified claims and validated limitations."
            )


# ============================================================
# Clear Conversation
# ============================================================

if st.session_state.conversation_history:

    st.divider()

    if st.button(
        "🗑️ Clear Conversation Memory"
    ):

        st.session_state.conversation_history = []

        st.rerun()