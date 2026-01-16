# Model Management Guide

## Supported Models

This agent supports any model available in the [Ollama Library](https://ollama.com/library).

Common recommendations:
- **Llama 3.2**: Great balance of speed and intelligence. (Text & Vision versions available).
- **Mistral**: Excellent reasoning capabilities.
- **Phi-3**: Very lightweight, good for older laptops.
- **Llava**: Specialized for image description.

## Loading Models

Models are loaded into memory automatically when you send the first chat request.

1.  **First Run**: The first message might take longer as the model is loaded from disk to RAM/VRAM.
2.  **Switching**: When you select a new model in the UI, the next message will trigger a load switch. This may pause for a few seconds.

## Unloading Models

Ollama manages memory efficiently. 
- By default, models stay in memory for 5 minutes after the last request.
- After 5 minutes, they are offloaded to free up resources.

## Large Models (70B+)

If you attempt to run a 70B parameter model:
1.  Ensure you have at least 48GB+ of RAM (system RAM is slower than VRAM).
2.  The UI might time out if generation takes too long on CPU.
3.  Use 4-bit quantization (Ollama default) to fit it.

## Vision Models

To use image features, ensure you have a vision-capable model loaded, such as:
- `llama3.2-vision`
- `llava`
- `moondream`

If you send an image to a text-only model, it may ignore it or halllucinate.
