"""数据导入服务
支持三种目标存储：MySQL、HDFS（WebHDFS）、Hive（HiveServer2）
每个清洗步骤写入 clean_log 表供前端实时查看
"""
from __future__ import annotations

import hashlib
import io
import re
import uuid
from datetime import datetime
from typing import Any

import pandas as pd
from sqlalchemy.orm import Session
from sqlalchemy import text

from ..models.clean_log import CleanLog
from ..models.restaurant import Restaurant

# 上海 16 区标准名
SHANGHAI_DISTRICTS = {
    "黄浦", "徐汇", "长宁", "静安", "普陀", "虹口", "杨浦",
    "闵行", "宝山", "嘉定", "浦东", "金山", "松江", "青浦", "奉贤", "崇明",
}
DISTRICT_SUFFIX_MAP = {
    "浦东新区": "浦东新区", "浦东": "浦东新区",
    "黄浦区": "黄浦区",  "黄浦": "黄浦区",
    "徐汇区": "徐汇区",  "徐汇": "徐汇区",
    "长宁区": "长宁区",  "长宁": "长宁区",
    "静安区": "静安区",  "静安": "静安区",
    "普陀区": "普陀区",  "普陀": "普陀区",
    "虹口区": "虹口区",  "虹口": "虹口区",
    "杨浦区": "杨浦区",  "杨浦": "杨浦区",
    "闵行区": "闵行区",  "闵行": "闵行区",
    "宝山区": "宝山区",  "宝山": "宝山区",
    "嘉定区": "嘉定区",  "嘉定": "嘉定区",
    "金山区": "金山区",  "金山": "金山区",
    "松江区": "松江区",  "松江": "松江区",
    "青浦区": "青浦区",  "青浦": "青浦区",
    "奉贤区": "奉贤区",  "奉贤": "奉贤区",
    "崇明区": "崇明区",  "崇明": "崇明区",
}

COLUMN_ALIASES = {
    "id": "restaurant_id", "name": "restaurant_name",
    "餐厅名": "restaurant_name", "餐厅名称": "restaurant_name", "title": "restaurant_name",
    "address": "address", "地址": "address",
    "phone": "phone", "电话": "phone", "tel": "phone",
    "avg_price": "avg_price", "price": "avg_price", "人均": "avg_price", "人均消费": "avg_price",
    "rating_overall": "rating_overall", "rating": "rating_overall", "评分": "rating_overall",
    "review_count": "review_count", "reviews": "review_count", "评论数": "review_count",
    "cuisine_type": "cuisine_type", "cuisine": "cuisine_type", "菜系": "cuisine_type",
    "district": "district", "区域": "district", "行政区": "district",
    "business_area": "business_area", "商圈": "business_area",
    "latitude": "latitude", "lat": "latitude", "纬度": "latitude",
    "longitude": "longitude", "lng": "longitude", "经度": "longitude",
}


