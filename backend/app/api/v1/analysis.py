from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.deps import get_db
from app.services.analysis_service import AnalysisService


router = APIRouter(prefix="/analysis", tags=["analysis"])


def success(data: Any) -> dict[str, Any]:
    return {"code": 200, "message": "success", "data": data}


@router.get("/overview")
def get_overview(db: Session = Depends(get_db)) -> dict[str, Any]:
    try:
        service = AnalysisService(db)
        return success(service.get_overview())
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"获取概览数据失败: {exc}") from exc


@router.get("/area-distribution")
def get_area_distribution(db: Session = Depends(get_db)) -> dict[str, Any]:
    try:
        service = AnalysisService(db)
        return success(service.get_area_distribution())
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"获取区域分布失败: {exc}") from exc


@router.get("/cuisine-distribution")
def get_cuisine_distribution(db: Session = Depends(get_db)) -> dict[str, Any]:
    try:
        service = AnalysisService(db)
        return success(service.get_cuisine_distribution())
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"获取菜系分布失败: {exc}") from exc


@router.get("/price-distribution")
def get_price_distribution(db: Session = Depends(get_db)) -> dict[str, Any]:
    try:
        service = AnalysisService(db)
        return success(service.get_price_distribution())
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"获取价格分布失败: {exc}") from exc


@router.get("/rating-distribution")
def get_rating_distribution(db: Session = Depends(get_db)) -> dict[str, Any]:
    try:
        service = AnalysisService(db)
        return success(service.get_rating_distribution())
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"获取评分分布失败: {exc}") from exc


@router.get("/area-avg-price")
def get_area_avg_price(db: Session = Depends(get_db)) -> dict[str, Any]:
    try:
        service = AnalysisService(db)
        return success(service.get_area_avg_price())
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"获取各区均价失败: {exc}") from exc


@router.get("/review-keywords")
def get_review_keywords(limit: int = 30, db: Session = Depends(get_db)) -> dict[str, Any]:
    try:
        service = AnalysisService(db)
        return success(service.get_review_keywords(limit=limit))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"获取口碑关键词失败: {exc}") from exc
