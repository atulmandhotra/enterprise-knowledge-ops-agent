import subprocess
import sys
from pathlib import Path

from src.health import start_health_server, set_app_process


APP_DIR = Path("/app")
CHROMA_DIR = APP_DIR / "chroma_db"
MARKER = CHROMA_DIR / ".ingestion_complete"


# Make sure Chroma directory exists.
CHROMA_DIR.mkdir(
    parents=True,
    exist_ok=True
)


# ----------------------------------------
# Start health server
# ----------------------------------------

start_health_server()


# ----------------------------------------
# Document ingestion
# ----------------------------------------

if not MARKER.exists():

    print("=" * 60)
    print("CHROMA DATABASE NOT INITIALIZED")
    print("Running enterprise document ingestion...")
    print("=" * 60)

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "src.rag.injest"
        ],
        cwd=APP_DIR,
        check=False,
    )

    if result.returncode != 0:

        print(
            "Document ingestion failed. "
            "Streamlit will not start."
        )

        sys.exit(result.returncode)

    MARKER.write_text(
        "Document ingestion completed successfully.\n",
        encoding="utf-8"
    )

    print("Initial Chroma ingestion completed.")

else:

    print(
        "Chroma database already initialized. "
        "Skipping ingestion."
    )


# ----------------------------------------
# Start Streamlit
# ----------------------------------------

print("Starting Streamlit...")


streamlit_process = subprocess.Popen(
    [
        "streamlit",
        "run",
        "app.py",
        "--server.address=0.0.0.0",
        "--server.port=8501",
    ]
)


# Tell health server about Streamlit.
set_app_process(streamlit_process)


# ----------------------------------------
# Keep container alive
# ----------------------------------------

return_code = streamlit_process.wait()


print(
    f"Streamlit process exited with code {return_code}"
)


sys.exit(return_code)