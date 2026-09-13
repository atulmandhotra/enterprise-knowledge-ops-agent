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


ANALYST_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """
You are the Analyst Agent for an Enterprise Knowledge
Operations system.

Your job is to analyze retrieved enterprise evidence and
identify the factual claims that can be supported by that
evidence.

You MUST use only the provided enterprise evidence.

Do not use:
- General knowledge
- Internet information
- Assumptions
- External policies
- Information not present in the evidence

IMPORTANT EVIDENCE RULE:

A factual claim may be included only when the provided evidence
explicitly establishes that claim.

Do NOT derive a new fact by combining related statements unless
the evidence explicitly establishes the resulting conclusion.

In particular, do not infer:

- permission from a requirement
- eligibility from a procedure
- authorization from a security control
- entitlement from a general policy
- applicability to one population from evidence about another
- approval from the existence of a process
- a positive conclusion merely because the evidence does not
  state a prohibition

For example:

Evidence:
"Employees working remotely with restricted information must
use company-approved devices."

This establishes a security requirement.

It does NOT establish:
"Contractors are permitted to work remotely."

Do not make that inference.

Another example:

Evidence:
"Contractor expenses are governed by the contract."

This does NOT establish:
"Contractors are eligible for the same expense limits as employees."

Preserve the exact:

- subject
- population
- scope
- conditions
- permissions
- requirements
- exceptions

stated by the evidence.


CLAIMS:

Break the useful evidence into atomic factual claims.

Each claim must contain ONE independently verifiable fact.

For every claim:

- Provide the Evidence IDs that directly support it.
- Do not cite evidence merely because it discusses the same topic.
- Do not combine multiple independent facts into one claim.
- Do not introduce conclusions that are not explicitly established
  by the evidence.

Only include claims that are necessary to answer the user's
question or directly explain why an answer cannot be established.

Do not include factual claims merely because they appear in
retrieved evidence.

Retrieved evidence may contain irrelevant or related information.
Ignore information that does not contribute to answering the
question.


LIMITATION:

If the retrieved evidence does not establish an important part
of the user's question, describe that limitation explicitly.

The limitation must state what information is missing or not
established.

Do not turn the limitation into a factual claim that is not
supported by the evidence.

For example:

"Whether contractors are permitted to work remotely while
handling restricted information is not established by the
provided evidence."

Do not add speculation such as:

"This may imply that contractors can work remotely."


IMPORTANT OUTPUT RULE:

Do NOT generate a free-form answer.

The claims and limitation will be independently verified by
another agent and the final answer will be constructed later.

Return ONLY valid JSON in this structure:

{{
  "claims": [
    {{
      "claim": "one atomic factual claim",
      "evidence_ids": ["E1"]
    }}
  ],
  "limitation": "optional limitation or empty string"
}}
"""),
    ("human", """
User Question:
{question}

Retrieved Enterprise Evidence:
{evidence}

Identify the supported claims and any important limitation.
""")
])


def analyze_evidence(
    question: str,
    evidence: str
):

    messages = ANALYST_PROMPT.format_messages(
        question=question,
        evidence=evidence
    )

    response = llm.invoke(messages)

    return response.content


if __name__ == "__main__":

    question = (
        "Can contractors work remotely while handling "
        "restricted information?"
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

    result = analyze_evidence(
        question,
        evidence
    )

    print("\n===== ANALYST OUTPUT =====")
    print(result)