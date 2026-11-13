import asyncio
from typing import List
import torch
from fastapi import APIRouter, File, UploadFile, Form, HTTPException
from backend.services.model_service import ModelService
from backend.services.parser_service import parse_deplot
from backend.schemas import HealthResponse, PredictResponse, ModelInfo
from backend.config import DEVICE, DEFAULT_MODEL_ID, AVAILABLE_MODELS

router = APIRouter(prefix="/api", tags=["Prediction"])

@router.get("/health", response_model=HealthResponse)
def health_check():
    model_service = ModelService.get_instance()
    current_name = AVAILABLE_MODELS.get(model_service.current_model_id, {}).get("name", "Bilinmiyor")
    return {
        "status": "online",
        "device": DEVICE,
        "cuda_available": torch.cuda.is_available(),
        "gpu_name": torch.cuda.get_device_name(0) if torch.cuda.is_available() else "CPU",
        "current_model": current_name
    }

@router.get("/models", response_model=List[ModelInfo])
def get_models():
    model_service = ModelService.get_instance()
    return model_service.get_available_models()

@router.post("/cancel")
def cancel_prediction():
    model_service = ModelService.get_instance()
    model_service.cancel()
    return {"success": True, "message": "İşlem iptal edildi."}

@router.post("/predict", response_model=PredictResponse)
async def predict_chart(
    file: UploadFile = File(...),
    max_tokens: int = Form(1024),
    model_id: str = Form(DEFAULT_MODEL_ID)
):
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Lütfen geçerli bir grafik görseli yükleyin.")

    model_service = ModelService.get_instance()
    contents = await file.read()

    try:
        raw_text = await asyncio.to_thread(
            model_service.predict,
            contents,
            max_tokens=max_tokens,
            model_id=model_id
        )
        parsed = parse_deplot(raw_text)
        used_model_name = AVAILABLE_MODELS.get(model_id, {}).get("name", model_id)

        return {
            "success": True,
            "title": parsed["title"],
            "columns": parsed["columns"],
            "rows": parsed["rows"],
            "row_count": len(parsed["rows"]),
            "col_count": len(parsed["columns"]),
            "raw_text": raw_text,
            "used_model": used_model_name
        }
    except InterruptedError:
        raise HTTPException(status_code=499, detail="İşlem kullanıcı tarafından iptal edildi.")
    except NotImplementedError as nie:
        raise HTTPException(status_code=400, detail=str(nie))
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except torch.cuda.OutOfMemoryError:
        model_service.clear_vram()
        raise HTTPException(
            status_code=500,
            detail="Ekran kartı belleği (VRAM) yetersiz kaldı! Arka plandaki GPU kullanan uygulamaları kapatıp tekrar deneyin."
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Çıkarım sırasında hata oluştu: {str(e)}")
