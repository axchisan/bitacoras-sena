import enum
from datetime import date, datetime
from sqlalchemy import String, Text, Date, DateTime, Integer, Enum, Boolean, ForeignKey, JSON, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from app.database import Base


class BitacoraStatus(str, enum.Enum):
    PENDING = "pending"       # No generada aún
    DRAFT = "draft"           # En borrador (generada por IA, sin confirmar)
    READY = "ready"           # Confirmada, lista para exportar
    EXPORTED = "exported"     # Excel generado
    UPLOADED = "uploaded"     # Subida a OneDrive


class Bitacora(Base):
    __tablename__ = "bitacoras"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    number: Mapped[int] = mapped_column(Integer, unique=True, nullable=False)
    period_start: Mapped[date] = mapped_column(Date, nullable=False)
    period_end: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[BitacoraStatus] = mapped_column(
        Enum(BitacoraStatus), default=BitacoraStatus.PENDING, nullable=False
    )
    delivery_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    excel_file_path: Mapped[str | None] = mapped_column(String(512), nullable=True)
    onedrive_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    activities: Mapped[list["Activity"]] = relationship(
        "Activity", back_populates="bitacora", cascade="all, delete-orphan",
        order_by="Activity.order_index"
    )


class Activity(Base):
    __tablename__ = "activities"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    bitacora_id: Mapped[int] = mapped_column(Integer, ForeignKey("bitacoras.id", ondelete="CASCADE"))
    order_index: Mapped[int] = mapped_column(Integer, default=0)

    title: Mapped[str] = mapped_column(String(512), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    competencias: Mapped[str | None] = mapped_column(Text, nullable=True)
    start_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    end_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    evidence_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    observations: Mapped[str | None] = mapped_column(Text, nullable=True)
    azure_work_item_ids: Mapped[list | None] = mapped_column(JSON, nullable=True)
    is_ai_generated: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    bitacora: Mapped["Bitacora"] = relationship("Bitacora", back_populates="activities")
    evidence_files: Mapped[list["Evidence"]] = relationship(
        "Evidence", back_populates="activity", cascade="all, delete-orphan"
    )


class Evidence(Base):
    __tablename__ = "evidence"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    activity_id: Mapped[int] = mapped_column(Integer, ForeignKey("activities.id", ondelete="CASCADE"))
    file_name: Mapped[str] = mapped_column(String(256), nullable=False)
    file_path: Mapped[str] = mapped_column(String(512), nullable=False)
    file_type: Mapped[str] = mapped_column(String(64), nullable=False)
    file_size: Mapped[int | None] = mapped_column(Integer, nullable=True)
    onedrive_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    uploaded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    activity: Mapped["Activity"] = relationship("Activity", back_populates="evidence_files")


class WorkItemCache(Base):
    __tablename__ = "work_item_cache"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    azure_id: Mapped[int] = mapped_column(Integer, unique=True, nullable=False)
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    work_item_type: Mapped[str] = mapped_column(String(64), nullable=False)
    state: Mapped[str] = mapped_column(String(64), nullable=False)
    assigned_to: Mapped[str | None] = mapped_column(String(256), nullable=True)
    area_path: Mapped[str | None] = mapped_column(String(256), nullable=True)
    iteration_path: Mapped[str | None] = mapped_column(String(256), nullable=True)
    tags: Mapped[str | None] = mapped_column(String(512), nullable=True)
    completed_work: Mapped[float | None] = mapped_column(Float, nullable=True)
    original_estimate: Mapped[float | None] = mapped_column(Float, nullable=True)
    created_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    changed_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    closed_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    cached_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
