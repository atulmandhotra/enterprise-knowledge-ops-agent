import json

from src.agents.graph import graph


# ============================================================
# Evaluation Test Cases
# ============================================================

TEST_CASES = [

    # ========================================================
    # Enterprise Knowledge Questions
    # ========================================================

    {
        "id": "Q1",
        "question": (
            "What is the annual leave entitlement "
            "for regular full-time employees?"
        ),
        "expected": "20 working days",
        "answerable": True,
    },

    {
        "id": "Q2",
        "question": (
            "How many unused annual leave days "
            "can employees carry forward?"
        ),
        "expected": "5 days",
        "answerable": True,
    },

    {
        "id": "Q3",
        "question": (
            "Are contractors eligible for "
            "employee annual leave?"
        ),
        "expected": "not eligible",
        "answerable": True,
    },

    {
        "id": "Q4",
        "question": (
            "What approval is required when a contractor "
            "requests more than 5 consecutive working "
            "days of unpaid time off?"
        ),
        "expected": (
            "project manager and business owner"
        ),
        "answerable": True,
    },

    {
        "id": "Q5",
        "question": (
            "Can contractors work remotely while handling "
            "restricted information?"
        ),
        "expected": "not established",
        "answerable": False,
    },

    {
        "id": "Q6",
        "question": (
            "What security mechanism is required for remote "
            "access to restricted systems?"
        ),
        "expected": (
            "company-approved secure access mechanism"
        ),
        "answerable": True,
    },

    {
        "id": "Q7",
        "question": (
            "What is the approval requirement for an expense "
            "above INR 25,000?"
        ),
        "expected": (
            "manager and department head approval"
        ),
        "answerable": True,
    },

    {
        "id": "Q8",
        "question": (
            "What is the company's maternity leave entitlement?"
        ),
        "expected": "not established",
        "answerable": False,
    },

    # ========================================================
    # Input Guardrail Questions
    # ========================================================

    {
        "id": "Q9",
        "question": "hi, hello",
        "expected": "GREETING",
        "answerable": True,
        "guardrail_category": "GREETING",
    },

    {
        "id": "Q10",
        "question": "what is the value of pi?",
        "expected": "OUT_OF_SCOPE",
        "answerable": True,
        "guardrail_category": "OUT_OF_SCOPE",
    },

    {
        "id": "Q11",
        "question": "tell me about Harry Potter",
        "expected": "OUT_OF_SCOPE",
        "answerable": True,
        "guardrail_category": "OUT_OF_SCOPE",
    },
]


# ============================================================
# Helper Functions
# ============================================================

def parse_verification(verification):
    """
    Parse the Verifier Agent JSON output.

    If the verifier returns invalid JSON, mark the
    verification as invalid instead of crashing evaluation.
    """

    if not verification:

        return {
            "overall_verdict": "NOT REQUIRED",
            "action": "GUARDRAIL",
            "claims": [],
            "limitation": {},
            "reason": "",
        }

    try:

        return json.loads(
            verification
        )

    except (
        json.JSONDecodeError,
        TypeError,
    ):

        return {
            "overall_verdict": "INVALID",
            "action": "REJECT",
            "claims": [],
            "limitation": {},
            "reason": (
                "Verifier output was not valid JSON."
            ),
        }


def count_evidence(evidence):
    """
    Count the number of Evidence IDs returned by the Retriever.
    """

    if not evidence:
        return 0

    return evidence.count(
        "Evidence ID:"
    )


# ============================================================
# Guardrail Evaluation
# ============================================================

def evaluate_guardrail(
    test_case,
    final_state,
    final_answer,
):
    """
    Evaluate Input Guardrail behavior.

    Checks:

    1. Correct guardrail classification.
    2. Correct response.
    3. No enterprise evidence retrieval.
    4. Verifier was not required.
    """

    expected_category = test_case.get(
        "guardrail_category"
    )

    input_guardrail = final_state.get(
        "input_guardrail",
        {},
    )

    actual_category = input_guardrail.get(
        "category",
        "UNKNOWN",
    )

    # --------------------------------------------------------
    # Classification Check
    # --------------------------------------------------------

    classification_pass = (
        actual_category == expected_category
    )

    # --------------------------------------------------------
    # Retrieval Check
    # --------------------------------------------------------

    evidence = final_state.get(
        "evidence",
        "",
    )

    evidence_count = count_evidence(
        evidence
    )

    no_retrieval = (
        evidence_count == 0
    )

    # --------------------------------------------------------
    # Response Check
    # --------------------------------------------------------

    answer = final_answer.lower()

    if expected_category == "GREETING":

        response_pass = (
            "hello" in answer
            and (
                "enterprise policies" in answer
                or "how can i help" in answer
            )
        )

    elif expected_category == "OUT_OF_SCOPE":

        response_pass = (
            "outside the scope" in answer
            or "out of scope" in answer
        )

    else:

        response_pass = True

    # --------------------------------------------------------
    # Verifier Check
    # --------------------------------------------------------

    verification = final_state.get(
        "verification",
        "",
    )

    verification_not_required = (
        not verification
    )

    # --------------------------------------------------------
    # Final Guardrail Result
    # --------------------------------------------------------

    return (
        classification_pass
        and no_retrieval
        and response_pass
        and verification_not_required
    )


