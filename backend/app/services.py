from datetime import datetime, timezone
from typing import Optional, Tuple
from zoneinfo import ZoneInfo

from fastapi import HTTPException, status
from sqlmodel import Session, select

from .config import Settings
from .models import (
    AvailabilityResponse,
    GPU,
    GPURead,
    GPUStatus,
    Reservation,
    ReservationCreate,
    ReservationRead,
    ReservationUpdate,
)


def normalize_window(
    start_time: datetime, end_time: datetime, settings: Settings
) -> Tuple[datetime, datetime]:
    """タイムゾーン付きの時間範囲をUTCに正規化する。"""
    zone = ZoneInfo(settings.timezone)

    if start_time.tzinfo is None:
        start_time = start_time.replace(tzinfo=zone)
    if end_time.tzinfo is None:
        end_time = end_time.replace(tzinfo=zone)

    start_utc = start_time.astimezone(timezone.utc)
    end_utc = end_time.astimezone(timezone.utc)

    if start_utc >= end_utc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="start_time は end_time より前にしてください。",
        )

    return start_utc, end_utc


def to_utc(value: datetime, settings: Settings) -> datetime:
    zone = ZoneInfo(settings.timezone)
    if value.tzinfo is None:
        value = value.replace(tzinfo=zone)
    return value.astimezone(timezone.utc)


def get_gpu_or_404(session: Session, gpu_id: int) -> GPU:
    gpu = session.get(GPU, gpu_id)
    if not gpu:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="GPU が見つかりません。")
    return gpu


def _find_overlap(
    session: Session, gpu_id: int, start: datetime, end: datetime, exclude_id: Optional[int] = None
) -> Optional[Reservation]:
    statement = select(Reservation).where(
        Reservation.gpu_id == gpu_id,
        Reservation.status != "cancelled",
        Reservation.start_time < end,
        Reservation.end_time > start,
    )
    if exclude_id:
        statement = statement.where(Reservation.id != exclude_id)

    return session.exec(statement).first()


def create_reservation(
    session: Session, payload: ReservationCreate, settings: Settings
) -> ReservationRead:
    start_utc, end_utc = normalize_window(payload.start_time, payload.end_time, settings)
    get_gpu_or_404(session, payload.gpu_id)

    overlap = _find_overlap(session, payload.gpu_id, start_utc, end_utc)
    if overlap:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="指定した時間帯はすでに予約があります。",
        )

    reservation = Reservation(
        gpu_id=payload.gpu_id,
        user=payload.user,
        purpose=payload.purpose,
        start_time=start_utc,
        end_time=end_utc,
        status="confirmed",
    )
    session.add(reservation)
    session.commit()
    session.refresh(reservation)
    return ReservationRead.model_validate(reservation)


def update_reservation(
    session: Session, reservation_id: int, payload: ReservationUpdate, settings: Settings
) -> ReservationRead:
    reservation = session.get(Reservation, reservation_id)
    if not reservation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="予約が見つかりません。")

    start = payload.start_time or reservation.start_time
    end = payload.end_time or reservation.end_time

    start_utc, end_utc = normalize_window(start, end, settings)
    overlap = _find_overlap(session, reservation.gpu_id, start_utc, end_utc, exclude_id=reservation.id)
    if overlap:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="指定した時間帯はすでに予約があります。",
        )

    reservation.start_time = start_utc
    reservation.end_time = end_utc
    reservation.purpose = payload.purpose if payload.purpose is not None else reservation.purpose
    reservation.status = payload.status or reservation.status

    session.add(reservation)
    session.commit()
    session.refresh(reservation)
    return ReservationRead.model_validate(reservation)


def delete_reservation(session: Session, reservation_id: int) -> None:
    reservation = session.get(Reservation, reservation_id)
    if not reservation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="予約が見つかりません。")
    session.delete(reservation)
    session.commit()


def build_gpu_status(session: Session, gpu: GPU, now: datetime) -> GPUStatus:
    current_stmt = (
        select(Reservation)
        .where(
            Reservation.gpu_id == gpu.id,
            Reservation.status != "cancelled",
            Reservation.start_time <= now,
            Reservation.end_time > now,
        )
        .order_by(Reservation.start_time)
    )
    current = session.exec(current_stmt).first()

    next_stmt = (
        select(Reservation)
        .where(
            Reservation.gpu_id == gpu.id,
            Reservation.status != "cancelled",
            Reservation.start_time > now,
        )
        .order_by(Reservation.start_time)
    )
    next_reservation = session.exec(next_stmt).first()

    return GPUStatus(
        gpu=GPURead.model_validate(gpu),
        is_available_now=current is None,
        current_reservation=ReservationRead.model_validate(current) if current else None,
        next_reservation=ReservationRead.model_validate(next_reservation) if next_reservation else None,
    )


def availability_for_window(
    session: Session, start: datetime, end: datetime, settings: Settings
) -> AvailabilityResponse:
    start_utc, end_utc = normalize_window(start, end, settings)
    gpus = session.exec(select(GPU)).all()

    available: list[GPURead] = []
    reserved: list[GPURead] = []

    for gpu in gpus:
        overlap = _find_overlap(session, gpu.id, start_utc, end_utc)
        (reserved if overlap else available).append(GPURead.model_validate(gpu))

    return AvailabilityResponse(
        start_time=start_utc,
        end_time=end_utc,
        available_gpus=available,
        reserved_gpus=reserved,
    )
