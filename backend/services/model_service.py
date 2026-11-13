import io
import gc
import threading
from typing import List, Dict, Any
import torch
from PIL import Image
from transformers import (
    AutoProcessor, 
    Pix2StructForConditionalGeneration,
    Qwen2VLForConditionalGeneration,
    BitsAndBytesConfig,
    StoppingCriteria,
    StoppingCriteriaList
)
from peft import PeftModel
from qwen_vl_utils import process_vision_info
from backend.config import AVAILABLE_MODELS, DEFAULT_MODEL_ID, DEVICE, DTYPE, BASE_MODEL_PATH

class CancelStoppingCriteria(StoppingCriteria):
    def __init__(self, cancel_event: threading.Event):
        super().__init__()
        self.cancel_event = cancel_event

    def __call__(self, input_ids: torch.LongTensor, scores: torch.FloatTensor, **kwargs) -> bool:
        return self.cancel_event.is_set()

class ModelService:
    _instance = None

    def __init__(self):
        self.device = DEVICE
        self.current_model_id = None
        self.cancel_event = threading.Event()
        
        # DePlot bileşenleri
        self.deplot_processor = None
        self.deplot_base = None
        self.deplot_lora = None
        
        # Qwen2-VL bileşenleri
        self.qwen_processor = None
        self.qwen_model = None
        
        # Varsayılan modeli yükle
        self.load_model(DEFAULT_MODEL_ID)

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def clear_vram(self):
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()

    def get_available_models(self) -> List[Dict[str, Any]]:
        return [
            {
                "id": info["id"],
                "name": info["name"],
                "description": info["description"],
                "type": info["type"],
                "ready": info["ready"]
            }
            for info in AVAILABLE_MODELS.values()
        ]

    def _unload_all_models(self):
        """VRAM'i tamamen boşaltmak için tüm modelleri bellekten siler."""
        self.deplot_lora = None
        self.deplot_base = None
        self.deplot_processor = None
        self.qwen_model = None
        self.qwen_processor = None
        self.clear_vram()

    def _load_deplot(self, model_id: str):
        """DePlot modelini (ham veya LoRA) hazırlar."""
        if self.qwen_model is not None:
            print("Qwen2-VL bellekten temizleniyor...")
            self._unload_all_models()

        if self.deplot_base is None:
            print(f"DePlot temel modeli ({BASE_MODEL_PATH}) yükleniyor...")
            self.deplot_processor = AutoProcessor.from_pretrained(BASE_MODEL_PATH)
            self.deplot_base = Pix2StructForConditionalGeneration.from_pretrained(
                BASE_MODEL_PATH,
                dtype=DTYPE
            ).to(self.device)
            self.deplot_base.eval()

        if model_id == "deplot_v2" and self.deplot_lora is None:
            lora_path = AVAILABLE_MODELS["deplot_v2"]["path"]
            print(f"DePlot LoRA adaptörü ({lora_path}) bağlanıyor...")
            self.deplot_lora = PeftModel.from_pretrained(self.deplot_base, lora_path).to(self.device)
            self.deplot_lora.eval()

    def _load_qwen(self):
        """Qwen2-VL-2B modelini 4-bit kuantize olarak GPU'ya yükler."""
        if self.deplot_base is not None or self.deplot_lora is not None:
            print("DePlot bellekten temizleniyor...")
            self._unload_all_models()

        if self.qwen_model is None:
            qwen_info = AVAILABLE_MODELS["qwen2_vl"]
            print("Qwen2-VL-2B modeli 4-bit olarak yükleniyor (~1.5 GB VRAM)...")
            
            bnb_config = BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_compute_dtype=torch.float16,
                bnb_4bit_use_double_quant=True,
                bnb_4bit_quant_type="nf4"
            )
            
            base_m = Qwen2VLForConditionalGeneration.from_pretrained(
                qwen_info["base_model"],
                quantization_config=bnb_config,
                device_map="auto"
            )
            
            print(f"Qwen LoRA adaptörü ({qwen_info['path']}) bağlanıyor...")
            self.qwen_processor = AutoProcessor.from_pretrained(qwen_info["path"])
            self.qwen_model = PeftModel.from_pretrained(base_m, qwen_info["path"])
            self.qwen_model.eval()
            print("Qwen2-VL modeli başarıyla hazırlandı!")

    def load_model(self, model_id: str):
        if model_id not in AVAILABLE_MODELS:
            model_id = DEFAULT_MODEL_ID

        if self.current_model_id == model_id:
            # Zaten yüklüyse işlem yapma
            if model_id in ["qwen2_vl", "qwen2_vl_base"] and self.qwen_model is not None:
                return
            if model_id in ["deplot_v2", "deplot_base"] and self.deplot_base is not None:
                return

        model_info = AVAILABLE_MODELS[model_id]
        print(f"Model yükleniyor: {model_info['name']}...")

        if model_info["type"] in ["qwen2_vl", "qwen2_vl_base"]:
            self._load_qwen()
        elif model_info["type"] in ["deplot_lora", "deplot_base"]:
            self._load_deplot(model_id)

        self.current_model_id = model_id
        self.clear_vram()

    def cancel(self):
        print("İptal sinyali tetiklendi. Model çıkarımı durduruluyor...")
        self.cancel_event.set()
        self.clear_vram()

    def predict(self, image_bytes: bytes, max_tokens: int = 1024, model_id: str = DEFAULT_MODEL_ID) -> str:
        self.cancel_event.clear()
        self.load_model(model_id)
        self.clear_vram()

        stopping_criteria = StoppingCriteriaList([CancelStoppingCriteria(self.cancel_event)])

        try:
            image = Image.open(io.BytesIO(image_bytes))
            if image.mode != "RGB":
                image = image.convert("RGB")

            # 1. QWEN2-VL ÇIKARIMI (LoRA'lı veya Ham Base)
            if model_id in ["qwen2_vl", "qwen2_vl_base"]:
                messages = [
                    {
                        "role": "system",
                        "content": (
                            "You are a professional chart data extraction model. Extract all data from the chart "
                            "and output it STRICTLY as a clean Markdown table with '|' column separators and newlines "
                            "for every row (e.g. '| Category | Percentage |' or '| Item | Value |'). "
                            "Never output inline text, inline asterisk lists (**), bullet points, conversational text, or Chinese phrases."
                        )
                    },
                    {
                        "role": "user",
                        "content": [
                            {"type": "image", "image": image},
                            {"type": "text", "text": "Generate underlying data table of the figure below strictly as a Markdown table with '|' separators:"}
                        ]
                    }
                ]
                
                text = self.qwen_processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
                image_inputs, video_inputs = process_vision_info(messages)
                inputs = self.qwen_processor(
                    text=[text],
                    images=image_inputs,
                    videos=video_inputs,
                    padding=True,
                    return_tensors="pt"
                ).to(self.device)

                with torch.no_grad():
                    # Ham Qwen modeli isteniyorsa LoRA adaptörlerini devre dışı bırak
                    if model_id == "qwen2_vl_base":
                        with self.qwen_model.disable_adapter():
                            outputs = self.qwen_model.generate(
                                **inputs,
                                max_new_tokens=int(max_tokens),
                                stopping_criteria=stopping_criteria
                            )
                    else:
                        outputs = self.qwen_model.generate(
                            **inputs,
                            max_new_tokens=int(max_tokens),
                            stopping_criteria=stopping_criteria
                        )

                if self.cancel_event.is_set():
                    raise InterruptedError("İşlem kullanıcı tarafından iptal edildi.")

                generated_ids = [
                    out[len(inp):] for inp, out in zip(inputs.input_ids, outputs)
                ]
                return self.qwen_processor.batch_decode(
                    generated_ids, skip_special_tokens=True, clean_up_tokenization_spaces=False
                )[0]

            # 2. DEPLOT BASE ÇIKARIMI (LoRA Devre Dışı)
            elif model_id == "deplot_base":
                inputs = self.deplot_processor(
                    images=image,
                    text="Generate underlying data table of the figure below:",
                    return_tensors="pt"
                ).to(self.device)

                if torch.cuda.is_available():
                    inputs["flattened_patches"] = inputs["flattened_patches"].to(dtype=DTYPE)

                with torch.no_grad():
                    outputs = self.deplot_base.generate(
                        **inputs,
                        max_new_tokens=int(max_tokens),
                        stopping_criteria=stopping_criteria
                    )

                if self.cancel_event.is_set():
                    raise InterruptedError("İşlem kullanıcı tarafından iptal edildi.")

                return self.deplot_processor.decode(outputs[0], skip_special_tokens=True)

            # 3. DEPLOT LORA V2 ÇIKARIMI
            elif model_id == "deplot_v2":
                inputs = self.deplot_processor(
                    images=image,
                    text="Generate underlying data table of the figure below:",
                    return_tensors="pt"
                ).to(self.device)

                if torch.cuda.is_available():
                    inputs["flattened_patches"] = inputs["flattened_patches"].to(dtype=DTYPE)

                with torch.no_grad():
                    outputs = self.deplot_lora.generate(
                        **inputs,
                        max_new_tokens=int(max_tokens),
                        stopping_criteria=stopping_criteria
                    )

                if self.cancel_event.is_set():
                    raise InterruptedError("İşlem kullanıcı tarafından iptal edildi.")

                return self.deplot_processor.decode(outputs[0], skip_special_tokens=True)

            else:
                raise ValueError(f"Bilinmeyen model: {model_id}")

        finally:
            self.clear_vram()
