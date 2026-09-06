# ============================================================
#  YouTube Transcripter - CPU image (default)
# ============================================================
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    HF_HUB_DISABLE_TELEMETRY=1

# ffmpeg: audio normalisation. curl: healthcheck.
RUN apt-get update && apt-get install -y --no-install-recommends \
        ffmpeg \
        curl \
    && rm -rf /var/lib/apt/lists/*

# Match the host user so bind-mounted data/ and models/ stay writable.
ARG UID=1000
ARG GID=1000
RUN groupadd -g "${GID}" app 2>/dev/null || true \
    && useradd -m -u "${UID}" -g "${GID}" -s /bin/bash app 2>/dev/null || true

WORKDIR /app

COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY app/ ./app/
COPY .streamlit/ ./.streamlit/

RUN mkdir -p /app/data /app/models /app/downloads \
    && chown -R "${UID}:${GID}" /app

USER ${UID}:${GID}

EXPOSE 8501

HEALTHCHECK --interval=30s --timeout=5s --start-period=60s --retries=3 \
    CMD curl -fsS http://localhost:8501/_stcore/health || exit 1

CMD ["streamlit", "run", "app/main.py"]
