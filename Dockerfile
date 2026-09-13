FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .
COPY src ./src
COPY documents ./documents
COPY docker_entrypoint.py .

EXPOSE 8501

ENTRYPOINT ["python", "docker_entrypoint.py"]
