from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd
from sqlalchemy import create_engine, text

from config.dictionaries.area_dict import BUSINESS_AREA_DICT
from config.dictionaries.cuisine_dict import CUISINE_DICT


COLUMN_MAPPING = {
    "restaurant_id": "restaurant_id",
    "id": "restaurant_id",
    "name": "restaurant_name",
    "restaurant_name": "restaurant_name",
    "餐厅名": "restaurant_name",
    "餐厅名称": "restaurant_name",
    "title": "restaurant_name",
    "address": "address",
    "地址": "address",
    "phone": "phone",
    "电话": "phone",
    "tel": "phone",
    "business_hours": "business_hours",
    "营业时间": "business_hours",
    "avg_price": "avg_price",
    "price": "avg_price",
    "人均": "avg_price",
    "人均消费": "avg_price",
    "rating_overall": "rating_overall",
    "rating": "rating_overall",
    "评分": "rating_overall",
    "review_count": "review_count",
    "reviews": "review_count",
    "评论数": "review_count",
    "cuisine_type": "cuisine_type",
    "cuisine": "cuisine_type",
    "菜系": "cuisine_type",
    "district": "district",
    "区域": "district",
    "行政区": "district",
    "business_area": "business_area",
    "商圈": "business_area",
    "latitude": "latitude",
    "lat": "latitude",
    "纬度": "latitude",
    "longitude": "longitude",
    "lng": "longitude",
    "经度": "longitude",
}

DISTRICTS = set(BUSINESS_AREA_DICT.keys())


def load_env_file() -> None:
    env_path = Path(__file__).resolve().parents[1] / ".env"
    if not env_path.exists():
        return
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip("'").strip('"')
        os.environ.setdefault(key, value)


def build_db_url() -> str:
    load_env_file()
    host = os.getenv("MYSQL_HOST", "127.0.0.1")
    port = os.getenv("MYSQL_PORT", "3306")
    user = os.getenv("MYSQL_USER", "root")
    password = os.getenv("MYSQL_PASSWORD", "")
    database = os.getenv("MYSQL_DATABASE", "shanghai_food")
    return f"mysql+pymysql://{user}:{password}@{host}:{port}/{database}?charset=utf8mb4"


def read_dataset(file_path: Path) -> pd.DataFrame:
    suffix = file_path.suffix.lower()
    if suffix == ".csv":
        return pd.read_csv(file_path)
    if suffix == ".json":
        with file_path.open("r", encoding="utf-8") as f:
            payload = json.load(f)
        if isinstance(payload, dict):
            for key in ("data", "items", "restaurants", "records"):
                if key in payload and isinstance(payload[key], list):
                    return pd.DataFrame(payload[key])
            return pd.DataFrame([payload])
        return pd.DataFrame(payload)
    if suffix in {".xlsx", ".xls"}:
        return pd.read_excel(file_path)
    raise ValueError(f"不支持的数据格式: {file_path.suffix}")


def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    rename_map: dict[str, str] = {}
    for col in df.columns:
        normalized = str(col).strip()
        normalized = COLUMN_MAPPING.get(normalized, COLUMN_MAPPING.get(normalized.lower(), normalized))
        rename_map[col] = normalized
    result = df.rename(columns=rename_map).copy()
    if "restaurant_name" not in result.columns:
        raise ValueError("数据集中缺少餐厅名称字段")
    if "address" not in result.columns:
        result["address"] = ""
    return result


def desensitize_phone(phone: Any) -> str | None:
    if phone is None or (isinstance(phone, float) and pd.isna(phone)):
        return None
    value = re.sub(r"\D", "", str(phone))
    if len(value) == 11:
        return f"{value[:3]}****{value[-4:]}"
    if len(value) >= 7:
        return f"{value[:3]}****{value[-4:]}"
    return None


def normalize_district(raw: Any, business_area: Any, address: Any) -> str | None:
    candidates = [str(raw or "").strip(), str(business_area or "").strip(), str(address or "").strip()]
    for text_item in candidates:
        if not text_item:
            continue
        for district in DISTRICTS:
            if district in text_item:
                return district
        for district, areas in BUSINESS_AREA_DICT.items():
            for area in areas:
                if area and area in text_item:
                    return district
    return None


def normalize_cuisine(raw: Any) -> str:
    value = str(raw or "").strip()
    if not value:
        return "其他"
    lowered = value.lower()
    for standard, synonyms in CUISINE_DICT.items():
        for term in synonyms:
            if term.lower() in lowered:
                return standard
    return value if len(value) <= 50 else value[:50]


def parse_float(raw: Any, default: float = 0.0) -> float:
    if raw is None or (isinstance(raw, float) and pd.isna(raw)):
        return default
    text_value = str(raw).strip()
    if not text_value:
        return default
    match = re.search(r"-?\d+(\.\d+)?", text_value)
    if not match:
        return default
    return float(match.group())


def parse_int(raw: Any, default: int = 0) -> int:
    return int(round(parse_float(raw, default)))


def ensure_restaurant_id(name: str, address: str, source: str) -> str:
    seed = f"{source}|{name}|{address}"
    digest = hashlib.md5(seed.encode("utf-8")).hexdigest()[:20]
    return f"ds_{digest}"