class ImportService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self._task_name = ""

    def _log(self, stage: str, message: str, level: str = "INFO", record_count: int | None = None) -> None:
        entry = CleanLog(
            task_name=self._task_name,
            stage=stage,
            level=level,
            message=message,
            record_count=record_count,
        )
        self.db.add(entry)
        self.db.commit()

    # ──────────────────────────────────────────────
    # 公共：解析文件 → DataFrame
    # ──────────────────────────────────────────────
    def _parse_file(self, file_bytes: bytes, filename: str) -> pd.DataFrame:
        ext = filename.rsplit(".", 1)[-1].lower()
        if ext == "csv":
            df = pd.read_csv(io.BytesIO(file_bytes), encoding="utf-8-sig")
        elif ext in ("xls", "xlsx"):
            df = pd.read_excel(io.BytesIO(file_bytes))
        elif ext == "json":
            df = pd.read_json(io.BytesIO(file_bytes))
        else:
            raise ValueError(f"不支持的文件格式：{ext}，请上传 CSV/JSON/Excel 文件")
        return df

    # ──────────────────────────────────────────────
    # 公共：清洗 DataFrame → 标准化字段
    # ──────────────────────────────────────────────
    def _clean(self, df: pd.DataFrame) -> pd.DataFrame:
        raw_count = len(df)
        self._log("load", f"文件加载完成，共 {raw_count} 条原始记录", record_count=raw_count)

        # 1. 字段名映射
        df.columns = [COLUMN_ALIASES.get(c.strip(), c.strip()) for c in df.columns]
        if "restaurant_name" not in df.columns:
            raise ValueError("文件缺少餐厅名称字段（name / restaurant_name / 餐厅名称）")

        # 2. 生成 restaurant_id（若缺失）
        if "restaurant_id" not in df.columns:
            df["restaurant_id"] = df["restaurant_name"].apply(
                lambda n: hashlib.md5(str(n).encode()).hexdigest()[:16]
            )

        # 3. 去重（按 restaurant_id）
        before_dedup = len(df)
        df = df.drop_duplicates(subset=["restaurant_id"])
        dup_count = before_dedup - len(df)
        self._log("dedup", f"去重完成，删除 {dup_count} 条重复记录，剩余 {len(df)} 条",
                  record_count=dup_count)

        # 4. 标准化区域名
        if "district" in df.columns:
            df["district"] = df["district"].apply(self._normalize_district)
            invalid_dist = df["district"].isna().sum()
            if invalid_dist:
                self._log("normalize", f"区域标准化：{invalid_dist} 条记录区域无法识别，已清空",
                          level="WARNING", record_count=int(invalid_dist))
            else:
                self._log("normalize", f"区域标准化完成，共 {len(df)} 条记录",
                          record_count=len(df))

        # 5. 脱敏手机号
        if "phone" in df.columns:
            df["phone"] = df["phone"].apply(self._mask_phone)
            self._log("normalize", f"手机号脱敏完成", record_count=len(df))

        # 6. 数值字段清洗
        for col in ("avg_price", "rating_overall", "review_count", "latitude", "longitude"):
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")
        df["avg_price"] = df.get("avg_price", pd.Series(0)).fillna(0)
        df["rating_overall"] = df.get("rating_overall", pd.Series(0)).fillna(0)
        df["review_count"] = df.get("review_count", pd.Series(0)).fillna(0).astype(int)

        # 7. 删除餐厅名为空的行
        before_validate = len(df)
        df = df[df["restaurant_name"].notna() & (df["restaurant_name"].astype(str).str.strip() != "")]
        dropped = before_validate - len(df)
        if dropped:
            self._log("validate", f"删除餐厅名为空的记录 {dropped} 条",
                      level="WARNING", record_count=dropped)

        df["data_source"] = df.get("data_source", pd.Series("import")).fillna("import")
        df["crawl_time"] = datetime.utcnow()

        self._log("validate", f"数据清洗完成，最终有效记录 {len(df)} 条", record_count=len(df))
        return df

    @staticmethod
    def _normalize_district(val: Any) -> str | None:
        if pd.isna(val):
            return None
        s = str(val).strip()
        return DISTRICT_SUFFIX_MAP.get(s, None)

    @staticmethod
    def _mask_phone(val: Any) -> str | None:
        if pd.isna(val):
            return None
        s = re.sub(r"\D", "", str(val))
        if len(s) == 11:
            return s[:3] + "****" + s[7:]
        return str(val)

    # ──────────────────────────────────────────────
    # 目标：MySQL
    # ──────────────────────────────────────────────
    def import_to_mysql(self, file_bytes: bytes, filename: str, task_name: str) -> dict:
        self._task_name = task_name
        self._log("load", f"开始导入任务：{task_name}，目标：MySQL")
        df = self._parse_file(file_bytes, filename)
        df = self._clean(df)

        TARGET_COLS = [
            "restaurant_id", "restaurant_name", "address", "phone", "business_hours",
            "avg_price", "rating_overall", "review_count", "cuisine_type",
            "district", "business_area", "latitude", "longitude", "data_source", "crawl_time",
        ]
        insert_df = df[[c for c in TARGET_COLS if c in df.columns]].copy()

        inserted = 0
        skipped = 0
        for _, row in insert_df.iterrows():
            exists = self.db.execute(
                text("SELECT 1 FROM restaurant_info WHERE restaurant_id = :rid LIMIT 1"),
                {"rid": row["restaurant_id"]},
            ).fetchone()
            if exists:
                skipped += 1
                continue
            self.db.execute(
                text("""
                    INSERT INTO restaurant_info
                    (restaurant_id, restaurant_name, address, phone, business_hours,
                     avg_price, rating_overall, review_count, cuisine_type,
                     district, business_area, latitude, longitude, data_source, crawl_time)
                    VALUES
                    (:restaurant_id, :restaurant_name, :address, :phone, :business_hours,
                     :avg_price, :rating_overall, :review_count, :cuisine_type,
                     :district, :business_area, :latitude, :longitude, :data_source, :crawl_time)
                """),
                {c: (None if pd.isna(row.get(c)) else row.get(c)) for c in TARGET_COLS},
            )
            inserted += 1
            if inserted % 100 == 0:
                self.db.commit()
                self._log("insert", f"已写入 {inserted} 条…", record_count=inserted)

        self.db.commit()
        self._log("insert", f"MySQL 写入完成：新增 {inserted} 条，跳过已存在 {skipped} 条",
                  record_count=inserted)
        return {"destination": "mysql", "inserted": inserted, "skipped": skipped, "total": len(df)}

    # ──────────────────────────────────────────────
    # 目标：HDFS（WebHDFS REST API）
    # ──────────────────────────────────────────────
    def import_to_hdfs(
        self,
        file_bytes: bytes,
        filename: str,
        task_name: str,
        hdfs_host: str,
        hdfs_port: int = 9870,
        hdfs_path: str = "/user/hadoop/restaurant",
        hdfs_user: str = "hadoop",
    ) -> dict:
        import requests as req_lib

        self._task_name = task_name
        self._log("load", f"开始导入任务：{task_name}，目标：HDFS {hdfs_host}:{hdfs_port}")
        df = self._parse_file(file_bytes, filename)
        df = self._clean(df)

        csv_bytes = df.to_csv(index=False).encode("utf-8")
        remote_path = f"{hdfs_path.rstrip('/')}/{filename}"
        create_url = (
            f"http://{hdfs_host}:{hdfs_port}/webhdfs/v1{remote_path}"
            f"?op=CREATE&user.name={hdfs_user}&overwrite=true"
        )

        self._log("hdfs", f"正在上传至 HDFS：{remote_path}")
        try:
            # Step 1: 获取重定向 URL
            resp = req_lib.put(create_url, allow_redirects=False, timeout=10)
            if resp.status_code != 307:
                raise RuntimeError(f"WebHDFS CREATE 返回 {resp.status_code}：{resp.text[:200]}")
            upload_url = resp.headers["Location"]
            # Step 2: 实际上传
            upload_resp = req_lib.put(upload_url, data=csv_bytes, timeout=60)
            if upload_resp.status_code not in (200, 201):
                raise RuntimeError(f"WebHDFS 上传失败 {upload_resp.status_code}：{upload_resp.text[:200]}")
        except Exception as exc:
            self._log("hdfs", f"HDFS 上传失败：{exc}", level="ERROR")
            raise

        self._log("hdfs", f"HDFS 上传成功，路径：{remote_path}，共 {len(df)} 条记录",
                  record_count=len(df))
        return {
            "destination": "hdfs",
            "hdfs_path": remote_path,
            "rows": len(df),
        }

    # ──────────────────────────────────────────────
    # 目标：Hive（先上传 HDFS，再 LOAD DATA INPATH）
    # ──────────────────────────────────────────────
    def import_to_hive(
        self,
        file_bytes: bytes,
        filename: str,
        task_name: str,
        hdfs_host: str,
        hdfs_port: int = 9870,
        hdfs_path: str = "/user/hadoop/restaurant",
        hdfs_user: str = "hadoop",
        hive_host: str = "localhost",
        hive_port: int = 10000,
        hive_db: str = "default",
        hive_table: str = "restaurant_info",
    ) -> dict:
        self._task_name = task_name

        # Step 1: 上传到 HDFS
        hdfs_result = self.import_to_hdfs(
            file_bytes, filename, task_name,
            hdfs_host, hdfs_port, hdfs_path, hdfs_user,
        )
        remote_path = hdfs_result["hdfs_path"]

        # Step 2: 通过 HiveServer2 加载
        self._log("hive", f"正在连接 HiveServer2 {hive_host}:{hive_port}")
        try:
            from pyhive import hive as pyhive_conn
            conn = pyhive_conn.Connection(host=hive_host, port=hive_port, username=hdfs_user)
            cursor = conn.cursor()
            cursor.execute(f"""
                CREATE TABLE IF NOT EXISTS `{hive_db}`.`{hive_table}` (
                    restaurant_id   STRING,
                    restaurant_name STRING,
                    address         STRING,
                    phone           STRING,
                    avg_price       DOUBLE,
                    rating_overall  DOUBLE,
                    review_count    INT,
                    cuisine_type    STRING,
                    district        STRING,
                    business_area   STRING,
                    latitude        DOUBLE,
                    longitude       DOUBLE,
                    data_source     STRING
                ) ROW FORMAT DELIMITED FIELDS TERMINATED BY ','
                STORED AS TEXTFILE
                TBLPROPERTIES ('skip.header.line.count'='1')
            """)
            cursor.execute(
                f"LOAD DATA INPATH '{remote_path}' OVERWRITE INTO TABLE `{hive_db}`.`{hive_table}`"
            )
            cursor.close()
            conn.close()
        except ImportError:
            self._log("hive", "pyhive 未安装，跳过 Hive 加载步骤。手动执行以下命令：\n"
                      f"LOAD DATA INPATH '{remote_path}' INTO TABLE {hive_db}.{hive_table};",
                      level="WARNING")
        except Exception as exc:
            self._log("hive", f"Hive 加载失败：{exc}", level="ERROR")
            raise

        self._log("hive", f"Hive 表 {hive_db}.{hive_table} 加载完成，数据来自 {remote_path}",
                  record_count=hdfs_result["rows"])
        return {
            "destination": "hive",
            "hdfs_path": remote_path,
            "hive_table": f"{hive_db}.{hive_table}",
            "rows": hdfs_result["rows"],
        }
