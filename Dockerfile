FROM python:3.10-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
      git ffmpeg curl unzip build-essential && \
    rm -rf /var/lib/apt/lists/*

# Deno install
RUN curl -fsSL https://deno.land/install.sh | sh && \
    ln -s /root/.deno/bin/deno /usr/local/bin/deno

WORKDIR /app

COPY requirements.txt .
RUN python -m pip install --upgrade pip && \
    python -m pip install --no-cache-dir -r requirements.txt && \
    python -m pip install --no-deps git+https://github.com/CertifiedCoders/youtube-search-python

COPY . .

CMD ["python", "-m", "AnnieXMedia"]
