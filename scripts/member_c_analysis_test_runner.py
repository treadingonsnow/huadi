from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from typing import Any, Callable

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

sys.path.insert(0, "backend")
sys.path.insert(0, ".")

from app.api.v1 import analysis as analysis_api


@dataclass
class Case:
    case_id: str
    name: str
    path: str
    expected: str
    validator: Callable[[dict[str, Any]], bool]


def build_session_factory() -> sessionmaker[Session]:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    session_factory = sessionmaker(bind=engine)
    session = session_factory()
    session.execute(
        text(
            "CREATE TABLE restaurant_info ("
            "restaurant_id TEXT PRIMARY KEY, "
            "restaurant_name TEXT, "
            "district TEXT, "
            "cuisine_type TEXT, "
            "avg_price REAL, "
            "rating_overall REAL)"
        )
    )
    session.execute(
        text(
            "CREATE TABLE restaurant_review ("
            "review_id TEXT PRIMARY KEY, "
            "restaurant_id TEXT, "
            "review_content TEXT, "
            "sentiment_score REAL, "
            "rating_overall REAL, "
            "review_time TEXT)"
        )
    )
    session.execute(
        text(
            """
            INSERT INTO restaurant_info
            (restaurant_id, restaurant_name, district, cuisine_type, avg_price, rating_overall)
            VALUES
            ('r1', '店1', '浦东新区', '川菜', 45, 3.8),
            ('r2', '店2', '浦东新区', '川菜', 80, 4.6),
            ('r3', '店3', '黄浦区', '粤菜', 150, 4.2),
            ('r4', '店4', '徐汇区', '本帮菜', 220, 4.9),
            ('r5', '店5', '黄浦区', '日料', 0, 0)
            """
        )
    )
    session.execute(
        text(
            """
            INSERT INTO restaurant_review
            (review_id, restaurant_id, review_content, sentiment_score, rating_overall, review_time)
            VALUES
            ('v1', 'r2', '味道好吃 服务贴心 环境舒适', 0.9, 4.8, '2026-01-01'),
            ('v2', 'r3', '新鲜 美味 交通方便', 0.6, 4.3, '2026-01-02'),
            ('v3', 'r4', '体验不错 菜品精致', 0.4, 4.7, '2026-01-03'),
            ('v4', 'r1', '太贵 服务差 排队久', -0.8, 2.3, '2026-01-04'),
            ('v5', 'r3', '难吃 不推荐 服务慢', -0.7, 2.1, '2026-01-05'),
            ('v6', 'r5', '价格离谱 环境一般', -0.5, 2.0, '2026-01-06')
            """
        )
    )
    session.commit()
    session.close()
    return session_factory


def build_app(session_factory: sessionmaker[Session]) -> FastAPI:
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


def cases() -> list[Case]:
    return [
        Case(
            case_id="TC_ANALYSIS_001",
            name="概览接口",
            path="/api/v1/analysis/overview",
            expected="status=200, code=200, total_count=5, district_count=3",
            validator=lambda payload: payload.get("data", {}).get("total_count") == 5
            and payload.get("data", {}).get("district_count") == 3,
        ),
        Case(
            case_id="TC_ANALYSIS_002",
            name="区域分布接口",
            path="/api/v1/analysis/area-distribution",
            expected="status=200, code=200, districts数量=3",
            validator=lambda payload: len(payload.get("data", {}).get("districts", [])) == 3,
        ),
        Case(
            case_id="TC_ANALYSIS_003",
            name="菜系分布接口",
            path="/api/v1/analysis/cuisine-distribution",
            expected="status=200, code=200, cuisines数量=4",
            validator=lambda payload: len(payload.get("data", {}).get("cuisines", [])) == 4,
        ),
        Case(
            case_id="TC_ANALYSIS_004",
            name="价格分布接口",
            path="/api/v1/analysis/price-distribution",
            expected="status=200, code=200, 四个价格区间计数正确",
            validator=lambda payload: [item.get("count") for item in payload.get("data", {}).get("ranges", [])]
            == [1, 1, 1, 1],
        ),
        Case(
            case_id="TC_ANALYSIS_005",
            name="评分分布接口",
            path="/api/v1/analysis/rating-distribution",
            expected="status=200, code=200, 四个评分区间计数正确",
            validator=lambda payload: [item.get("count") for item in payload.get("data", {}).get("ratings", [])]
            == [1, 1, 1, 2],
        ),
        Case(
            case_id="TC_ANALYSIS_006",
            name="区域均价接口",
            path="/api/v1/analysis/area-avg-price",
            expected="status=200, code=200, district按均价降序返回",
            validator=lambda payload: [item.get("name") for item in payload.get("data", {}).get("districts", [])]
            == ["徐汇区", "黄浦区", "浦东新区"],
        ),
        Case(
            case_id="TC_ANALYSIS_007",
            name="关键词接口默认参数",
            path="/api/v1/analysis/review-keywords",
            expected="status=200, code=200, positive和negative均返回列表",
            validator=lambda payload: isinstance(payload.get("data", {}).get("positive"), list)
            and isinstance(payload.get("data", {}).get("negative"), list),
        ),
        Case(
            case_id="TC_ANALYSIS_008",
            name="关键词接口limit参数",
            path="/api/v1/analysis/review-keywords?limit=2",
            expected="status=200, code=200, positive/negative长度<=2",
            validator=lambda payload: len(payload.get("data", {}).get("positive", [])) <= 2
            and len(payload.get("data", {}).get("negative", [])) <= 2,
        ),
    ]


def run() -> dict[str, Any]:
    session_factory = build_session_factory()
    app = build_app(session_factory)
    report_items: list[dict[str, Any]] = []
    with TestClient(app) as client:
        for case in cases():
            response = client.get(case.path, timeout=30)
            payload = response.json()
            base_ok = response.status_code == 200 and payload.get("code") == 200 and payload.get("message") == "success"
            detail_ok = case.validator(payload)
            passed = base_ok and detail_ok
            item = {
                "case_id": case.case_id,
                "name": case.name,
                "path": case.path,
                "expected": case.expected,
                "status_code": response.status_code,
                "passed": passed,
                "actual": payload,
            }
            report_items.append(item)
            print(f"{case.case_id} {case.name} {'PASS' if passed else 'FAIL'}")
            if not passed:
                raise RuntimeError(f"测试失败: {case.case_id}")
    return {"all_passed": all(item["passed"] for item in report_items), "items": report_items}


def main() -> None:
    report = run()
    print("ALL_CASES_PASSED", report["all_passed"])
    print("REPORT_JSON_START")
    print(json.dumps(report, ensure_ascii=False))
    print("REPORT_JSON_END")


if __name__ == "__main__":
    main()
