import json

from src.agents.finalizer_agent import (
    extract_evidence_sources,
    finalize_answer,
)


def test_extract_evidence_sources():

    evidence = """
Evidence ID: E1
Source: Employee_Leave_Policy.pdf
Page: 1
Retrieval Score: 0.42

Content:
Regular full-time employees receive 20 working days.

---

Evidence ID: E2
Source: Contractor_Engagement_Policy.pdf
Page: 1
Retrieval Score: 0.51

Content:
Contractors are not eligible for employee annual leave.
"""

    result = extract_evidence_sources(
        evidence
    )

    assert result["E1"]["source"] == (
        "Employee_Leave_Policy.pdf"
    )

    assert result["E1"]["page"] == "1"

    assert result["E2"]["source"] == (
        "Contractor_Engagement_Policy.pdf"
    )

    assert result["E2"]["page"] == "1"


def test_extract_evidence_sources_empty():

    result = extract_evidence_sources(
        ""
    )

    assert result == {}


def test_finalizer_uses_only_supported_claims():

    claims = json.dumps([
        {
            "claim": (
                "20 working days of annual leave."
            ),
            "evidence_ids": ["E1"],
        },
        {
            "claim": "Unsupported claim.",
            "evidence_ids": ["E2"],
        },
    ])

    verification = json.dumps({

        "claims": [

            {
                "claim": (
                    "20 working days of annual leave."
                ),
                "evidence_ids": ["E1"],
                "status": "SUPPORTED",
                "reason": "Directly supported.",
            },

            {
                "claim": "Unsupported claim.",
                "evidence_ids": ["E2"],
                "status": "NOT_SUPPORTED",
                "reason": (
                    "Not established by evidence."
                ),
            },

        ],

        "limitation": {
            "text": "",
            "valid": False,
            "reason": "",
        },

        "overall_verdict": "PASS",

        "action": "COMPLETE",

        "reason": (
            "All substantive claims used "
            "are supported."
        ),
    })

    evidence = """
Evidence ID: E1
Source: Employee_Leave_Policy.pdf
Page: 1
Retrieval Score: 0.40

Content:
Regular full-time employees receive 20 working days.
"""

    result = finalize_answer(
        claims=claims,
        limitation="",
        verification=verification,
        evidence=evidence,
    )

    assert (
        "20 working days of annual leave."
        in result
    )

    assert (
        "Unsupported claim."
        not in result
    )

    assert (
        "Employee_Leave_Policy.pdf"
        in result
    )

    assert "Page 1" in result


def test_finalizer_rejects_incomplete_verification():

    verification = json.dumps({

        "claims": [],

        "limitation": {},

        "overall_verdict": "REJECT",

        "action": "REJECT",

        "reason": (
            "Evidence does not establish "
            "the requested information."
        ),
    })

    result = finalize_answer(
        claims="[]",
        limitation="",
        verification=verification,
        evidence="",
    )

    assert (
        "don't have enough information"
        in result.lower()
    )