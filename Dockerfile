FROM python:3.12-slim

# install system packages required for tgcrypto & pytgcalls
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    gcc \
    build-essential \
    python3-dev \
    libssl-dev \
    libffi-dev \
    git \
    ffmpeg \
    curl \
    unzip \
    && rm -rf /var/lib/apt/lists/*

# (optional) deno for some plugins
RUN curl -fsSL https://deno.land/install.sh | sh && \
    ln -s /root/.deno/bin/deno /usr/local/bin/deno

WORKDIR /app

COPY requirements.txt .
RUN pip install --upgrade pip setuptools wheel
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python3", "-m", "AnnieXMedia"]
