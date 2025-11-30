from datetime import datetime, timedelta, timezone

from sqlmodel import Session, select

from .database import engine, init_db
from .models import GPU, Reservation


def seed() -> None:
    """簡易サンプルデータ投入。既存データがあれば何もしない。"""
    init_db()

    with Session(engine) as session:
        if session.exec(select(GPU)).first():
            print("既にGPUデータが存在するため、シードはスキップしました。")
            return

        gpus = [
            GPU(
                name="RTX5090-1",
                hostname="lab-node-1",
                slot="GPU0",
                model="RTX 5090",
                memory_gb=32,
            ),
        ]
        session.add_all(gpus)
        session.commit()
        session.refresh(gpus[0])

        now = datetime.now(timezone.utc)
        reservations = [
            Reservation(
                gpu_id=gpus[0].id,
                user="alice",
                purpose="モデル学習",
                start_time=now + timedelta(hours=1),
                end_time=now + timedelta(hours=5),
                status="confirmed",
            ),
        ]
        session.add_all(reservations)
        session.commit()

    print("シードデータを投入しました。")


if __name__ == "__main__":
    seed()