def transform(df: pd.DataFrame, source: str) -> pd.DataFrame:
    now = datetime.now().replace(microsecond=0)
    data = normalize_columns(df)
    for field in (
        "restaurant_id",
        "phone",
        "business_hours",
        "avg_price",
        "rating_overall",
        "review_count",
        "cuisine_type",
        "district",
        "business_area",
        "latitude",
        "longitude",
    ):
        if field not in data.columns:
            data[field] = None

    data["restaurant_name"] = data["restaurant_name"].astype(str).str.strip()
    data["address"] = data["address"].astype(str).str.strip()
    data = data[(data["restaurant_name"] != "") & (data["restaurant_name"] != "nan")]
    data = data.drop_duplicates(subset=["restaurant_name", "address"], keep="first")

    data["phone"] = data["phone"].apply(desensitize_phone)
    data["business_hours"] = data["business_hours"].astype(str).str.strip()
    data["avg_price"] = data["avg_price"].apply(parse_float)
    data["rating_overall"] = data["rating_overall"].apply(parse_float)
    data["review_count"] = data["review_count"].apply(parse_int)
    data["cuisine_type"] = data["cuisine_type"].apply(normalize_cuisine)
    data["district"] = data.apply(
        lambda row: normalize_district(row.get("district"), row.get("business_area"), row.get("address")),
        axis=1,
    )
    data["business_area"] = data["business_area"].astype(str).str.strip().replace({"nan": None, "": None})
    data["latitude"] = data["latitude"].apply(lambda x: parse_float(x, 0.0) or None)
    data["longitude"] = data["longitude"].apply(lambda x: parse_float(x, 0.0) or None)
    data["data_source"] = source
    data["crawl_time"] = now

    data["restaurant_id"] = data.apply(
        lambda row: str(row.get("restaurant_id")).strip()
        if row.get("restaurant_id") and str(row.get("restaurant_id")).strip().lower() not in {"nan", ""}
        else ensure_restaurant_id(row["restaurant_name"], row["address"], source),
        axis=1,
    )

    columns = [
        "restaurant_id",
        "restaurant_name",
        "address",
        "phone",
        "business_hours",
        "avg_price",
        "rating_overall",
        "review_count",
        "cuisine_type",
        "district",
        "business_area",
        "latitude",
        "longitude",
        "data_source",
        "crawl_time",
    ]
    return data[columns].copy()


def insert_records(df: pd.DataFrame, db_url: str) -> tuple[int, int]:
    engine = create_engine(db_url, future=True)
    inserted = 0
    updated = 0
    sql = text(
        """
        INSERT INTO restaurant_info (
            restaurant_id, restaurant_name, address, phone, business_hours,
            avg_price, rating_overall, review_count, cuisine_type, district,
            business_area, latitude, longitude, data_source, crawl_time
        ) VALUES (
            :restaurant_id, :restaurant_name, :address, :phone, :business_hours,
            :avg_price, :rating_overall, :review_count, :cuisine_type, :district,
            :business_area, :latitude, :longitude, :data_source, :crawl_time
        )
        ON DUPLICATE KEY UPDATE
            restaurant_name = VALUES(restaurant_name),
            address = VALUES(address),
            phone = VALUES(phone),
            business_hours = VALUES(business_hours),
            avg_price = VALUES(avg_price),
            rating_overall = VALUES(rating_overall),
            review_count = VALUES(review_count),
            cuisine_type = VALUES(cuisine_type),
            district = VALUES(district),
            business_area = VALUES(business_area),
            latitude = VALUES(latitude),
            longitude = VALUES(longitude),
            data_source = VALUES(data_source),
            crawl_time = VALUES(crawl_time)
        """
    )
    records = df.to_dict(orient="records")
    with engine.begin() as conn:
        before = conn.execute(text("SELECT COUNT(*) FROM restaurant_info")).scalar_one()
        conn.execute(sql, records)
        after = conn.execute(text("SELECT COUNT(*) FROM restaurant_info")).scalar_one()
    inserted = max(int(after - before), 0)
    updated = max(len(records) - inserted, 0)
    return inserted, updated


def main() -> None:
    parser = argparse.ArgumentParser(description="导入公开数据集到 restaurant_info 表")
    parser.add_argument("--file", required=True, help="数据文件路径，支持 CSV/JSON/XLSX/XLS")
    parser.add_argument("--source", default="dataset", help="数据来源标识")
    args = parser.parse_args()

    file_path = Path(args.file).resolve()
    if not file_path.exists():
        raise FileNotFoundError(f"文件不存在: {file_path}")

    raw_df = read_dataset(file_path)
    if raw_df.empty:
        raise ValueError("数据集为空")

    cleaned_df = transform(raw_df, args.source)
    if cleaned_df.empty:
        raise ValueError("清洗后无可导入数据")

    db_url = build_db_url()
    inserted, updated = insert_records(cleaned_df, db_url)
    print(f"导入完成，总记录 {len(cleaned_df)} 条，新增 {inserted} 条，更新 {updated} 条")


if __name__ == "__main__":
    main()
