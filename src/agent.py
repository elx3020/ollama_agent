import ollama
from typing import List, Dict, Optional, Union
import base64
from io import BytesIO

class OllamaAgent:
    def __init__(self, model_name: str = "llama3.2", host: str = "http://localhost:11434"):
        self.client = ollama.Client(host=host)
        self.model_name = model_name

    def list_models(self) -> List[Dict]:
        """List available models in Ollama."""
        try:
            response = self.client.list()
            # The structure of response usually has 'models' key
            return response.get('models', [])
        except Exception as e:
            print(f"Error listing models: {e}")
            return []

    def pull_model(self, model_name: str):
        """Pull a model from the registry."""
        # This acts as a generator
        return self.client.pull(model_name, stream=True)

    def chat(self, messages: List[Dict], stream: bool = True):
        """
        Send a chat request to the model.
        messages: List of {"role": "user/assistant", "content": "...", "images": [...]}
        """
        try:
            if stream:
                yield from self.client.chat(model=self.model_name, messages=messages, stream=stream)
            else:
                yield self.client.chat(model=self.model_name, messages=messages, stream=stream)
        except Exception as e:
            yield {"error": str(e)}

    @staticmethod
    def process_image(image_file) -> str:
        """
        Convert uploaded file to bytes for Ollama.
        Streamlit UploadedFile -> bytes
        """
        if image_file is None:
            return None
        return image_file.getvalue()

    def generate_response(self, prompt: str, image_bytes: List[bytes] = None, history: List[Dict] = None):
        """
        Simple wrapper for one-off interaction or continuation.
        """
        if history is None:
            history = []
        
        message = {
            'role': 'user',
            'content': prompt
        }
        
        if image_bytes:
            # client.chat expects 'images' field in the message to be list of bytes or base64
            message['images'] = image_bytes
            
        messages = history + [message]
        
        return self.chat(messages=messages, stream=True)
