"""数据清洗日志 API"""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from ...database import get_db
from ...models.clean_log import CleanLog
from ...response import success

router = APIRouter(prefix="/clean-logs", tags=["数据清洗日志"])


@router.get("")
def list_logs(
    task_name: Optional[str] = Query(None, description="按任务名过滤"),
    level: Optional[str] = Query(None, description="日志级别：INFO/WARNING/ERROR"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    """获取数据清洗日志列表（按时间倒序）"""
    query = db.query(CleanLog)
    if task_name:
        query = query.filter(CleanLog.task_name == task_name)
    if level:
        query = query.filter(CleanLog.level == level.upper())

    total = query.count()
    items = (
        query.order_by(CleanLog.create_time.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return success(data={
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": [item.to_dict() for item in items],
    })


@router.get("/tasks")
def list_task_names(db: Session = Depends(get_db)):
    """获取所有任务名列表（用于筛选下拉）"""
    from sqlalchemy import distinct
    rows = db.query(distinct(CleanLog.task_name)).order_by(CleanLog.task_name.desc()).limit(50).all()
    return success(data={"tasks": [r[0] for r in rows]})


@router.delete("")
def clear_logs(
    task_name: Optional[str] = Query(None, description="清空指定任务的日志，为空则清空全部"),
    db: Session = Depends(get_db),
):
    """清空日志"""
    query = db.query(CleanLog)
    if task_name:
        query = query.filter(CleanLog.task_name == task_name)
    count = query.count()
    query.delete()
    db.commit()
    return success(data={"deleted": count})
