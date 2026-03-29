from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel
from app.models.bitacora import BitacoraStatus


# ─── Evidence ────────────────────────────────────────────────────────────────

class EvidenceOut(BaseModel):
    id: int
    activity_id: int
    file_name: str
    file_type: str
    file_size: Optional[int]
    onedrive_url: Optional[str]
    uploaded_at: datetime

    model_config = {"from_attributes": True}


# ─── Activity ─────────────────────────────────────────────────────────────────

class ActivityCreate(BaseModel):
    title: str
    description: str
    competencias: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    evidence_description: Optional[str] = None
    observations: Optional[str] = None
    azure_work_item_ids: Optional[list[int]] = None
    order_index: int = 0


class ActivityUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    competencias: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    evidence_description: Optional[str] = None
    observations: Optional[str] = None
    azure_work_item_ids: Optional[list[int]] = None
    order_index: Optional[int] = None


class ActivityOut(BaseModel):
    id: int
    bitacora_id: int
    order_index: int
    title: str
    description: str
    competencias: Optional[str]
    start_date: Optional[date]
    end_date: Optional[date]
    evidence_description: Optional[str]
    observations: Optional[str]
    azure_work_item_ids: Optional[list]
    is_ai_generated: bool
    created_at: datetime
    updated_at: datetime
    evidence_files: list[EvidenceOut] = []

    model_config = {"from_attributes": True}


# ─── Bitácora ─────────────────────────────────────────────────────────────────

class BitacoraUpdate(BaseModel):
    delivery_date: Optional[date] = None
    notes: Optional[str] = None
    status: Optional[BitacoraStatus] = None


class BitacoraOut(BaseModel):
    id: int
    number: int
    period_start: date
    period_end: date
    status: BitacoraStatus
    delivery_date: Optional[date]
    excel_file_path: Optional[str]
    onedrive_url: Optional[str]
    notes: Optional[str]
    created_at: datetime
    updated_at: datetime
    activities: list[ActivityOut] = []

    model_config = {"from_attributes": True}


class BitacoraListItem(BaseModel):
    id: int
    number: int
    period_start: date
    period_end: date
    status: BitacoraStatus
    delivery_date: Optional[date]
    onedrive_url: Optional[str]
    activity_count: int = 0

    model_config = {"from_attributes": True}


# ─── Work Items ───────────────────────────────────────────────────────────────

class WorkItemOut(BaseModel):
    azure_id: int
    title: str
    description: Optional[str]
    work_item_type: str
    state: str
    assigned_to: Optional[str]
    area_path: Optional[str]
    tags: Optional[str]
    completed_work: Optional[float]
    original_estimate: Optional[float]
    created_date: Optional[datetime]
    changed_date: Optional[datetime]
    closed_date: Optional[datetime]
    url: Optional[str]

    model_config = {"from_attributes": True}


# ─── Generate request ─────────────────────────────────────────────────────────

class ActivityImport(BaseModel):
    """Actividad pre-generada (ej: por Claude Code). Bypasea la API de Claude."""
    title: str
    description: str
    competencias: Optional[str] = None
    start_date: Optional[str] = None  # YYYY-MM-DD
    end_date: Optional[str] = None    # YYYY-MM-DD
    evidence_description: Optional[str] = None
    observations: Optional[str] = None
    azure_work_item_ids: Optional[list[int]] = None
    order_index: int = 0


class GenerateRequest(BaseModel):
    work_item_ids: Optional[list[int]] = None  # Si None, usa todos del período
    regenerate: bool = False  # Si True, reemplaza actividades existentes
    activities: Optional[list[ActivityImport]] = None  # Si se provee, bypasea Claude API


class ReorderActivities(BaseModel):
    activity_ids: list[int]  # IDs en el nuevo orden
