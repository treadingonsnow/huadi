"""机器学习预测服务
基于数据库中的餐厅数据训练随机森林回归模型，预测餐厅评分
"""
from __future__ import annotations

import os
import pickle
from typing import Any

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sqlalchemy import text
from sqlalchemy.orm import Session

MODEL_PATH = "/tmp/shanghai_food_rf_model.pkl"


class MLService:
    def __init__(self, db: Session) -> None:
        self.db = db

    # ──────────────────────────────────────────────
    # 训练
    # ──────────────────────────────────────────────
    def train(self) -> dict[str, Any]:
        rows = self.db.execute(
            text("""
                SELECT cuisine_type, district, avg_price, rating_overall, review_count
                FROM restaurant_info
                WHERE avg_price > 0
                  AND rating_overall > 0
                  AND cuisine_type IS NOT NULL AND cuisine_type != ''
                  AND district     IS NOT NULL AND district     != ''
            """)
        ).mappings().all()

        if len(rows) < 20:
            raise ValueError(f"数据量不足（当前 {len(rows)} 条），需要至少 20 条有效数据才能训练模型")

        df = pd.DataFrame([dict(r) for r in rows])

        le_cuisine = LabelEncoder()
        le_district = LabelEncoder()
        df["cuisine_enc"] = le_cuisine.fit_transform(df["cuisine_type"])
        df["district_enc"] = le_district.fit_transform(df["district"])

        feature_cols = ["cuisine_enc", "district_enc", "avg_price"]
        X = df[feature_cols].fillna(0).astype(float)
        y = df["rating_overall"].astype(float)

        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )

        model = RandomForestRegressor(n_estimators=100, random_state=42, n_jobs=-1)
        model.fit(X_train, y_train)

        y_pred = model.predict(X_test)
        r2 = float(r2_score(y_test, y_pred))
        rmse = float(mean_squared_error(y_test, y_pred) ** 0.5)

        # 特征重要性
        importances = {
            "菜系类型": round(float(model.feature_importances_[0]), 4),
            "所属区域": round(float(model.feature_importances_[1]), 4),
            "人均消费": round(float(model.feature_importances_[2]), 4),
        }

        model_data = {
            "model": model,
            "le_cuisine": le_cuisine,
            "le_district": le_district,
            "cuisine_classes": list(le_cuisine.classes_),
            "district_classes": list(le_district.classes_),
            "r2": round(r2, 4),
            "rmse": round(rmse, 4),
            "sample_count": len(df),
            "feature_importances": importances,
        }
        with open(MODEL_PATH, "wb") as f:
            pickle.dump(model_data, f)

        return {
            "status": "success",
            "r2": round(r2, 4),
            "rmse": round(rmse, 4),
            "sample_count": len(df),
            "feature_importances": importances,
        }

    # ──────────────────────────────────────────────
    # 预测
    # ──────────────────────────────────────────────
    def predict(self, cuisine_type: str, district: str, avg_price: float) -> dict[str, Any]:
        if not os.path.exists(MODEL_PATH):
            # 自动触发训练
            self.train()

        with open(MODEL_PATH, "rb") as f:
            model_data = pickle.load(f)

        model: RandomForestRegressor = model_data["model"]
        le_cuisine: LabelEncoder = model_data["le_cuisine"]
        le_district: LabelEncoder = model_data["le_district"]

        # 处理未见标签
        try:
            cuisine_enc = int(le_cuisine.transform([cuisine_type])[0])
        except ValueError:
            cuisine_enc = 0

        try:
            district_enc = int(le_district.transform([district])[0])
        except ValueError:
            district_enc = 0

        X = np.array([[cuisine_enc, district_enc, float(avg_price)]])
        raw_pred = float(model.predict(X)[0])
        predicted_rating = round(min(5.0, max(1.0, raw_pred)), 1)

        # 获取所有树的预测，计算置信区间（标准差）
        tree_preds = np.array([t.predict(X)[0] for t in model.estimators_])
        std = float(np.std(tree_preds))
        confidence_low = round(max(1.0, predicted_rating - std), 1)
        confidence_high = round(min(5.0, predicted_rating + std), 1)

        return {
            "predicted_rating": predicted_rating,
            "confidence_low": confidence_low,
            "confidence_high": confidence_high,
            "model_r2": model_data["r2"],
            "model_rmse": model_data["rmse"],
            "sample_count": model_data["sample_count"],
            "available_cuisines": model_data["cuisine_classes"],
            "available_districts": model_data["district_classes"],
        }

    # ──────────────────────────────────────────────
    # 模型信息
    # ──────────────────────────────────────────────
    def get_info(self) -> dict[str, Any]:
        if not os.path.exists(MODEL_PATH):
            return {
                "trained": False,
                "message": "模型尚未训练，请先点击「训练模型」",
            }
        with open(MODEL_PATH, "rb") as f:
            model_data = pickle.load(f)
        return {
            "trained": True,
            "r2": model_data["r2"],
            "rmse": model_data["rmse"],
            "sample_count": model_data["sample_count"],
            "feature_importances": model_data.get("feature_importances", {}),
            "available_cuisines": model_data["cuisine_classes"],
            "available_districts": model_data["district_classes"],
        }
