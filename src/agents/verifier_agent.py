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


VERIFIER_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """
You are the Verifier Agent for an Enterprise Knowledge
Operations system.

Your responsibility is to independently verify the Analyst's
claims and limitation against the retrieved enterprise evidence.

You MUST use only the provided enterprise evidence.

Do not use:
- General knowledge
- Internet information
- Assumptions
- External policies
- Information outside the evidence

FOR EACH CLAIM:

1. Check that every cited Evidence ID exists.
2. Read the cited evidence.
3. Determine whether the evidence directly establishes the claim.
4. Preserve the exact subject, population, scope, conditions,
   permissions, requirements, and exceptions stated by the evidence.
5. Do not accept evidence merely because it discusses the same topic.
6. Do not accept unsupported inference.
7. Do not transfer a statement from one population to another
   unless the evidence explicitly establishes that relationship.
8. A requirement does not automatically establish permission.
9. A procedure does not automatically establish eligibility.
10. A security control does not automatically establish authorization.
11. Absence of a prohibition does not establish permission.
12. Do not combine evidence to create a conclusion that the evidence
    itself does not establish.

CLAIM STATUS:

SUPPORTED:
The cited evidence directly establishes the claim.

NOT_SUPPORTED:
The evidence does not establish the claim.

INVALID_EVIDENCE:
One or more cited Evidence IDs do not exist.

LIMITATION:

The Analyst may provide a limitation describing information that
is not established by the retrieved evidence.

Verify that the limitation is consistent with the evidence.

A limitation such as:

"Whether contractors are permitted to work remotely is not
established by the provided evidence."

is valid if the evidence does not establish contractor
remote-work permission.

Do not treat a limitation as a factual claim requiring positive
evidence. Instead, determine whether the retrieved evidence
actually contains the information that the limitation says is
missing.

OVERALL DECISION:

PASS:
All substantive claims are supported and the limitation, if
present, is consistent with the evidence.

RETRY:
One or more substantive claims are not adequately supported, but
additional retrieval could reasonably provide the missing evidence.

REJECT:
A substantive claim is unsupported and the available evidence
does not establish it.

ACTION MUST MATCH THE VERDICT:

PASS  -> COMPLETE
RETRY -> RETRY
REJECT -> REJECT

Return ONLY valid JSON.

Use exactly this structure:

{{
  "claims": [
    {{
      "claim": "claim text",
      "evidence_ids": ["E1"],
      "status": "SUPPORTED",
      "reason": "explanation"
    }}
  ],
  "limitation": {{
    "text": "limitation text",
    "valid": true,
    "reason": "explanation"
  }},
  "overall_verdict": "PASS",
  "action": "COMPLETE",
  "reason": "overall verification reasoning"
}}
"""),
    ("human", """
User Question:
{question}

Analyst Claims:
{claims}

Analyst Limitation:
{limitation}

Retrieved Enterprise Evidence:
{evidence}

Independently verify the Analyst output against the evidence.
""")
])


def verify_answer(
    question: str,
    claims: str,
    limitation: str,
    evidence: str
):

    messages = VERIFIER_PROMPT.format_messages(
        question=question,
        claims=claims,
        limitation=limitation,
        evidence=evidence
    )

    response = llm.invoke(messages)

    return response.content


if __name__ == "__main__":

    question = (
        "Can contractors work remotely while handling "
        "restricted information?"
    )

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

    evidence = """
Evidence ID: E1
Source: Remote_Work_Policy.pdf
Page: 1

Content:
Eligible employees may work remotely up to 3 days per week
with manager approval. Employees handling confidential or
restricted information remotely must use company-approved
devices, secure networks, and approved tools.

---

Evidence ID: E2
Source: Information_Security_Policy.pdf
Page: 1

Content:
This policy defines minimum information-security requirements
for employees and contractors accessing TechNova Solutions
information and systems.

Remote access to restricted systems must use a
company-approved secure access mechanism. MFA is required
where enabled.

---

Evidence ID: E3
Source: Contractor_Engagement_Policy.pdf
Page: 1

Content:
Contractors are not eligible for employee annual leave.
Contractor time off is subject to project requirements and
manager approval.
"""

    result = verify_answer(
        question,
        claims,
        limitation,
        evidence
    )

    print("\n===== VERIFIER OUTPUT =====")
    print(result)