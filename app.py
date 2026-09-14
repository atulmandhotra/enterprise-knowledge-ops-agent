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

    if not verification_text:
        return {
            "overall_verdict": "NOT REQUIRED",
            "action": "GUARDRAIL",
            "claims": [],
            "limitation": {},
            "reason": "",
        }

    try:

        return json.loads(
            verification_text
        )

    except (
        json.JSONDecodeError,
        TypeError
    ):

        return {
            "overall_verdict": "UNKNOWN",
            "action": "UNKNOWN",
            "claims": [],
            "limitation": {},
            "reason": (
                "Verification output could not "
                "be interpreted."
            ),
        }


def extract_sources(evidence):
    """
    Extract unique source documents and pages
    from Retriever evidence.
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

    matches = pattern.findall(
        evidence
    )

    sources = []
    seen = set()

    for evidence_id, source, page in matches:

        source = source.strip()
        page = page.strip()

        key = (
            source,
            page
        )

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


def get_execution_status(
    verification,
    input_guardrail
):

    category = input_guardrail.get(
        "category",
        ""
    )

    # --------------------------------------------------------
    # Guardrail handled request
    # --------------------------------------------------------

    if category == "GREETING":

        return {
            "verification": "NOT REQUIRED",
            "action": "GUARDRAIL",
            "message": (
                "✓ Request handled by input guardrail"
            ),
            "message_type": "success",
        }

    if category == "OUT_OF_SCOPE":

        return {
            "verification": "NOT REQUIRED",
            "action": "GUARDRAIL",
            "message": (
                "✓ Request blocked by input guardrail"
            ),
            "message_type": "info",
        }

    # --------------------------------------------------------
    # Normal enterprise workflow
    # --------------------------------------------------------

    verdict = verification.get(
        "overall_verdict",
        "UNKNOWN"
    )

    action = verification.get(
        "action",
        "UNKNOWN"
    )

    if verdict == "PASS" and action == "COMPLETE":

        return {
            "verification": "PASS",
            "action": "COMPLETE",
            "message": (
                "✓ Grounded and verified "
                "against enterprise evidence"
            ),
            "message_type": "success",
        }

    if action == "REJECT":

        return {
            "verification": "REJECT",
            "action": "REJECT",
            "message": (
                "⚠ The requested information "
                "is not established by the "
                "available enterprise evidence."
            ),
            "message_type": "warning",
        }

    return {
        "verification": verdict,
        "action": action,
        "message": (
            "The result requires review."
        ),
        "message_type": "info",
    }


# ============================================================
# Header
# ============================================================

st.title(
    "📚 Enterprise Knowledge Ops Agent"
)

st.caption(
    "Agentic enterprise knowledge assistant with "
    "input validation, retrieval, reasoning, "
    "verification, memory, and source attribution."
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

st.subheader(
    "Ask a Question"
)

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

        # Keep a copy of the history before
        # adding the current question.
        previous_history = (
            st.session_state.conversation_history.copy()
        )

        with st.spinner(
            "Running the enterprise knowledge agent..."
        ):

            initial_state = {

                "question": question,

                "conversation_history": (
                    previous_history
                ),

                "input_guardrail": {},

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

        input_guardrail = final_state.get(
            "input_guardrail",
            {},
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


        # ====================================================
        # Parse Results
        # ====================================================

        verification = parse_verification(
            verification_text
        )

        sources = extract_sources(
            evidence
        )

        execution_status = get_execution_status(
            verification,
            input_guardrail
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

        st.subheader(
            "Answer"
        )


        if execution_status["message_type"] == "success":

            st.success(
                execution_status["message"]
            )

        elif execution_status["message_type"] == "warning":

            st.warning(
                execution_status["message"]
            )

        else:

            st.info(
                execution_status["message"]
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
                execution_status[
                    "verification"
                ],
            )


        with col2:

            st.metric(
                "Action",
                execution_status[
                    "action"
                ],
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
        # Input Guardrail
        # ====================================================

        st.subheader(
            "🛡️ Input Guardrail"
        )

        guardrail_category = input_guardrail.get(
            "category",
            "UNKNOWN"
        )

        guardrail_reason = input_guardrail.get(
            "reason",
            ""
        )

        if guardrail_category == "GREETING":

            st.success(
                f"Classification: **{guardrail_category}**"
            )

            st.caption(
                guardrail_reason
            )

            st.write(
                "Enterprise retrieval was not required."
            )

        elif guardrail_category == "OUT_OF_SCOPE":

            st.info(
                f"Classification: **{guardrail_category}**"
            )

            st.caption(
                guardrail_reason
            )

            st.write(
                "Enterprise retrieval was intentionally skipped."
            )

        elif guardrail_category == "ENTERPRISE_QUERY":

            st.success(
                f"Classification: **{guardrail_category}**"
            )

            st.caption(
                guardrail_reason
            )

            st.write(
                "The request was routed to the enterprise "
                "knowledge workflow."
            )

        else:

            st.warning(
                f"Classification: **{guardrail_category}**"
            )

            st.caption(
                guardrail_reason
            )


        # ====================================================
        # Memory
        # ====================================================

        st.subheader(
            "🧠 Memory"
        )


        if memory_result:

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
                        "No previous conversation context "
                        "was required."
                    )


            except (
                json.JSONDecodeError,
                TypeError
            ):

                st.write(
                    "Memory result could not be interpreted."
                )

        else:

            st.write(
                "Memory Agent was not invoked because "
                "the input guardrail handled the request."
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
                    f"{source['source']} — "
                    f"Page {source['page']}"
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


        # ----------------------------------------------------
        # Guardrail-only execution
        # ----------------------------------------------------

        if guardrail_category in {
            "GREETING",
            "OUT_OF_SCOPE",
        }:

            flow_cols = st.columns(2)

            with flow_cols[0]:

                st.markdown(
                    "**1. Input Guardrail**"
                )

                st.caption(
                    "Validate / classify"
                )

            with flow_cols[1]:

                st.markdown(
                    "**2. Guardrail Response**"
                )

                st.caption(
                    "Handle request"
                )


        # ----------------------------------------------------
        # Normal enterprise execution
        # ----------------------------------------------------

        else:

            flow_cols = st.columns(7)

            agents = [

                (
                    "1",
                    "Input Guardrail",
                    "Validate"
                ),

                (
                    "2",
                    "Memory",
                    "Context"
                ),

                (
                    "3",
                    "Planner",
                    "Plan"
                ),

                (
                    "4",
                    "Retriever",
                    "Retrieve"
                ),

                (
                    "5",
                    "Analyst",
                    "Analyze"
                ),

                (
                    "6",
                    "Verifier",
                    "Verify"
                ),

                (
                    "7",
                    "Finalizer",
                    "Answer"
                ),
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


            # ------------------------------------------------
            # Input Guardrail
            # ------------------------------------------------

            st.markdown(
                "### Input Guardrail"
            )

            st.code(
                json.dumps(
                    input_guardrail,
                    indent=2,
                ),
                language="json",
            )


            # ------------------------------------------------
            # Guardrail-only request
            # ------------------------------------------------

            if guardrail_category in {
                "GREETING",
                "OUT_OF_SCOPE",
            }:

                st.markdown(
                    "### Guardrail Decision"
                )

                st.write(
                    "The request was handled by the "
                    "input guardrail. No enterprise "
                    "retrieval, analysis, or verification "
                    "was required."
                )


            # ------------------------------------------------
            # Normal enterprise workflow details
            # ------------------------------------------------

            else:

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