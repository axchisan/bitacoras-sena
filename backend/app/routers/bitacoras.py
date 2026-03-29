from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from datetime import date

from app.database import get_db
from app.models.bitacora import Bitacora, Activity, BitacoraStatus
from app.schemas.bitacora import BitacoraOut, BitacoraListItem, BitacoraUpdate, GenerateRequest
from app.utils.dates import get_all_periods, get_period_for_bitacora
from app.services import azure_devops, claude_service, excel_service, onedrive_service

router = APIRouter(prefix="/api/bitacoras", tags=["bitacoras"])


async def _ensure_bitacoras_exist(db: AsyncSession) -> None:
    """Creates all 12 bitácora records if they don't exist yet."""
    result = await db.execute(select(func.count()).select_from(Bitacora))
    count = result.scalar()
    if count == 0:
        periods = get_all_periods()
        for period in periods:
            db.add(Bitacora(
                number=period.number,
                period_start=period.start,
                period_end=period.end,
                delivery_date=period.delivery_date,
                status=BitacoraStatus.PENDING,
            ))
        await db.commit()


@router.get("", response_model=list[BitacoraListItem])
async def list_bitacoras(db: AsyncSession = Depends(get_db)):
    await _ensure_bitacoras_exist(db)

    result = await db.execute(
        select(Bitacora).order_by(Bitacora.number)
    )
    bitacoras = result.scalars().all()

    # Attach activity counts
    items = []
    for b in bitacoras:
        count_result = await db.execute(
            select(func.count()).select_from(Activity).where(Activity.bitacora_id == b.id)
        )
        count = count_result.scalar()
        item = BitacoraListItem(
            id=b.id,
            number=b.number,
            period_start=b.period_start,
            period_end=b.period_end,
            status=b.status,
            delivery_date=b.delivery_date,
            onedrive_url=b.onedrive_url,
            activity_count=count,
        )
        items.append(item)

    return items


@router.get("/{bitacora_id}", response_model=BitacoraOut)
async def get_bitacora(bitacora_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Bitacora)
        .options(selectinload(Bitacora.activities).selectinload(Activity.evidence_files))
        .where(Bitacora.id == bitacora_id)
    )
    bitacora = result.scalar_one_or_none()
    if not bitacora:
        raise HTTPException(status_code=404, detail="Bitácora no encontrada")
    return bitacora


@router.patch("/{bitacora_id}", response_model=BitacoraOut)
async def update_bitacora(
    bitacora_id: int,
    data: BitacoraUpdate,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Bitacora)
        .options(selectinload(Bitacora.activities).selectinload(Activity.evidence_files))
        .where(Bitacora.id == bitacora_id)
    )
    bitacora = result.scalar_one_or_none()
    if not bitacora:
        raise HTTPException(status_code=404, detail="Bitácora no encontrada")

    for field, value in data.model_dump(exclude_none=True).items():
        setattr(bitacora, field, value)

    await db.commit()
    await db.refresh(bitacora)

    result = await db.execute(
        select(Bitacora)
        .options(selectinload(Bitacora.activities).selectinload(Activity.evidence_files))
        .where(Bitacora.id == bitacora_id)
    )
    return result.scalar_one()


