# Dockerfile — stable, reproducible runtime with aria2 + Python 3.10
FROM python:3.10-slim

ENV DEBIAN_FRONTEND=noninteractive
WORKDIR /app

# Install system deps needed by some wheels and aria2
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
      aria2 ca-certificates curl build-essential git libffi-dev libssl-dev pkg-config && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Copy requirements first (helps caching)
COPY requirements.txt /app/requirements.txt

# Create and use a venv at /opt/venv
RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Upgrade pip + install wheels / requirements
RUN python -m pip install --upgrade pip setuptools wheel
RUN if [ -f /app/requirements.txt ]; then python -m pip install --no-cache-dir -r /app/requirements.txt; fi

# Copy the rest of the app
COPY . /app

# Make start.sh executable
RUN chmod +x /app/start.sh

# Default command — start.sh should start aria2 then run the bot
CMD ["bash", "/app/start.sh"]
