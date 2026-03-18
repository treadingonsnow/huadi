from __future__ import annotations

import re
from collections import Counter
from functools import lru_cache
from typing import Any

import jieba
from sqlalchemy import text
from sqlalchemy.orm import Session

from config.dictionaries.sentiment_dict import SENTIMENT_DICT


class AnalysisService:
    PRICE_RANGES = (
        ("50元以下", 0, 50),
        ("51-100元", 50, 100),
        ("101-200元", 100, 200),
        ("200元以上", 200, None),
    )
    RATING_RANGES = (
        ("3.0分以下", 0.0, 3.0, True, False),
        ("3.0-3.9分", 3.0, 4.0, True, False),
        ("4.0-4.4分", 4.0, 4.5, True, False),
        ("4.5-5.0分", 4.5, 5.0, True, True),
    )
    BASE_STOP_WORDS = {
        "真的",
        "就是",
        "这个",
        "那个",
        "还是",
        "我们",
        "你们",
        "他们",
        "感觉",
        "非常",
        "比较",
        "一个",
        "一点",
        "一下",
        "然后",
        "而且",
        "因为",
        "所以",
        "但是",
        "没有",
        "不是",
        "可以",
        "不会",
        "已经",
        "餐厅",
        "店里",
        "这家",
        "服务员",
    }
    CHINESE_WORD_PATTERN = re.compile(r"^[\u4e00-\u9fff]{2,}$")

    def __init__(self, db: Session) -> None:
        self.db = db

    def get_overview(self) -> dict[str, Any]:
        row = self.db.execute(
            text(
                """
                SELECT
                    COUNT(*) AS total_count,
                    COALESCE(ROUND(AVG(NULLIF(rating_overall, 0)), 2), 0) AS avg_rating,
                    COALESCE(ROUND(AVG(NULLIF(avg_price, 0)), 2), 0) AS avg_price,
                    COUNT(DISTINCT district) AS district_count
                FROM restaurant_info
                """
            )
        ).mappings().one()
        return dict(row)

    def get_area_distribution(self) -> dict[str, list[dict[str, Any]]]:
        rows = self.db.execute(
            text(
                """
                SELECT district AS name, COUNT(*) AS count
                FROM restaurant_info
                WHERE district IS NOT NULL AND district != ''
                GROUP BY district
                ORDER BY count DESC, district ASC
                """
            )
        ).mappings().all()
        return {"districts": [dict(row) for row in rows]}

    def get_cuisine_distribution(self) -> dict[str, list[dict[str, Any]]]:
        total = self.db.execute(
            text("SELECT COUNT(*) FROM restaurant_info WHERE cuisine_type IS NOT NULL AND cuisine_type != ''")
        ).scalar_one()
        rows = self.db.execute(
            text(
                """
                SELECT cuisine_type AS name, COUNT(*) AS count
                FROM restaurant_info
                WHERE cuisine_type IS NOT NULL AND cuisine_type != ''
                GROUP BY cuisine_type
                ORDER BY count DESC, cuisine_type ASC
                """
            )
        ).mappings().all()
        cuisines: list[dict[str, Any]] = []
        for row in rows:
            count = int(row["count"])
            percentage = round((count / total) * 100, 2) if total else 0
            cuisines.append({"name": row["name"], "count": count, "percentage": percentage})
        return {"cuisines": cuisines}

    def get_price_distribution(self) -> dict[str, list[dict[str, Any]]]:
        ranges: list[dict[str, Any]] = []
        for label, min_value, max_value in self.PRICE_RANGES:
            if max_value is None:
                count = self.db.execute(
                    text("SELECT COUNT(*) FROM restaurant_info WHERE avg_price > :min_value"),
                    {"min_value": min_value},
                ).scalar_one()
            else:
                count = self.db.execute(
                    text(
                        """
                        SELECT COUNT(*)
                        FROM restaurant_info
                        WHERE avg_price > :min_value AND avg_price <= :max_value
                        """
                    ),
                    {"min_value": min_value, "max_value": max_value},
                ).scalar_one()
            ranges.append({"label": label, "count": int(count)})
        return {"ranges": ranges}

    def get_rating_distribution(self) -> dict[str, list[dict[str, Any]]]:
        ratings: list[dict[str, Any]] = []
        for label, min_value, max_value, include_min, include_max in self.RATING_RANGES:
            min_op = ">=" if include_min else ">"
            max_op = "<=" if include_max else "<"
            count = self.db.execute(
                text(
                    f"""
                    SELECT COUNT(*)
                    FROM restaurant_info
                    WHERE rating_overall {min_op} :min_value AND rating_overall {max_op} :max_value
                    """
                ),
                {"min_value": min_value, "max_value": max_value},
            ).scalar_one()
            ratings.append({"range": label, "count": int(count)})
        return {"ratings": ratings}

    def get_area_avg_price(self) -> dict[str, list[dict[str, Any]]]:
        rows = self.db.execute(
            text(
                """
                SELECT district AS name, ROUND(AVG(avg_price), 2) AS avg_price
                FROM restaurant_info
                WHERE district IS NOT NULL
                  AND district != ''
                  AND avg_price > 0
                GROUP BY district
                ORDER BY avg_price DESC, district ASC
                """
            )
        ).mappings().all()
        return {"districts": [dict(row) for row in rows]}

    def get_review_keywords(self, limit: int = 30) -> dict[str, list[dict[str, Any]]]:
        positive_rows = self.db.execute(
            text(
                """
                SELECT review_content
                FROM restaurant_review
                WHERE review_content IS NOT NULL
                  AND review_content != ''
                  AND (
                    sentiment_score > 0
                    AND rating_overall >= 4
                  )
                ORDER BY review_time DESC
                LIMIT 5000
                """
            )
        ).scalars().all()
        negative_rows = self.db.execute(
            text(
                """
                SELECT review_content
                FROM restaurant_review
                WHERE review_content IS NOT NULL
                  AND review_content != ''
                  AND (
                    sentiment_score < 0
                    AND rating_overall <= 2.5
                  )
                ORDER BY review_time DESC
                LIMIT 5000
                """
            )
        ).scalars().all()
        positive = self._extract_keywords(positive_rows, limit, "正面")
        negative = self._extract_keywords(negative_rows, limit, "负面")
        return {"positive": positive, "negative": negative}

    @classmethod
    @lru_cache(maxsize=1)
    def _sentiment_words(cls) -> dict[str, set[str]]:
        words: dict[str, set[str]] = {}
        for polarity, dimensions in SENTIMENT_DICT.items():
            merged: set[str] = set()
            for vocab in dimensions.values():
                merged.update(vocab)
            words[polarity] = merged
        return words

    def _extract_keywords(self, texts: list[str], limit: int, polarity: str) -> list[dict[str, Any]]:
        counter: Counter[str] = Counter()
        sentiment_words = self._sentiment_words()
        target_words = sentiment_words.get(polarity, set())
        stop_words = self.BASE_STOP_WORDS
        for text_item in texts:
            for token in jieba.lcut(text_item):
                token = token.strip()
                if not token or token in stop_words:
                    continue
                if not self.CHINESE_WORD_PATTERN.match(token):
                    continue
                counter[token] += 1

        prioritized = [(word, counter[word]) for word in target_words if counter[word] > 0]
        prioritized.sort(key=lambda item: item[1], reverse=True)
        selected = prioritized[:limit]
        if len(selected) < limit:
            selected_words = {word for word, _ in selected}
            for word, count in counter.most_common(limit * 3):
                if word in selected_words:
                    continue
                selected.append((word, count))
                selected_words.add(word)
                if len(selected) >= limit:
                    break
        return [{"word": word, "count": count} for word, count in selected]
