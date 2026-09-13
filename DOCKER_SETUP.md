# Docker Setup

This setup runs the Enterprise Knowledge Ops Agent in Docker and automatically initializes the Chroma knowledge base on first startup.

## Files

- `Dockerfile` — builds the application image.
- `.dockerignore` — keeps secrets, caches, local databases, tests, and unrelated files out of the image.
- `docker_entrypoint.py` — checks whether Chroma has been initialized; if not, it runs `src.rag.injest` before starting Streamlit.
- `docker-compose.yml` — optional convenience configuration with a persistent Chroma volume and read-only document mount.

## Important

Keep `.env` outside the Docker image. The API key is injected at runtime through `env_file`.

## Build and run with Docker

From the project root:

```powershell
docker build -t enterprise-knowledge-ops-agent .
docker run --rm -p 8501:8501 --env-file .env enterprise-knowledge-ops-agent
```

Open:

```text
http://localhost:8501
```

On the first container run, the entrypoint automatically runs:

```text
python -m src.rag.injest
```

and creates the Chroma database. A `.ingestion_complete` marker prevents unnecessary re-ingestion on subsequent starts when the Chroma directory is persisted.

## Recommended: Docker Compose

From the project root:

```powershell
docker compose up --build
```

The compose configuration:

- injects `.env` at runtime;
- persists Chroma in a Docker named volume;
- mounts `documents/` read-only;
- automatically ingests documents on the first run;
- starts Streamlit on port 8501.

Open:

```text
http://localhost:8501
```

To stop:

```powershell
docker compose down
```

To remove the persisted Chroma data and force a fresh ingestion:

```powershell
docker compose down -v
docker compose up --build
```
