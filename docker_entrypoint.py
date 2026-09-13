import os
import subprocess
import sys
from pathlib import Path

APP_DIR = Path("/app")
CHROMA_DIR = APP_DIR / "chroma_db"
MARKER = CHROMA_DIR / ".ingestion_complete"

CHROMA_DIR.mkdir(parents=True, exist_ok=True)

if not MARKER.exists():
    print("=" * 60)
    print("CHROMA DATABASE NOT INITIALIZED")
    print("Running enterprise document ingestion...")
    print("=" * 60)

    result = subprocess.run(
        [sys.executable, "-m", "src.rag.injest"],
        cwd=APP_DIR,
        check=False,
    )

    if result.returncode != 0:
        print("Document ingestion failed. Streamlit will not start.")
        sys.exit(result.returncode)

    MARKER.write_text("Document ingestion completed successfully.\n", encoding="utf-8")
    print("Initial Chroma ingestion completed.")
else:
    print("Chroma database already initialized. Skipping ingestion.")

print("Starting Streamlit...")
os.execvp(
    "streamlit",
    [
        "streamlit",
        "run",
        "app.py",
        "--server.address=0.0.0.0",
        "--server.port=8501",
    ],
)
