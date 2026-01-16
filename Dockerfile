FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY . .

# Expose Streamlit port
EXPOSE 8501

# Healthcheck to ensure the UI is up
HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health || exit 1

# Default environment for Ollama connection
# Users should set this to http://host.docker.internal:11434 on MacOS/Windows
# or use --network host on Linux.
ENV OLLAMA_HOST="http://localhost:11434"

ENTRYPOINT ["streamlit", "run", "ui/app.py", "--server.port=8501", "--server.address=0.0.0.0"]
