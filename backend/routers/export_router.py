from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from backend.schemas import ExportPayload
from backend.services.export_service import export_to_excel, export_to_csv

router = APIRouter(prefix="/api/export", tags=["Export"])

@router.post("/excel")
def download_excel(payload: ExportPayload):
    try:
        buffer, filename = export_to_excel(payload.columns, payload.rows, payload.title or "grafik_tablosu")
        return StreamingResponse(
            buffer,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename*=UTF-8''{filename}"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Excel oluşturulamadı: {str(e)}")

@router.post("/csv")
def download_csv(payload: ExportPayload):
    try:
        buffer, filename = export_to_csv(payload.columns, payload.rows, payload.title or "grafik_tablosu")
        return StreamingResponse(
            buffer,
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename*=UTF-8''{filename}"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"CSV oluşturulamadı: {str(e)}")
