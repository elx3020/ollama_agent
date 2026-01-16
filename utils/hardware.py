import psutil
import shutil
import platform

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
    
    if shutil.which('nvidia-smi'):
        try:
            import GPUtil
            gpus = GPUtil.getGPUs()
            if gpus:
                info['gpu_available'] = True
                info['gpu_name'] = gpus[0].name
                info['vram_gb'] = round(gpus[0].memoryTotal / 1024, 2)
        except ImportError:
            pass # GPUtil might not be installed or fail
        except Exception:
            pass

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
