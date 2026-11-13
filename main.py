import os
import time
import threading
import webbrowser
import urllib.request
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from backend.config import DIST_DIR, HOST, PORT
from backend.services.model_service import ModelService
from backend.routers.predict_router import router as predict_router
from backend.routers.export_router import router as export_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Uygulama açılırken modeli GPU'ya yükle
    print("=" * 60)
    print("🚀 DePlot & Qwen Vision Studio başlatılıyor...")
    ModelService.get_instance()
    print(f"🌐 Web Arayüzü Hazır: http://{HOST}:{PORT}")
    print("=" * 60)
    yield
    print("Uygulama kapatılıyor...")

app = FastAPI(
    title="DePlot & Qwen Vision Studio API",
    description="Yapay zeka ile grafiklerden tablo ve veri çıkarma servisi",
    version="2.0.0",
    lifespan=lifespan
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Tarayıcı önbelleğini engelleme middleware (Her zaman en güncel frontend kodunu yükler)
@app.middleware("http")
async def add_no_cache_headers(request, call_next):
    response = await call_next(request)
    if request.url.path == "/" or request.url.path.endswith(".html"):
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
    return response

# Modüler Router'ları Dahil Et
app.include_router(predict_router)
app.include_router(export_router)

# React Frontend statik dosyalarını bağla
if os.path.exists(DIST_DIR):
    app.mount("/", StaticFiles(directory=DIST_DIR, html=True), name="frontend")

def _open_browser_when_ready():
    """
    Sunucu portu açılana ve model yüklenene kadar bekler.
    Hazır olduğunda tarayıcıyı açar (ERR_CONNECTION_REFUSED hatasını önler).
    """
    health_url = f"http://{HOST}:{PORT}/api/health"
    for _ in range(120): # Maksimum 60 saniye bekle
        time.sleep(0.5)
        try:
            with urllib.request.urlopen(health_url, timeout=1) as response:
                if response.status == 200:
                    webbrowser.open(f"http://{HOST}:{PORT}")
                    break
        except Exception:
            pass

def start_server():
    import uvicorn
    # Sunucu hazır olunca tarayıcıyı açacak izleyiciyi başlat
    threading.Thread(target=_open_browser_when_ready, daemon=True).start()
    uvicorn.run(app, host=HOST, port=PORT)

if __name__ == "__main__":
    start_server()
