from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

sys.path.insert(0, "backend")
sys.path.insert(0, ".")

from app.api.v1 import analysis as analysis_api


def load_env_file() -> None:
    env_path = Path(".env")
    if not env_path.exists():
        return
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip("'").strip('"'))


def build_db_url() -> str:
    host = os.getenv("MYSQL_HOST")
    port = os.getenv("MYSQL_PORT", "3306")
    user = os.getenv("MYSQL_USER")
    password = os.getenv("MYSQL_PASSWORD", "")
    database = os.getenv("MYSQL_DATABASE")
    if not all([host, user, database]):
        raise RuntimeError("缺少 MySQL 配置，请检查 .env 中 MYSQL_HOST/MYSQL_USER/MYSQL_DATABASE")
    return f"mysql+pymysql://{user}:{password}@{host}:{port}/{database}?charset=utf8mb4"


def check_tables(db: Session) -> None:
    needed = {"restaurant_info", "restaurant_review"}
    rows = db.execute(
        text(
            """
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = :schema
            """
        ),
        {"schema": os.getenv("MYSQL_DATABASE")},
    ).mappings().all()
    existing = {
        str(row.get("table_name") or row.get("TABLE_NAME") or next(iter(row.values())))
        for row in rows
    }
    missing = needed - existing
    if missing:
        raise RuntimeError(f"缺少必要数据表: {', '.join(sorted(missing))}")


def create_app(session_factory: sessionmaker[Session]) -> FastAPI:
    app = FastAPI()
    app.include_router(analysis_api.router, prefix="/api/v1")

    def override_get_db() -> Any:
        db = session_factory()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[analysis_api.get_db] = override_get_db
    return app


def validate_endpoints(client: TestClient) -> dict[str, Any]:
    paths = [
        "/api/v1/analysis/overview",
        "/api/v1/analysis/area-distribution",
        "/api/v1/analysis/cuisine-distribution",
        "/api/v1/analysis/price-distribution",
        "/api/v1/analysis/rating-distribution",
        "/api/v1/analysis/area-avg-price",
        "/api/v1/analysis/review-keywords",
    ]
    report: dict[str, Any] = {}
    for path in paths:
        response = client.get(path, timeout=30)
        payload = response.json() if response.headers.get("content-type", "").startswith("application/json") else {}
        ok = response.status_code == 200 and payload.get("code") == 200
        report[path] = {
            "status_code": response.status_code,
            "ok": ok,
            "message": payload.get("message"),
            "has_data": payload.get("data") is not None,
        }
        if not ok:
            raise RuntimeError(f"{path} 校验失败: {report[path]}")
    return report


def main() -> None:
    load_env_file()
    url = build_db_url()
    engine = create_engine(url, pool_pre_ping=True)
    session_factory = sessionmaker(bind=engine)

    db = session_factory()
    try:
        check_tables(db)
        db.execute(text("SELECT 1"))
    finally:
        db.close()

    app = create_app(session_factory)
    with TestClient(app) as client:
        report = validate_endpoints(client)
    print("real_db_e2e_validation_passed")
    for path, item in report.items():
        print(path, item["status_code"], item["ok"], item["has_data"])


if __name__ == "__main__":
    main()
