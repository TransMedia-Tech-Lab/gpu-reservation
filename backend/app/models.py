from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import Column, DateTime
from sqlmodel import Field, Relationship, SQLModel


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class GPUBase(SQLModel):
    name: str = Field(index=True, description="物理GPUの識別名")
    hostname: Optional[str] = Field(
        default=None, index=True, description="GPUが載っているサーバーのホスト名など"
    )
    slot: Optional[str] = Field(default=None, description="ノード内のスロット/インデックス")
    model: Optional[str] = Field(default=None, description="GPU型番 (例: RTX 4090)")
    memory_gb: Optional[float] = Field(default=None, description="メモリ容量(GB)")
    notes: Optional[str] = Field(default=None, description="補足情報")


class GPU(GPUBase, table=True):
    __tablename__ = "gpus"

    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=utcnow, sa_column=Column(DateTime(timezone=True)))

    reservations: list["Reservation"] = Relationship(back_populates="gpu")


class GPURead(GPUBase):
    id: int
    created_at: datetime


class GPUCreate(GPUBase):
    pass


class GPUUpdate(SQLModel):
    name: Optional[str] = None
    hostname: Optional[str] = None
    slot: Optional[str] = None
    model: Optional[str] = None
    memory_gb: Optional[float] = None
    notes: Optional[str] = None


class ReservationBase(SQLModel):
    gpu_id: int = Field(foreign_key="gpus.id")
    user: str = Field(description="利用者名など")
    purpose: Optional[str] = Field(default=None, description="利用目的")
    start_time: datetime = Field(sa_column=Column(DateTime(timezone=True)))
    end_time: datetime = Field(sa_column=Column(DateTime(timezone=True)))
    status: str = Field(default="confirmed", description="confirmed / cancelled など")


class Reservation(ReservationBase, table=True):
    __tablename__ = "reservations"

    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=utcnow, sa_column=Column(DateTime(timezone=True)))

    gpu: GPU = Relationship(back_populates="reservations")


class ReservationRead(ReservationBase):
    id: int
    created_at: datetime


class ReservationCreate(SQLModel):
    gpu_id: int
    user: str
    purpose: Optional[str] = None
    start_time: datetime
    end_time: datetime


class ReservationUpdate(SQLModel):
    purpose: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    status: Optional[str] = None


class GPUStatus(SQLModel):
    gpu: GPURead
    is_available_now: bool
    current_reservation: Optional[ReservationRead] = None
    next_reservation: Optional[ReservationRead] = None


class AvailabilityResponse(SQLModel):
    start_time: datetime
    end_time: datetime
    available_gpus: list[GPURead]
    reserved_gpus: list[GPURead]


__all__ = [
    "GPU",
    "GPUBase",
    "GPUCreate",
    "GPURead",
    "GPUUpdate",
    "GPUStatus",
    "Reservation",
    "ReservationBase",
    "ReservationCreate",
    "ReservationRead",
    "ReservationUpdate",
    "AvailabilityResponse",
]

