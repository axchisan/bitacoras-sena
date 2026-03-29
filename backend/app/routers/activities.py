from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models.bitacora import Activity, Bitacora, BitacoraStatus
from app.schemas.bitacora import ActivityCreate, ActivityUpdate, ActivityOut, ReorderActivities

router = APIRouter(prefix="/api/activities", tags=["activities"])


@router.post("", response_model=ActivityOut)
async def create_activity(data: ActivityCreate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Bitacora).where(Bitacora.id == data.bitacora_id
                                                      if hasattr(data, 'bitacora_id') else True))
    activity = Activity(**data.model_dump())
    db.add(activity)
    await db.commit()
    await db.refresh(activity)
    return activity


@router.get("/{activity_id}", response_model=ActivityOut)
async def get_activity(activity_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Activity)
        .options(selectinload(Activity.evidence_files))
        .where(Activity.id == activity_id)
    )
    activity = result.scalar_one_or_none()
    if not activity:
        raise HTTPException(status_code=404, detail="Actividad no encontrada")
    return activity


@router.patch("/{activity_id}", response_model=ActivityOut)
async def update_activity(
    activity_id: int,
    data: ActivityUpdate,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Activity)
        .options(selectinload(Activity.evidence_files))
        .where(Activity.id == activity_id)
    )
    activity = result.scalar_one_or_none()
    if not activity:
        raise HTTPException(status_code=404, detail="Actividad no encontrada")

    for field, value in data.model_dump(exclude_none=True).items():
        setattr(activity, field, value)

    # Update parent bitácora to DRAFT if it was READY/EXPORTED
    b_result = await db.execute(select(Bitacora).where(Bitacora.id == activity.bitacora_id))
    bitacora = b_result.scalar_one_or_none()
    if bitacora and bitacora.status in (BitacoraStatus.READY, BitacoraStatus.EXPORTED):
        bitacora.status = BitacoraStatus.DRAFT

    await db.commit()
    await db.refresh(activity)
    return activity


@router.delete("/{activity_id}")
async def delete_activity(activity_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Activity).where(Activity.id == activity_id))
    activity = result.scalar_one_or_none()
    if not activity:
        raise HTTPException(status_code=404, detail="Actividad no encontrada")
    await db.delete(activity)
    await db.commit()
    return {"message": "Actividad eliminada"}


@router.post("/reorder")
async def reorder_activities(data: ReorderActivities, db: AsyncSession = Depends(get_db)):
    for idx, activity_id in enumerate(data.activity_ids):
        result = await db.execute(select(Activity).where(Activity.id == activity_id))
        activity = result.scalar_one_or_none()
        if activity:
            activity.order_index = idx
    await db.commit()
    return {"message": "Orden actualizado"}
