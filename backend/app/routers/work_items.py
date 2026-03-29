from datetime import date
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.database import get_db
from app.models.bitacora import WorkItemCache, Bitacora
from app.schemas.bitacora import WorkItemOut
from app.services import azure_devops

router = APIRouter(prefix="/api/work-items", tags=["work-items"])


@router.get("", response_model=list[WorkItemOut])
async def get_work_items(
    start_date: date = Query(...),
    end_date: date = Query(...),
    use_cache: bool = Query(True),
    db: AsyncSession = Depends(get_db),
):
    """
    Fetch work items for a date range.
    By default uses cached data; set use_cache=false to force refresh from Azure DevOps.
    """
    if use_cache:
        result = await db.execute(
            select(WorkItemCache).where(
                or_(
                    WorkItemCache.changed_date.between(start_date, end_date),
                    WorkItemCache.closed_date.between(start_date, end_date),
                )
            ).order_by(WorkItemCache.changed_date.desc())
        )
        cached = result.scalars().all()
        if cached:
            return cached

    # Fetch fresh from Azure DevOps
    raw_items = await azure_devops.fetch_work_items_by_date_range(start_date, end_date)
    if not raw_items:
        return []

    # Upsert into cache
    for item in raw_items:
        existing = await db.execute(
            select(WorkItemCache).where(WorkItemCache.azure_id == item["azure_id"])
        )
        cached_item = existing.scalar_one_or_none()

        if cached_item:
            for k, v in item.items():
                if k != "azure_id":
                    setattr(cached_item, k, v)
        else:
            db.add(WorkItemCache(**item))

    await db.commit()

    # Return from cache
    result = await db.execute(
        select(WorkItemCache).where(
            or_(
                WorkItemCache.changed_date.between(start_date, end_date),
                WorkItemCache.closed_date.between(start_date, end_date),
            )
        ).order_by(WorkItemCache.changed_date.desc())
    )
    return result.scalars().all()


@router.post("/sync")
async def sync_work_items(
    start_date: date = Query(...),
    end_date: date = Query(...),
    db: AsyncSession = Depends(get_db),
):
    """Force sync work items from Azure DevOps into the local cache."""
    raw_items = await azure_devops.fetch_work_items_by_date_range(start_date, end_date)

    synced = 0
    for item in raw_items:
        existing = await db.execute(
            select(WorkItemCache).where(WorkItemCache.azure_id == item["azure_id"])
        )
        cached_item = existing.scalar_one_or_none()

        if cached_item:
            for k, v in item.items():
                if k != "azure_id":
                    setattr(cached_item, k, v)
        else:
            db.add(WorkItemCache(**item))
        synced += 1

    await db.commit()
    return {"message": f"Sincronizados {synced} work items", "count": synced}


@router.get("/by-bitacora/{bitacora_id}", response_model=list[WorkItemOut])
async def get_work_items_for_bitacora(
    bitacora_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Get work items for a specific bitácora's date range."""
    result = await db.execute(select(Bitacora).where(Bitacora.id == bitacora_id))
    bitacora = result.scalar_one_or_none()
    if not bitacora:
        raise HTTPException(status_code=404, detail="Bitácora no encontrada")

    raw_items = await azure_devops.fetch_work_items_by_date_range(
        bitacora.period_start, bitacora.period_end
    )
    return [WorkItemOut(**item) for item in raw_items]