# ============================================================
# Enterprise Answer Evaluation
# ============================================================

def evaluate_answer(
    test_case,
    final_answer,
):
    """
    Lightweight evaluation of the final answer.

    This function checks whether the answer contains the
    expected outcome for the specific evaluation case.

    It is intentionally separate from the Verifier.

    The Verifier checks:

        Is the claim supported by enterprise evidence?

    This function checks:

        Did the application produce the expected result?
    """

    answer = final_answer.lower()

    # ========================================================
    # Guardrail Cases
    # ========================================================

    if "guardrail_category" in test_case:

        return True

    # ========================================================
    # Unanswerable Questions
    # ========================================================

    if not test_case["answerable"]:

        refusal_indicators = [
            "not established",
            "does not establish",
            "don't have enough information",
            "do not have enough information",
            "not enough information",
            "cannot be determined",
            "cannot be established",
        ]

        return any(
            phrase in answer
            for phrase in refusal_indicators
        )

    # ========================================================
    # Q1 - Employee Annual Leave
    # ========================================================

    if test_case["id"] == "Q1":

        return (
            "20" in answer
            and "working days" in answer
            and "annual leave" in answer
        )

    # ========================================================
    # Q2 - Annual Leave Carry Forward
    # ========================================================

    if test_case["id"] == "Q2":

        return (
            "5" in answer
            and "carry forward" in answer
            and "annual leave" in answer
        )

    # ========================================================
    # Q3 - Contractor Annual Leave
    # ========================================================

    if test_case["id"] == "Q3":

        return (
            "contractor" in answer
            and "annual leave" in answer
            and (
                "not eligible" in answer
                or "not established" in answer
                or "does not establish" in answer
            )
        )

    # ========================================================
    # Q4 - Contractor Extended Unpaid Leave
    # ========================================================

    if test_case["id"] == "Q4":

        return (
            "project manager" in answer
            and "business owner" in answer
        )

    # ========================================================
    # Q5 - Contractor Remote Work
    # ========================================================

    if test_case["id"] == "Q5":

        return (
            "not established" in answer
            or "does not establish" in answer
        )

    # ========================================================
    # Q6 - Restricted System Remote Access
    # ========================================================

    if test_case["id"] == "Q6":

        return (
            "company-approved secure access mechanism"
            in answer
        )

    # ========================================================
    # Q7 - Expense Approval
    # ========================================================

    if test_case["id"] == "Q7":

        return (
            "manager" in answer
            and "department head" in answer
            and (
                "25,000" in answer
                or "25000" in answer
            )
        )

    # ========================================================
    # Fallback
    # ========================================================

    expected = test_case[
        "expected"
    ].lower()

    return expected in answer


# ============================================================
# Run Evaluation
# ============================================================

