from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from app.config import get_settings
from app.database import create_tables
from app.routers import bitacoras, activities, work_items, evidence
from app.services import excel_service

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await create_tables()
    Path("/app/uploads").mkdir(parents=True, exist_ok=True)
    Path("/app/output").mkdir(parents=True, exist_ok=True)
    # Pre-generate the clean template so the first export is fast
    import asyncio
    await asyncio.to_thread(excel_service._get_clean_template)
    yield
    # Shutdown — nothing to clean up


app = FastAPI(
    title="Bitácoras SENA API",
    description="Sistema de automatización de bitácoras de seguimiento SENA",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(bitacoras.router)
app.include_router(activities.router)
app.include_router(work_items.router)
app.include_router(evidence.router)

# Serve uploaded files
uploads_path = Path("/app/uploads")
if uploads_path.exists():
    app.mount("/uploads", StaticFiles(directory=str(uploads_path)), name="uploads")


@app.get("/api/health")
async def health():
    return {"status": "ok", "version": "1.0.0"}


@app.get("/api/config")
async def get_config():
    """Returns non-sensitive config info for the frontend."""
    from app.utils.dates import get_all_periods, get_current_bitacora_number
    periods = get_all_periods()
    current = get_current_bitacora_number()
    return {
        "total_bitacoras": settings.bitacoras_total,
        "current_bitacora": current,
        "start_date": settings.bitacoras_start_date.isoformat(),
        "onedrive_configured": bool(settings.onedrive_client_id),
        "periods": [
            {
                "number": p.number,
                "start": p.start.isoformat(),
                "end": p.end.isoformat(),
                "label": p.label,
                "delivery_date": p.delivery_date.isoformat(),
            }
            for p in periods
        ],
    }
