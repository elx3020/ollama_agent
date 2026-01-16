#!/bin/bash

# Ensure we are in the script's directory
cd "$(dirname "$0")"

echo "Initializing Ollama AI Agent..."

# Check for Python
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 could not be found. Please install it."
    exit 1
fi

# Create venv if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate venv
source venv/bin/activate

# Install requirements
echo "Checking dependencies..."
pip install -r requirements.txt | grep -v 'already satisfied'

# Check if Ollama is running
if ! pgrep -x "ollama" > /dev/null; then
    echo "-----------------------------------------------------"
    echo "WARNING: Ollama does not seem to be running."
    echo "Please start it with 'ollama serve' in another terminal."
    echo "-----------------------------------------------------"
    read -p "Press Enter to continue anyway (or Ctrl+C to abort)..."
fi

# Run the app
echo "Starting UI..."
streamlit run ui/app.py
