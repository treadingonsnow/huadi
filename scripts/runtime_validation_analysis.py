from __future__ import annotations

import sys

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

sys.path.insert(0, "backend")
sys.path.insert(0, ".")

from app.api.v1 import analysis as api_analysis
from app.services.analysis_service import AnalysisService


def main() -> None:
    engine = create_engine("sqlite:///:memory:")
    session = sessionmaker(bind=engine)()
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
            ('r1', '店1', '浦东新区', '川菜', 80, 4.6),
            ('r2', '店2', '黄浦区', '粤菜', 150, 4.2),
            ('r3', '店3', '浦东新区', '川菜', 45, 3.8)
            """
        )
    )
    session.execute(
        text(
            """
            INSERT INTO restaurant_review
            (review_id, restaurant_id, review_content, sentiment_score, rating_overall, review_time)
            VALUES
            ('v1', 'r1', '味道好吃 服务好', 0.9, 4.8, '2026-01-01'),
            ('v2', 'r2', '太贵 服务差', -0.7, 2.3, '2026-01-02')
            """
        )
    )
    session.commit()

    service = AnalysisService(session)
    outputs = [
        service.get_overview(),
        service.get_area_distribution(),
        service.get_cuisine_distribution(),
        service.get_price_distribution(),
        service.get_rating_distribution(),
        service.get_area_avg_price(),
        service.get_review_keywords(limit=10),
    ]
    assert all(isinstance(item, dict) for item in outputs)

    expected_paths = {
        "/analysis/overview",
        "/analysis/area-distribution",
        "/analysis/cuisine-distribution",
        "/analysis/price-distribution",
        "/analysis/rating-distribution",
        "/analysis/area-avg-price",
        "/analysis/review-keywords",
    }
    actual_paths = {route.path for route in api_analysis.router.routes}
    assert expected_paths == actual_paths

    assert api_analysis.get_overview(session)["code"] == 200
    assert api_analysis.get_area_distribution(session)["code"] == 200
    assert api_analysis.get_cuisine_distribution(session)["code"] == 200
    assert api_analysis.get_price_distribution(session)["code"] == 200
    assert api_analysis.get_rating_distribution(session)["code"] == 200
    assert api_analysis.get_area_avg_price(session)["code"] == 200
    assert api_analysis.get_review_keywords(10, session)["code"] == 200
    print("runtime_validation_passed")


if __name__ == "__main__":
    main()
