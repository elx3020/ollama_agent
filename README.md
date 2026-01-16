# Local AI Agent with Ollama

This is a modular AI agent interface running locally using [Ollama](https://ollama.com). It allows you to chat with various LLMs, upload images (multimodal support with Llama 3.2 Vision, Llava, etc.), and use text files as context.

## Features

- **Local & Private**: Runs entirely on your machine.
- **Hardware Aware**: Automatically checks your RAM/GPU and suggests appropriate models.
- **Multimodal**: Support for image inputs (depending on the model, e.g., use `llama3.2-vision` or `llava`).
- **File Context**: Upload text/code/PDF files to chat with them.
- **Model Management**: Pull new models directly from the UI.

## Prerequisites

1.  **Install Ollama**:
    - Linux: `curl -fsSL https://ollama.com/install.sh | sh`
    - macOS/Windows: Download from [ollama.com](https://ollama.com).

2.  **Start Ollama Service**:
    ```bash
    ollama serve
    ```

3.  **Python 3.8+**: Ensure you have Python installed.

## Installation

1.  Create a virtual environment:
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```

2.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```

## Running the Agent

Run the Streamlit UI:

```bash
streamlit run ui/app.py
```

## Documentation

### Managing Models

- **Pulling Models**: You can pull models via the sidebar in the UI, or via CLI:
  ```bash
  ollama pull llama3.2
  ```
- **Unloading Models**: Ollama automatically unloads models after 5 minutes of inactivity to free up VRAM. You can force it by stopping the server or running `ollama stop <model>` (if CLI supports it) or sending an empty request with `keep_alive: 0` (advanced).

### Hardware Recommendations

The app includes a built-in hardware checker (`utils/hardware.py`).
- **< 8GB RAM**: specific quantized small models (`phi`, `tinyllama`).
- **8GB - 16GB RAM**: 7B-8B parameter models (`llama3`, `mistral`).
- **16GB+ RAM / VRAM**: Larger models or higher quantization.

### File Structure

- `ui/`: Streamlit web application.
- `src/`: Core logic for Ollama interaction.
- `utils/`: Hardware diagnostics and helpers.
- `docs/`: Additional documentation.

## Docker Support

The easiest way to run this application is using Docker Compose. The setup is **fully portable** and includes its own isolated Ollama instance, so you don't need to install anything else on your host machine.

### Quick Start with Docker Compose (Recommended)

1.  **Start the Stack**:
    ```bash
    docker-compose up --build
    ```
    This will start both the agent UI and a dedicated Ollama server.

2.  **Access UI**: Open `http://localhost:8501`.

3.  **Manage Models**: 
    - Since this is a fresh isolated container, you will need to **pull models** (e.g., `llama3.2`) using the UI sidebar.
    - Models are saved in a permanent Docker volume (`ollama_storage`) and will persist between restarts.

*Note: This setup runs independently of any local Ollama installation you might have.*

### Advanced: Connecting to Host Ollama

If you prefer to use your existing Ollama installation on your host machine (saving disk space), you can run the container manually:

1.  **Configure Host Ollama**: Ensure your local Ollama is listening on `0.0.0.0` (see Troubleshooting below).
2.  **Run Container**:
    ```bash
    docker build -t ollama-agent .
    docker run -p 8501:8501 \
      --add-host host.docker.internal:host-gateway \
      -e OLLAMA_HOST=http://host.docker.internal:11434 \
      ollama-agent
    ```

### Troubleshooting: Connecting to Host Ollama

If you see `[Errno 111] Connection refused` or cannot connect to Ollama from Docker:

1.  **Linux Users**: By default, Ollama listens on `127.0.0.1`. Attempts to access it from inside Docker (which uses the bridge network IP) will be blocked.
    You must configure Ollama to listen on all IPv4 addresses `0.0.0.0`.
    
    If running as a systemd service:
    ```bash
    # Edit the service
    sudo sed -i '/\[Service\]/a Environment="OLLAMA_HOST=0.0.0.0"' /etc/systemd/system/ollama.service
    
    # Reload and restart
    sudo systemctl daemon-reload
    sudo systemctl restart ollama
    ```

    Or run manually:
    ```bash
    OLLAMA_HOST=0.0.0.0 ollama serve
    ```

2.  **Mac/Windows Users**: The default `http://host.docker.internal:11434` config usually works without changes.

