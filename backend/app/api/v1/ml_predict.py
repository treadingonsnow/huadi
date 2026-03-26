"""机器学习预测 API"""
from __future__ import annotations

from pydantic import BaseModel
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ...database import get_db
from ...response import success, error
from ...services.ml_service import MLService

router = APIRouter(prefix="/ml", tags=["机器学习预测"])


class PredictRequest(BaseModel):
    cuisine_type: str
    district: str
    avg_price: float


@router.post("/train")
def train_model(db: Session = Depends(get_db)):
    """从数据库数据训练评分预测模型"""
    svc = MLService(db)
    try:
        result = svc.train()
    except ValueError as exc:
        return error(message=f"训练失败：{exc}", code=422)
    except Exception as exc:
        return error(message=f"训练失败：{exc}", code=500)
    return success(
        data=result,
        message=f"训练成功：样本 {result.get('sample_count', 0)} 条，R²={result.get('r2')}, RMSE={result.get('rmse')}",
    )


@router.get("/info")
def model_info(db: Session = Depends(get_db)):
    """获取当前模型信息（精度、样本量等）"""
    svc = MLService(db)
    return success(data=svc.get_info())


@router.post("/predict")
def predict_rating(req: PredictRequest, db: Session = Depends(get_db)):
    """预测餐厅评分"""
    svc = MLService(db)
    try:
        result = svc.predict(req.cuisine_type, req.district, req.avg_price)
    except ValueError as exc:
        return error(message=str(exc), code=422)
    except Exception as exc:
        return error(message=f"预测失败：{exc}", code=500)
    return success(data=result)
