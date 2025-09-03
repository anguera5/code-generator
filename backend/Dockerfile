FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_NO_CACHE_DIR=on

WORKDIR /app
COPY pyproject.toml /app/
RUN pip install -U pip && pip install -e .
COPY app /app/app

# Pre-create logs directory with proper permissions
# Pre-create fixed logs directory and relax permissions (override by bind mount in compose)
RUN mkdir -p /var/log/genai-portfolio && chmod 777 /var/log/genai-portfolio

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
