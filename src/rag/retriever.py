from pathlib import Path

from dotenv import load_dotenv
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings


# Project root
BASE_DIR = Path(__file__).resolve().parents[2]

# Load environment variables
load_dotenv(BASE_DIR / ".env")

# Chroma database created during ingestion
CHROMA_DIR = str(BASE_DIR / "chroma_db")


def create_retriever():
    embeddings = OpenAIEmbeddings(
        model="text-embedding-3-small"
    )

    vector_store = Chroma(
        persist_directory=CHROMA_DIR,
        embedding_function=embeddings
    )

    return vector_store


def search_documents(query: str, k: int = 4):
    vector_store = create_retriever()

    results = vector_store.similarity_search_with_score(
        query,
        k=k
    )

    return results


if __name__ == "__main__":

    question = input("Enter your question: ")

    results = search_documents(question)

    print("\nRetrieved Documents:\n")

    for index, (document, score) in enumerate(results, start=1):

        print(f"--- Result {index} ---")
        print(f"Source: {document.metadata.get('source')}")
        print(f"Page: {document.metadata.get('page')}")
        print(f"Score: {score}")
        print(f"Content: {document.page_content}")
        print()