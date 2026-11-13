import os
import torch

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Donanım Ayarları
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
DTYPE = torch.float16 if torch.cuda.is_available() else torch.float32

# Dizinler
DIST_DIR = os.path.join(BASE_DIR, "frontend", "dist")
EXPORTS_DIR = os.path.join(BASE_DIR, "exports")
BASE_MODEL_PATH = os.path.join(BASE_DIR, "deplot_base_model")

# Sunucu Ayarları
HOST = "127.0.0.1"
PORT = 8000

# Kayıtlı Modeller (Registry)
AVAILABLE_MODELS = {
    "qwen2_vl": {
        "id": "qwen2_vl",
        "name": "Qwen2-VL-2B (LoRA İnce Ayarlı)",
        "type": "qwen2_vl",
        "path": os.path.join(BASE_DIR, "qwen2_vl_lora_finetuned"),
        "base_model": "Qwen/Qwen2-VL-2B-Instruct",
        "description": "Yeni nesil 2024 Vision-Language LoRA modeli (Önerilen)",
        "ready": True
    },
    "qwen2_vl_base": {
        "id": "qwen2_vl_base",
        "name": "Qwen2-VL-2B Orijinal (Ham Model)",
        "type": "qwen2_vl_base",
        "path": os.path.join(BASE_DIR, "qwen2_vl_lora_finetuned"),
        "base_model": "Qwen/Qwen2-VL-2B-Instruct",
        "description": "Alibaba'nın orijinal ham Qwen2-VL modeli (LoRA'sız)",
        "ready": True
    },
    "deplot_v2": {
        "id": "deplot_v2",
        "name": "DePlot LoRA (v2 - İnce Ayarlı)",
        "type": "deplot_lora",
        "path": os.path.join(BASE_DIR, "deplot_lora_finetuned_2"),
        "base_model": BASE_MODEL_PATH,
        "description": "Fine-tune edilmiş DePlot LoRA modeli",
        "ready": True
    },
    "deplot_base": {
        "id": "deplot_base",
        "name": "DePlot Orijinal (Yerel Ham Model)",
        "type": "deplot_base",
        "path": BASE_MODEL_PATH,
        "base_model": BASE_MODEL_PATH,
        "description": "Orijinal ham Google DePlot modeli (LoRA'sız)",
        "ready": True
    }
}

DEFAULT_MODEL_ID = "qwen2_vl"