@router.post("/{bitacora_id}/generate", response_model=BitacoraOut)
async def generate_bitacora(
    bitacora_id: int,
    req: GenerateRequest,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Bitacora)
        .options(selectinload(Bitacora.activities).selectinload(Activity.evidence_files))
        .where(Bitacora.id == bitacora_id)
    )
    bitacora = result.scalar_one_or_none()
    if not bitacora:
        raise HTTPException(status_code=404, detail="Bitácora no encontrada")

    if bitacora.activities and not req.regenerate:
        raise HTTPException(
            status_code=400,
            detail="Esta bitácora ya tiene actividades. Usa regenerate=true para reemplazarlas."
        )

    # ── Modo bypass: actividades pre-generadas (ej: por Claude Code) ──────────
    if req.activities:
        generated = [
            {**act.model_dump(), "is_ai_generated": False, "order_index": i}
            for i, act in enumerate(req.activities)
        ]
    else:
        # Fetch work items
        if req.work_item_ids:
            work_items = await azure_devops.fetch_work_items_by_ids(req.work_item_ids)
        else:
            work_items = await azure_devops.fetch_work_items_by_date_range(
                bitacora.period_start, bitacora.period_end
            )

        if not work_items:
            raise HTTPException(
                status_code=404,
                detail=f"No se encontraron work items entre {bitacora.period_start} y {bitacora.period_end}"
            )

        period = get_period_for_bitacora(bitacora.number)
        generated = await claude_service.generate_bitacora_activities(
            bitacora_number=bitacora.number,
            period_label=period.label,
            work_items=work_items,
        )

    # If regenerating, delete existing activities
    if req.regenerate and bitacora.activities:
        for act in bitacora.activities:
            await db.delete(act)
        await db.flush()

    for act_data in generated:
        start_d = act_data.get("start_date")
        end_d = act_data.get("end_date")
        if isinstance(start_d, str):
            from datetime import datetime
            start_d = datetime.strptime(start_d, "%Y-%m-%d").date()
        if isinstance(end_d, str):
            from datetime import datetime
            end_d = datetime.strptime(end_d, "%Y-%m-%d").date()

        activity = Activity(
            bitacora_id=bitacora.id,
            order_index=act_data.get("order_index", 0),
            title=act_data["title"],
            description=act_data["description"],
            competencias=act_data.get("competencias"),
            start_date=start_d,
            end_date=end_d,
            evidence_description=act_data.get("evidence_description"),
            observations=act_data.get("observations"),
            azure_work_item_ids=act_data.get("azure_work_item_ids"),
            is_ai_generated=True,
        )
        db.add(activity)

    bitacora.status = BitacoraStatus.DRAFT
    await db.commit()

    # Reload with activities
    result = await db.execute(
        select(Bitacora)
        .options(selectinload(Bitacora.activities).selectinload(Activity.evidence_files))
        .where(Bitacora.id == bitacora_id)
    )
    return result.scalar_one()


@router.post("/{bitacora_id}/export")
async def export_bitacora(bitacora_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Bitacora)
        .options(selectinload(Bitacora.activities))
        .where(Bitacora.id == bitacora_id)
    )
    bitacora = result.scalar_one_or_none()
    if not bitacora:
        raise HTTPException(status_code=404, detail="Bitácora no encontrada")
    if not bitacora.activities:
        raise HTTPException(status_code=400, detail="La bitácora no tiene actividades")

    activities_data = [
        {
            "title": a.title,
            "description": a.description,
            "competencias": a.competencias,
            "start_date": a.start_date,
            "end_date": a.end_date,
            "evidence_description": a.evidence_description,
            "observations": a.observations,
        }
        for a in sorted(bitacora.activities, key=lambda x: x.order_index)
    ]

    output_path = excel_service.generate_excel(
        bitacora_number=bitacora.number,
        period_start=bitacora.period_start,
        period_end=bitacora.period_end,
        activities=activities_data,
        delivery_date=bitacora.delivery_date,
    )

    bitacora.excel_file_path = str(output_path)
    bitacora.status = BitacoraStatus.EXPORTED
    await db.commit()

    return {
        "message": "Excel generado exitosamente",
        "file_path": str(output_path),
        "download_url": f"/api/bitacoras/{bitacora_id}/download",
    }


@router.get("/{bitacora_id}/download")
async def download_bitacora(bitacora_id: int, db: AsyncSession = Depends(get_db)):
    from fastapi.responses import FileResponse

    result = await db.execute(select(Bitacora).where(Bitacora.id == bitacora_id))
    bitacora = result.scalar_one_or_none()
    if not bitacora or not bitacora.excel_file_path:
        raise HTTPException(status_code=404, detail="Archivo no generado aún")

    from pathlib import Path
    file_path = Path(bitacora.excel_file_path)
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Archivo no encontrado en disco")

    return FileResponse(
        path=str(file_path),
        filename=file_path.name,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


@router.post("/{bitacora_id}/upload-onedrive")
async def upload_to_onedrive(bitacora_id: int, db: AsyncSession = Depends(get_db)):
    if not onedrive_service.is_configured():
        raise HTTPException(status_code=400, detail="OneDrive no está configurado")

    result = await db.execute(select(Bitacora).where(Bitacora.id == bitacora_id))
    bitacora = result.scalar_one_or_none()
    if not bitacora or not bitacora.excel_file_path:
        raise HTTPException(status_code=400, detail="Primero debes exportar el Excel")

    from pathlib import Path
    file_path = Path(bitacora.excel_file_path)
    url = await onedrive_service.upload_file(file_path, file_path.name)

    if url:
        bitacora.onedrive_url = url
        bitacora.status = BitacoraStatus.UPLOADED
        await db.commit()
        return {"message": "Subido exitosamente", "url": url}

    raise HTTPException(status_code=500, detail="Error al subir a OneDrive")
