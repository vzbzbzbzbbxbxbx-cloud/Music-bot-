FROM python:3.12-slim

RUN apt-get update && \
    apt-get install -y --no-install-recommends git ffmpeg curl unzip build-essential && \
    rm -rf /var/lib/apt/lists/* && \
    curl -fsSL https://deno.land/install.sh | sh && \
    ln -s /root/.deno/bin/deno /usr/local/bin/deno

WORKDIR /app

COPY requirements.txt .
RUN pip install --upgrade pip

# install main requirements
RUN pip install --no-cache-dir -r requirements.txt

# install youtube-search-python WITHOUT dependencies (VERY IMPORTANT)
RUN pip install --no-deps git+https://github.com/CertifiedCoders/youtube-search-python

COPY . .

CMD ["python3", "-m", "AnnieXMedia"]
