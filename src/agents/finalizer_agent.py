import json
import re


def extract_evidence_sources(evidence: str) -> dict:
    """
    Extract Evidence ID -> source/page mapping from the
    Retriever output.

    Example:

        E1 -> Remote_Work_Policy.pdf, Page 0
    """

    sources = {}

    if not evidence:
        return sources

    pattern = re.compile(
        r"Evidence ID:\s*(E\d+).*?"
        r"Source:\s*(.*?)\s*"
        r"Page:\s*(.*?)\s*"
        r"Retrieval Score:",
        re.DOTALL
    )

    matches = pattern.findall(evidence)

    for evidence_id, source, page in matches:
        sources[evidence_id] = {
            "source": source.strip(),
            "page": page.strip(),
        }

    return sources


def finalize_answer(
    claims: str,
    limitation: str,
    verification: str,
    evidence: str = ""
) -> str:
    """
    Construct the final user-facing answer using only
    information that has passed verification.

    The Finalizer:
    - does not call an LLM
    - does not retrieve documents
    - does not perform reasoning
    - uses only VERIFIED claims
    - attaches Evidence IDs and source information
    """

    # ---------------------------------------------------------
    # Parse verifier output
    # ---------------------------------------------------------

    try:
        verification_result = json.loads(
            verification
        )

    except json.JSONDecodeError:
        return (
            "I don't have enough information in the provided "
            "enterprise documents to answer this question confidently.\n\n"
            "Reason: The verification result could not be interpreted."
        )

    action = verification_result.get(
        "action",
        "REJECT"
    ).upper()

    # ---------------------------------------------------------
    # If verification did not complete successfully,
    # do not use unverified claims.
    # ---------------------------------------------------------

    if action != "COMPLETE":

        reason = verification_result.get(
            "reason",
            "The provided enterprise documents do not establish "
            "the requested information."
        )

        return (
            "I don't have enough information in the provided "
            "enterprise documents to answer this question confidently.\n\n"
            f"Reason: {reason}"
        )

    # ---------------------------------------------------------
    # Build Evidence ID -> Source mapping
    # ---------------------------------------------------------

    evidence_sources = extract_evidence_sources(
        evidence
    )

    # ---------------------------------------------------------
    # Get VERIFIED claims from Verifier
    # ---------------------------------------------------------

    verified_claims = verification_result.get(
        "claims",
        []
    )

    answer_parts = []
    source_references = []

    for item in verified_claims:

        status = item.get(
            "status",
            ""
        ).upper()

        claim = item.get(
            "claim",
            ""
        ).strip()

        evidence_ids = item.get(
            "evidence_ids",
            []
        )

        # -----------------------------------------------------
        # Only include claims explicitly marked SUPPORTED
        # -----------------------------------------------------

        if status != "SUPPORTED" or not claim:
            continue

        answer_parts.append(
            claim
        )

        # -----------------------------------------------------
        # Collect source information for this claim
        # -----------------------------------------------------

        claim_sources = []

        for evidence_id in evidence_ids:

            source_info = evidence_sources.get(
                evidence_id
            )

            if source_info:

                source = source_info["source"]
                page = source_info["page"]

                claim_sources.append(
                    f"{source}, Page {page}"
                )

                source_references.append(
                    (
                        evidence_id,
                        source,
                        page
                    )
                )

        if claim_sources:

            answer_parts.append(
                f"[Source: {'; '.join(claim_sources)}]"
            )

    # ---------------------------------------------------------
    # Add verified limitation
    # ---------------------------------------------------------

    verified_limitation = verification_result.get(
        "limitation",
        {}
    )

    if isinstance(
        verified_limitation,
        dict
    ):

        limitation_valid = verified_limitation.get(
            "valid",
            False
        )

        limitation_text = verified_limitation.get(
            "text",
            ""
        ).strip()

        if limitation_valid and limitation_text:

            answer_parts.append(
                limitation_text
            )

    # ---------------------------------------------------------
    # Safety fallback
    # ---------------------------------------------------------

    if not answer_parts:

        return (
            "I don't have enough information in the provided "
            "enterprise documents to answer this question confidently."
        )

    # ---------------------------------------------------------
    # Construct final answer
    # ---------------------------------------------------------

    return " ".join(
        answer_parts
    )


# =============================================================
# Standalone Test
# =============================================================

if __name__ == "__main__":

    claims = """
    [
      {
        "claim": "Remote access to restricted systems must use a company-approved secure access mechanism.",
        "evidence_ids": ["E2"]
      },
      {
        "claim": "MFA is required where enabled for remote access to restricted systems.",
        "evidence_ids": ["E2"]
      }
    ]
    """

    limitation = (
        "Whether contractors are permitted to work remotely while "
        "handling restricted information is not established by the "
        "provided evidence."
    )

    verification = """
    {
      "claims": [
        {
          "claim": "Remote access to restricted systems must use a company-approved secure access mechanism.",
          "evidence_ids": ["E2"],
          "status": "SUPPORTED",
          "reason": "The evidence directly supports the claim."
        },
        {
          "claim": "MFA is required where enabled for remote access to restricted systems.",
          "evidence_ids": ["E2"],
          "status": "SUPPORTED",
          "reason": "The evidence directly supports the claim."
        }
      ],
      "limitation": {
        "text": "Whether contractors are permitted to work remotely while handling restricted information is not established by the provided evidence.",
        "valid": true,
        "reason": "The evidence does not establish contractor remote-work permission."
      },
      "overall_verdict": "PASS",
      "action": "COMPLETE",
      "reason": "All claims are supported and the limitation is consistent with the evidence."
    }
    """

    evidence = """
Evidence ID: E2

Source: Information_Security_Policy.pdf
Page: 0
Retrieval Score: 0.75

Content:
Remote access to restricted systems must use the company-approved
secure access mechanism and multi-factor authentication where enabled.
"""

    result = finalize_answer(
        claims,
        limitation,
        verification,
        evidence
    )

    print("\n===== FINALIZER OUTPUT =====")
    print(result)