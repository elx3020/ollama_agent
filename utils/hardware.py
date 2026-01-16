import psutil
import shutil
import platform
import os
import subprocess
import urllib.request
import json

def _find_nvidia_smi():
    """Find nvidia-smi executable, checking common Windows locations."""
    # First try standard PATH lookup
    nvidia_smi = shutil.which('nvidia-smi')
    if nvidia_smi:
        return nvidia_smi
    
    # On Windows, check common installation paths
    if platform.system() == 'Windows':
        common_paths = [
            os.path.join(os.environ.get('SystemRoot', 'C:\\Windows'), 'System32', 'nvidia-smi.exe'),
            os.path.join(os.environ.get('ProgramFiles', 'C:\\Program Files'), 'NVIDIA Corporation', 'NVSMI', 'nvidia-smi.exe'),
        ]
        for path in common_paths:
            if os.path.isfile(path):
                return path
    
    return None

def _get_ollama_gpu_info():
    """
    Query Ollama API to check if GPU is available.
    Works in Docker containers where nvidia-smi isn't accessible but Ollama has GPU access.
    """
    ollama_host = os.environ.get('OLLAMA_HOST', 'http://localhost:11434')
    try:
        # Try to get running models or version info which may include GPU details
        url = f"{ollama_host}/api/ps"
        req = urllib.request.Request(url, method='GET')
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode())
            # Check if any model is using GPU
            models = data.get('models', [])
            for model in models:
                details = model.get('details', {})
                # If model is loaded, Ollama is likely using GPU if available
                if model.get('size_vram', 0) > 0:
                    return True, model.get('size_vram', 0) / (1024**3)  # Convert to GB
        
        # Alternative: try to infer from system by checking Ollama's /api/version or running a test
        # For now, if Ollama is reachable, we assume it might have GPU
        return None, 0  # Unknown
    except Exception:
        return None, 0

def get_system_info():
    info = {}
    
    # RAM
    ram = psutil.virtual_memory()
    info['total_ram_gb'] = round(ram.total / (1024**3), 2)
    info['available_ram_gb'] = round(ram.available / (1024**3), 2)
    
    # GPU (Basic check for Nvidia)
    info['gpu_available'] = False
    info['gpu_name'] = "None"
    info['vram_gb'] = 0
    
    nvidia_smi_path = _find_nvidia_smi()
    if nvidia_smi_path:
        try:
            import GPUtil
            gpus = GPUtil.getGPUs()
            if gpus:
                info['gpu_available'] = True
                info['gpu_name'] = gpus[0].name
                info['vram_gb'] = round(gpus[0].memoryTotal / 1024, 2)
        except ImportError:
            # GPUtil not installed, fall back to nvidia-smi directly
            try:
                result = subprocess.run(
                    [nvidia_smi_path, '--query-gpu=name,memory.total', '--format=csv,noheader,nounits'],
                    capture_output=True, text=True, timeout=10
                )
                if result.returncode == 0 and result.stdout.strip():
                    lines = result.stdout.strip().split('\n')
                    if lines:
                        parts = lines[0].split(',')
                        info['gpu_available'] = True
                        info['gpu_name'] = parts[0].strip()
                        if len(parts) > 1:
                            info['vram_gb'] = round(float(parts[1].strip()) / 1024, 2)
            except Exception:
                pass
        except Exception:
            pass
    
    # If no GPU detected locally, check if running in Docker with Ollama having GPU access
    if not info['gpu_available'] and os.environ.get('OLLAMA_HOST'):
        ollama_gpu, vram = _get_ollama_gpu_info()
        if ollama_gpu:
            info['gpu_available'] = True
            info['gpu_name'] = "GPU (via Ollama)"
            info['vram_gb'] = round(vram, 2) if vram else 8  # Default estimate
        elif ollama_gpu is None:
            # Ollama is reachable but we couldn't determine GPU status
            # Assume Ollama may have GPU access - user configured it
            info['gpu_available'] = True
            info['gpu_name'] = "GPU (assumed via Ollama)"
            info['vram_gb'] = 8  # Conservative estimate for model recommendations

    return info

def recommend_model(info):
    """
    Recommends an Ollama model based on system resources.
    """
    ram = info['available_ram_gb']
    vram = info['vram_gb']
    
    # Prefer VRAM if GPU is available, otherwise system RAM
    usable_memory = vram if info['gpu_available'] else ram
    
    recommendation = {
        "recommended_model": "llama3.2",
        "reason": "Standard lightweight model suitable for most modern hardware.",
        "alternatives": []
    }

    if usable_memory < 4:
        recommendation["recommended_model"] = "tinyllama"
        recommendation["reason"] = f"Very limited memory ({usable_memory}GB). TinyLlama is efficient."
        recommendation["alternatives"] = ["phi"]
    elif usable_memory < 8:
        recommendation["recommended_model"] = "phi3"
        recommendation["reason"] = f"Limited memory ({usable_memory}GB). Phi3 is very capable for its size."
        recommendation["alternatives"] = ["llama3.2", "mistral"]
    elif usable_memory < 16:
        recommendation["recommended_model"] = "llama3.1"
        recommendation["reason"] = f"Decent memory ({usable_memory}GB). Llama 3.1 8B is a strong general purpose model."
        recommendation["alternatives"] = ["mistral", "gemma2"]
    else:
        recommendation["recommended_model"] = "llama3.1:70b" # If user has a LOT of RAM, maybe? 
        # Actually 70b usually requires ~40GB provided 4-bit quantization on CPU or dual 3090s. 
        # Let's be safe and suggest the 8b as default but mention larger ones.
        recommendation["recommended_model"] = "llama3.1"
        recommendation["reason"] = f"Ample memory ({usable_memory}GB). You can run Llama 3.1 comfortably, and potentially larger models like Llama 3.1 70b (quantized) if you have over 32GB RAM."
        recommendation["alternatives"] = ["mixtral", "qwen2.5:14b"]
        
    return recommendation
