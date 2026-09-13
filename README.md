Enterprise Knowledge Ops Agent

An agentic AI system for answering complex enterprise policy questions using multi-agent orchestration, retrieval-augmented generation (RAG), conversational memory, independent validation, guardrails, and source attribution.

1. Project Objective

The Enterprise Knowledge Ops Agent answers questions using a local enterprise knowledge base of policy documents.

The system is designed to:

Plan how a question should be answered

Retrieve relevant enterprise evidence

Reason over retrieved evidence

Independently validate factual claims

Maintain conversational context across follow-up questions

Retry retrieval when verification identifies insufficient evidence

Refuse to invent information when the documents do not establish an answer

Provide source document and page attribution

Expose an execution trace for inspection

2. Architecture

User Question
      |
      v
Memory Agent
      |
      v
Planner Agent
      |
      v
Retriever Agent <---- Chroma Vector Database
      |
      v
Analyst Agent
      |
      v
Verifier Agent
      |
      +---- RETRY ----> Retriever Agent
      |
      +---- REJECT ---> Insufficient-information response
      |
      v
Finalizer
      |
      v
User Answer

Agent responsibilities

Agent

Responsibility

Memory

Resolves conversational references using previous turns

Planner

Determines the sequence of information-retrieval/reasoning actions

Retriever

Searches the enterprise vector database and returns evidence

Analyst

Extracts atomic claims supported by retrieved evidence

Verifier

Independently validates claims against evidence

Finalizer

Produces the final response using verified claims only

3. Important Grounding Principle

Conversational memory is context, not evidence.

The system follows this boundary:

Memory      -> conversational context
Retrieval   -> enterprise evidence
Analysis    -> candidate factual claims
Verification-> evidence validation
Finalizer   -> verified user response

Previous answers or memory entries cannot establish enterprise policy facts. Policy facts must be supported by retrieved enterprise documents and pass independent verification.

4. Technology Stack

Python

LangGraph

LangChain

OpenAI GPT-4o-mini

OpenAI text-embedding-3-small

Chroma

PyPDF

Streamlit

pytest

The application uses the OpenAI API directly.

5. Project Structure

enterprise-knowledge-ops-agent/
|
├── app.py
├── requirements.txt
├── pytest.ini
├── .env
├── .gitignore
|
├── documents/
|   ├── Employee_Leave_Policy.pdf
|   ├── Contractor_Engagement_Policy.pdf
|   ├── Remote_Work_Policy.pdf
|   ├── Information_Security_Policy.pdf
|   └── Expense_Reimbursement_Policy.pdf
|
├── chroma_db/
|
├── src/
|   ├── __init__.py
|   |
|   ├── agents/
|   |   ├── memory_agent.py
|   |   ├── planner.py
|   |   ├── retriever_agent.py
|   |   ├── analyst_agent.py
|   |   ├── verifier_agent.py
|   |   ├── finalizer_agent.py
|   |   └── graph.py
|   |
|   └── rag/
|       ├── __init__.py
|       ├── injest.py
|       ├── retriever.py
|       └── rag_chain.py
|
└── tests/
    └── test_unit_components.py

6. Setup

Create virtual environment

Windows PowerShell:

python -m venv .venv

Activate it:

.\.venv\Scripts\Activate.ps1

Install dependencies

pip install -r requirements.txt

If pytest is not already included:

pip install pytest

Configure OpenAI API key

Create a .env file in the project root:

OPENAI_API_KEY=your_api_key_here

Do not commit .env or expose the API key in the repository.

7. Ingest Enterprise Documents

Place the enterprise PDF documents in:

documents/

Create/recreate the Chroma database:

python .\src\rag\injest.py

The ingestion process:

PDF documents
      |
      v
PyPDFLoader
      |
      v
Page metadata
(source + human-readable page number)
      |
      v
Text chunking
      |
      v
OpenAI embeddings
      |
      v
Chroma vector database

8. Run the Application

From the project root:

streamlit run app.py

Open the local Streamlit URL displayed in the terminal, normally:

http://localhost:8501

The UI provides:

Question input

Grounded/verification status

Final answer

Execution summary

Sources

Conversational memory information

Agent execution flow

Detailed agent trace

9. Example Questions

Answerable question

What is the annual leave entitlement for regular full-time employees?

Expected behavior: retrieve the employee leave policy and provide the documented entitlement with source attribution.

Multi-turn memory example

First:

What is the annual leave entitlement for regular full-time employees?

Then:

What about contractors?

The Memory Agent resolves the follow-up using conversation context. The Retriever still retrieves the Contractor Engagement Policy before a factual answer is produced.

Insufficient-evidence example

What is the company's maternity leave entitlement?

Expected behavior: the system should not invent an entitlement when it is not established by the provided enterprise documents.

10. Evaluation

The current end-to-end evaluation suite contains 8 test cases covering:

Employee annual leave

Leave carry-forward

Contractor leave eligibility

Contractor unpaid time-off approval

Contractor remote-work question with insufficient evidence

Restricted-system remote-access security mechanism

Expense approval threshold

Maternity leave question with insufficient evidence

Current recorded result:

8 / 8 test cases passed
100% test-case pass rate

This is the pass rate for the current evaluation suite and should not be interpreted as a claim of universal real-world accuracy.

Run the evaluation with:

python .\src\evaluation.py

11. Unit Tests

The deterministic unit-test suite validates:

Evidence source extraction

Empty evidence handling

Finalizer filtering of unsupported claims

Finalizer rejection behavior

Run:

pytest -q

Current recorded execution:

4 passed in 0.03s

12. Guardrails

The system uses multiple controls to reduce unsupported answers:

Enterprise documents are the authoritative evidence source.

Analyst claims must be directly supported by retrieved evidence.

Population boundaries are preserved; employee rules are not automatically transferred to contractors.

Requirements are not automatically interpreted as permissions.

Evidence IDs are independently checked by the Verifier.

Unsupported claims can trigger RETRY or REJECT.

The Finalizer uses only verified claims.

Unknown or unsupported questions result in an explicit limitation.

Conversational memory is never treated as policy evidence.

Source document and page attribution are retained.

13. Observability

The LangGraph state records execution trace information.

The Streamlit interface exposes:

Memory Agent
Planner Agent
Retriever Agent
Analyst Agent
Verifier Agent
Retry (if required)
Finalizer

The detailed trace also exposes intermediate outputs for inspection and debugging.

14. Documentation

Supporting project documents include:

Architecture & Agent Flow

Evaluation & Guardrail Documentation

Unit Test Documentation

Architecture Diagram

Unit Test Execution Evidence

15. Scope

In scope

Local enterprise document ingestion

Vector search

Multi-agent orchestration

Conversational memory

Cross-document evidence retrieval

Evidence-based reasoning

Independent verification

Guardrails

Evaluation

Observability

Local Streamlit interface

Out of scope

Cloud/production deployment

Enterprise authentication and authorization

Model training or fine-tuning

Advanced frontend optimization

Production-scale infrastructure

16. Security Notes

Never commit:

.env
API keys
credentials
private enterprise documents

Recommended .gitignore entries:

.venv/
.env
__pycache__/
*.pyc
.pytest_cache/
chroma_db/

17. Key Design Principle

The application intentionally separates responsibilities:

Memory provides context. Retrieval provides evidence. Analysis identifies claims. Verification validates claims. Finalization communicates only verified information.

This separation supports grounded answers, explainability, governance, and controlled handling of unknown information.