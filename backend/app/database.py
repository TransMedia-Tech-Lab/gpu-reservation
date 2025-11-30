from pathlib import Path
from typing import Generator

from sqlmodel import Session, SQLModel, create_engine

from .config import get_settings

settings = get_settings()


def _build_engine():
    Path(settings.data_dir).mkdir(parents=True, exist_ok=True)
    connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}
    return create_engine(settings.database_url, echo=settings.echo_sql, connect_args=connect_args)


engine = _build_engine()


def init_db() -> None:
    """テーブルを作成。アプリ起動時に一度だけ呼ぶ。"""
    SQLModel.metadata.create_all(engine)


def get_session() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session

