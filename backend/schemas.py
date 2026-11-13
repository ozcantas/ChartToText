from typing import List, Optional
from pydantic import BaseModel

class ModelInfo(BaseModel):
    id: str
    name: str
    description: str
    type: str
    ready: bool

class HealthResponse(BaseModel):
    status: str
    device: str
    cuda_available: bool
    gpu_name: str
    current_model: str

class PredictResponse(BaseModel):
    success: bool
    title: str
    columns: List[str]
    rows: List[List[str]]
    row_count: int
    col_count: int
    raw_text: str
    used_model: str

class ExportPayload(BaseModel):
    title: Optional[str] = "grafik_tablosu"
    columns: List[str] = []
    rows: List[List[str]] = []
