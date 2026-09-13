from pathlib import Path

from dotenv import load_dotenv
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter


# ============================================================
# Project Configuration
# ============================================================

BASE_DIR = Path(__file__).resolve().parents[2]

load_dotenv(
    BASE_DIR / ".env"
)

DOCUMENTS_DIR = (
    BASE_DIR / "documents"
)

CHROMA_DIR = str(
    BASE_DIR / "chroma_db"
)


# ============================================================
# Load Documents
# ============================================================

def load_documents():
    """
    Load all PDF documents from the enterprise
    documents directory.
    """

    documents = []

    pdf_files = sorted(
        DOCUMENTS_DIR.glob("*.pdf")
    )

    if not pdf_files:
        raise FileNotFoundError(
            f"No PDF documents found in {DOCUMENTS_DIR}"
        )

    for pdf_file in pdf_files:

        print(
            f"Loading: {pdf_file.name}"
        )

        loader = PyPDFLoader(
            str(pdf_file)
        )

        pages = loader.load()

        for page in pages:

            # Store the document name
            page.metadata["source"] = (
                pdf_file.name
            )

            # PyPDFLoader uses zero-based page numbers.
            # Convert them to human-readable page numbers.
            page.metadata["page"] = (
                page.metadata.get("page", 0) + 1
            )

        documents.extend(
            pages
        )

    print(
        f"\nLoaded {len(documents)} pages."
    )

    return documents


# ============================================================
# Split Documents
# ============================================================

def split_documents(documents):
    """
    Split documents into smaller chunks for
    vector retrieval.
    """

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50,
    )

    chunks = text_splitter.split_documents(
        documents
    )

    print(
        f"Created {len(chunks)} document chunks."
    )

    return chunks


# ============================================================
# Create Chroma Vector Database
# ============================================================

def create_vector_store(chunks):
    """
    Create a new Chroma vector database
    containing the enterprise document chunks.
    """

    embeddings = OpenAIEmbeddings(
        model="text-embedding-3-small"
    )

    vector_store = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=CHROMA_DIR,
    )

    print(
        f"\nChroma vector database created at:"
        f"\n{CHROMA_DIR}"
    )

    return vector_store


# ============================================================
# Main Ingestion Pipeline
# ============================================================

def ingest_documents():

    print(
        "\n"
        + "=" * 60
    )

    print(
        "ENTERPRISE DOCUMENT INGESTION"
    )

    print(
        "=" * 60
    )

    documents = load_documents()

    chunks = split_documents(
        documents
    )

    create_vector_store(
        chunks
    )

    print(
        "\nIngestion completed successfully."
    )


# ============================================================
# Run Ingestion
# ============================================================

if __name__ == "__main__":

    ingest_documents()