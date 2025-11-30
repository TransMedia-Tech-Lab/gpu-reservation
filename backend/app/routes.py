from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel import Session, select

from .config import Settings, get_settings
from .database import get_session
from .models import (
    AvailabilityResponse,
    GPU,
    GPUCreate,
    GPURead,
    GPUStatus,
    GPUUpdate,
    Reservation,
    ReservationCreate,
    ReservationRead,
    ReservationUpdate,
)
from .services import (
    availability_for_window,
    build_gpu_status,
    create_reservation,
    delete_reservation,
    get_gpu_or_404,
    normalize_window,
    to_utc,
    update_reservation,
)

router = APIRouter()


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@router.post("/gpus", response_model=GPURead, status_code=status.HTTP_201_CREATED)
def create_gpu(
    payload: GPUCreate, session: Session = Depends(get_session)
) -> GPURead:
    gpu = GPU.model_validate(payload)
    session.add(gpu)
    session.commit()
    session.refresh(gpu)
    return GPURead.model_validate(gpu)


@router.get("/gpus", response_model=list[GPUStatus])
def list_gpus(
    session: Session = Depends(get_session),
) -> list[GPUStatus]:
    now = datetime.now(timezone.utc)
    gpus = session.exec(select(GPU).order_by(GPU.id)).all()
    return [build_gpu_status(session, gpu, now) for gpu in gpus]


@router.get("/gpus/{gpu_id}", response_model=GPUStatus)
def get_gpu(
    gpu_id: int,
    session: Session = Depends(get_session),
) -> GPUStatus:
    gpu = get_gpu_or_404(session, gpu_id)
    now = datetime.now(timezone.utc)
    return build_gpu_status(session, gpu, now)


@router.patch("/gpus/{gpu_id}", response_model=GPURead)
def update_gpu(
    gpu_id: int,
    payload: GPUUpdate,
    session: Session = Depends(get_session),
) -> GPURead:
    gpu = session.get(GPU, gpu_id)
    if not gpu:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="GPU が見つかりません。")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(gpu, field, value)

    session.add(gpu)
    session.commit()
    session.refresh(gpu)
    return GPURead.model_validate(gpu)


@router.get("/gpus/{gpu_id}/reservations", response_model=list[ReservationRead])
def list_gpu_reservations(
    gpu_id: int,
    start: Optional[datetime] = Query(default=None, description="この時刻以降の予約を取得"),
    end: Optional[datetime] = Query(default=None, description="この時刻以前の予約を取得"),
    session: Session = Depends(get_session),
    settings: Settings = Depends(get_settings),
) -> list[ReservationRead]:
    get_gpu_or_404(session, gpu_id)

    statement = select(Reservation).where(Reservation.gpu_id == gpu_id)

    if start and end:
        start_utc, end_utc = normalize_window(start, end, settings)
        statement = statement.where(Reservation.start_time < end_utc, Reservation.end_time > start_utc)
    elif start:
        start_utc = to_utc(start, settings)
        statement = statement.where(Reservation.end_time >= start_utc)
    elif end:
        end_utc = to_utc(end, settings)
        statement = statement.where(Reservation.start_time <= end_utc)

    statement = statement.order_by(Reservation.start_time)
    reservations = session.exec(statement).all()
    return [ReservationRead.model_validate(r) for r in reservations]


@router.get("/reservations", response_model=list[ReservationRead])
def list_reservations(
    start: Optional[datetime] = Query(default=None, description="この時刻以降の予約を取得"),
    end: Optional[datetime] = Query(default=None, description="この時刻以前の予約を取得"),
    gpu_id: Optional[int] = Query(default=None, description="特定GPUの予約に絞り込む"),
    session: Session = Depends(get_session),
    settings: Settings = Depends(get_settings),
) -> list[ReservationRead]:
    statement = select(Reservation)

    if gpu_id is not None:
        get_gpu_or_404(session, gpu_id)
        statement = statement.where(Reservation.gpu_id == gpu_id)

    if start and end:
        start_utc, end_utc = normalize_window(start, end, settings)
        statement = statement.where(Reservation.start_time < end_utc, Reservation.end_time > start_utc)
    elif start:
        start_utc = to_utc(start, settings)
        statement = statement.where(Reservation.end_time >= start_utc)
    elif end:
        end_utc = to_utc(end, settings)
        statement = statement.where(Reservation.start_time <= end_utc)

    statement = statement.order_by(Reservation.start_time)
    reservations = session.exec(statement).all()
    return [ReservationRead.model_validate(r) for r in reservations]


@router.post("/reservations", response_model=ReservationRead, status_code=status.HTTP_201_CREATED)
def create_reservation_endpoint(
    payload: ReservationCreate,
    session: Session = Depends(get_session),
    settings: Settings = Depends(get_settings),
) -> ReservationRead:
    return create_reservation(session, payload, settings)


@router.patch("/reservations/{reservation_id}", response_model=ReservationRead)
def update_reservation_endpoint(
    reservation_id: int,
    payload: ReservationUpdate,
    session: Session = Depends(get_session),
    settings: Settings = Depends(get_settings),
) -> ReservationRead:
    return update_reservation(session, reservation_id, payload, settings)


@router.delete("/reservations/{reservation_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_reservation_endpoint(
    reservation_id: int,
    session: Session = Depends(get_session),
) -> None:
    delete_reservation(session, reservation_id)
    return None


@router.get("/availability", response_model=AvailabilityResponse)
def availability(
    start: datetime = Query(..., description="開始時刻 (ISO8601)"),
    end: datetime = Query(..., description="終了時刻 (ISO8601)"),
    session: Session = Depends(get_session),
    settings: Settings = Depends(get_settings),
) -> AvailabilityResponse:
    return availability_for_window(session, start, end, settings)
