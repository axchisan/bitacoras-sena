import uuid
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import aiofiles

from app.database import get_db
from app.models.bitacora import Evidence, Activity, Bitacora
from app.schemas.bitacora import EvidenceOut
from app.services import onedrive_service

router = APIRouter(prefix="/api/evidence", tags=["evidence"])

UPLOADS_DIR = Path("/app/uploads")
ALLOWED_TYPES = {"image/jpeg", "image/png", "image/gif", "image/webp", "application/pdf"}
MAX_FILE_SIZE = 20 * 1024 * 1024  # 20MB


@router.post("/activities/{activity_id}", response_model=EvidenceOut)
async def upload_evidence(
    activity_id: int,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    # Validate activity exists
    act_result = await db.execute(
        select(Activity).where(Activity.id == activity_id)
    )
    activity = act_result.scalar_one_or_none()
    if not activity:
        raise HTTPException(status_code=404, detail="Actividad no encontrada")

    # Validate file type
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Tipo de archivo no permitido. Usa: PNG, JPG, GIF, WEBP, PDF"
        )

    # Read and validate size
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="El archivo supera los 20MB")

    # Get bitácora number for folder organization
    b_result = await db.execute(select(Bitacora).where(Bitacora.id == activity.bitacora_id))
    bitacora = b_result.scalar_one_or_none()

    # Save to disk
    ext = Path(file.filename).suffix
    unique_name = f"{uuid.uuid4().hex}{ext}"
    folder = UPLOADS_DIR / f"bitacora_{bitacora.number}" / f"activity_{activity_id}"
    folder.mkdir(parents=True, exist_ok=True)
    file_path = folder / unique_name

    async with aiofiles.open(file_path, "wb") as f:
        await f.write(content)

    # Create DB record
    evidence = Evidence(
        activity_id=activity_id,
        file_name=file.filename,
        file_path=str(file_path),
        file_type=file.content_type,
        file_size=len(content),
    )
    db.add(evidence)
    await db.commit()
    await db.refresh(evidence)

    # Try to upload to OneDrive in background (non-blocking)
    if onedrive_service.is_configured():
        try:
            url = await onedrive_service.upload_evidence(
                file_path, bitacora.number, f"activity_{activity_id}_{unique_name}"
            )
            if url:
                evidence.onedrive_url = url
                await db.commit()
        except Exception:
            pass  # OneDrive upload failure is non-fatal

    return evidence


@router.delete("/{evidence_id}")
async def delete_evidence(evidence_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Evidence).where(Evidence.id == evidence_id))
    evidence = result.scalar_one_or_none()
    if not evidence:
        raise HTTPException(status_code=404, detail="Evidencia no encontrada")

    # Delete file from disk
    file_path = Path(evidence.file_path)
    if file_path.exists():
        file_path.unlink()

    await db.delete(evidence)
    await db.commit()
    return {"message": "Evidencia eliminada"}


@router.get("/file/{evidence_id}")
async def serve_evidence_file(evidence_id: int, db: AsyncSession = Depends(get_db)):
    from fastapi.responses import FileResponse

    result = await db.execute(select(Evidence).where(Evidence.id == evidence_id))
    evidence = result.scalar_one_or_none()
    if not evidence:
        raise HTTPException(status_code=404, detail="Evidencia no encontrada")

    file_path = Path(evidence.file_path)
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Archivo no encontrado")

    return FileResponse(path=str(file_path), media_type=evidence.file_type)
