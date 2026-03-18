from __future__ import annotations

from collections.abc import Generator
from typing import Any


def get_db() -> Generator[Any, None, None]:
    try:
        from app.database import get_db as database_get_db
    except Exception as exc:
        raise RuntimeError("数据库依赖未配置，请先实现 app.database.get_db") from exc
    yield from database_get_db()