def run_evaluation():

    results = []

    print("\n")
    print("=" * 70)
    print(
        "ENTERPRISE KNOWLEDGE OPS AGENT - EVALUATION"
    )
    print("=" * 70)

    for test_case in TEST_CASES:

        print("\n")
        print("=" * 70)
        print(
            f"{test_case['id']}: "
            f"{test_case['question']}"
        )
        print("=" * 70)

        # ----------------------------------------------------
        # Initial Graph State
        # ----------------------------------------------------

        initial_state = {

            "question": test_case[
                "question"
            ],

            "conversation_history": [],

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

        # ----------------------------------------------------
        # Execute Graph
        # ----------------------------------------------------

        final_state = graph.invoke(
            initial_state
        )

        final_answer = final_state.get(
            "final_answer",
            "",
        )

        # ----------------------------------------------------
        # Input Guardrail
        # ----------------------------------------------------

        input_guardrail = final_state.get(
            "input_guardrail",
            {},
        )

        guardrail_category = input_guardrail.get(
            "category",
            "UNKNOWN",
        )

        # ----------------------------------------------------
        # Verification / Guardrail Status
        # ----------------------------------------------------

        if "guardrail_category" in test_case:

            # Guardrail requests intentionally bypass
            # Memory, Planner, Retriever, Analyst and Verifier.

            verdict = "NOT REQUIRED"
            action = "GUARDRAIL"

        else:

            verification = parse_verification(
                final_state.get(
                    "verification",
                    "",
                )
            )

            verdict = verification.get(
                "overall_verdict",
                "UNKNOWN",
            )

            action = verification.get(
                "action",
                "UNKNOWN",
            )

        # ----------------------------------------------------
        # Observability Metrics
        # ----------------------------------------------------

        retry_count = final_state.get(
            "retry_count",
            0,
        )

        evidence_count = count_evidence(
            final_state.get(
                "evidence",
                "",
            )
        )

        # ----------------------------------------------------
        # Evaluation Check
        # ----------------------------------------------------

        if "guardrail_category" in test_case:

            evaluation_pass = evaluate_guardrail(
                test_case,
                final_state,
                final_answer,
            )

        else:

            evaluation_pass = evaluate_answer(
                test_case,
                final_answer,
            )

        # ----------------------------------------------------
        # Display Result
        # ----------------------------------------------------

        print("\nFinal Answer:")
        print(
            final_answer
        )

        print("\nInput Guardrail:")
        print(
            guardrail_category
        )

        print("\nVerification Verdict:")
        print(
            verdict
        )

        print("\nVerification Action:")
        print(
            action
        )

        print("\nEvidence Chunks:")
        print(
            evidence_count
        )

        print("\nRetry Count:")
        print(
            retry_count
        )

        print("\nEvaluation Check:")
        print(
            "PASS"
            if evaluation_pass
            else "FAIL"
        )

        # ----------------------------------------------------
        # Store Result
        # ----------------------------------------------------

        results.append(
            {
                "id": test_case["id"],
                "question": test_case["question"],
                "expected": test_case["expected"],
                "answerable": test_case["answerable"],
                "guardrail_category": (
                    test_case.get(
                        "guardrail_category",
                        "",
                    )
                ),
                "actual_guardrail_category": (
                    guardrail_category
                ),
                "final_answer": final_answer,
                "verification_verdict": verdict,
                "verification_action": action,
                "retry_count": retry_count,
                "evidence_count": evidence_count,
                "evaluation_pass": evaluation_pass,
            }
        )

    # ========================================================
    # Overall Evaluation Summary
    # ========================================================

    total_tests = len(
        results
    )

    passed_tests = sum(
        1
        for result in results
        if result["evaluation_pass"]
    )

    failed_tests = (
        total_tests - passed_tests
    )

    pass_rate = (
        (
            passed_tests
            / total_tests
        ) * 100
        if total_tests > 0
        else 0
    )

    total_retries = sum(
        result["retry_count"]
        for result in results
    )

    total_evidence = sum(
        result["evidence_count"]
        for result in results
    )

    # ========================================================
    # Guardrail Summary
    # ========================================================

    guardrail_results = [
        result
        for result in results
        if result["guardrail_category"]
    ]

    guardrail_passed = sum(
        1
        for result in guardrail_results
        if result["evaluation_pass"]
    )

    guardrail_total = len(
        guardrail_results
    )

    guardrail_pass_rate = (
        (
            guardrail_passed
            / guardrail_total
        ) * 100
        if guardrail_total > 0
        else 0
    )

    # ========================================================
    # Print Overall Summary
    # ========================================================

    print("\n")
    print("=" * 70)
    print(
        "EVALUATION SUMMARY"
    )
    print("=" * 70)

    print(
        f"\nTotal Test Cases : "
        f"{total_tests}"
    )

    print(
        f"Passed           : "
        f"{passed_tests}"
    )

    print(
        f"Failed           : "
        f"{failed_tests}"
    )

    print(
        f"Pass Rate        : "
        f"{pass_rate:.2f}%"
    )

    print(
        f"Total Retries    : "
        f"{total_retries}"
    )

    print(
        f"Evidence Chunks  : "
        f"{total_evidence}"
    )

    print(
        f"\nGuardrail Tests  : "
        f"{guardrail_total}"
    )

    print(
        f"Guardrail Passed : "
        f"{guardrail_passed}"
    )

    print(
        f"Guardrail Rate   : "
        f"{guardrail_pass_rate:.2f}%"
    )

    # ========================================================
    # Per-Test Summary
    # ========================================================

    print("\n")
    print(
        "Test Case Results:"
    )
    print(
        "-" * 70
    )

    for result in results:

        status = (
            "PASS"
            if result["evaluation_pass"]
            else "FAIL"
        )

        print(
            f"{result['id']} | "
            f"{status} | "
            f"Verdict={result['verification_verdict']} | "
            f"Action={result['verification_action']} | "
            f"Retries={result['retry_count']} | "
            f"Evidence={result['evidence_count']}"
        )

    print(
        "-" * 70
    )

    return results


# ============================================================
# Entry Point
# ============================================================

if __name__ == "__main__":

    run_evaluation()