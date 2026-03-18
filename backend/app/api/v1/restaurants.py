# 餐厅相关 API 路由
# 功能：
# - GET  /search          多维度搜索（关键词、区域、商圈、菜系、价格区间、评分、场景）
#                          支持分页、排序（距离/评分/价格/热度）
# - GET  /{restaurant_id} 餐厅详情（基础信息、评分、菜品、评论列表）
# - GET  /{restaurant_id}/reviews  餐厅评论列表（分页、排序、筛选）
# - POST /favorites        收藏/取消收藏餐厅（需登录）
# - GET  /favorites        获取用户收藏列表（需登录）

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import and_, func, desc
from typing import Optional, List
from decimal import Decimal

# 相对导入（向上 3 级：api/v1 → api → app）
from ...database import get_db
from ...models.restaurant import Restaurant
from ...models.review import Review
from ...models.favorite import UserFavorite
from ...models.user import User
from ...core.deps import get_current_user
from ...response import success, error

router = APIRouter()


# === 餐厅搜索 ===

@router.get("/search")
def search_restaurants(
        keyword: Optional[str] = Query(None, description="关键词（餐厅名称）"),
        district: Optional[str] = Query(None, description="行政区"),
        business_area: Optional[str] = Query(None, description="商圈"),
        cuisine_type: Optional[str] = Query(None, description="菜系类型"),
        min_price: Optional[Decimal] = Query(None, description="最低人均消费"),
        max_price: Optional[Decimal] = Query(None, description="最高人均消费"),
        min_rating: Optional[Decimal] = Query(None, description="最低评分"),
        sort_by: str = Query("default", description="排序方式：default/distance/rating/price/hot"),
        page: int = Query(1, ge=1, description="页码"),
        page_size: int = Query(20, ge=1, le=100, description="每页数量"),
        db: Session = Depends(get_db)
):
    """
    餐厅搜索接口

    返回:
        {"code": 200, "message": "success", "data": {"total": 100, "page": 1, "page_size": 20, "items": [...]}}
    """
    # 构建查询条件
    conditions = []

    if keyword:
        conditions.append(Restaurant.restaurant_name.like(f"%{keyword}%"))
    if district:
        conditions.append(Restaurant.district == district)
    if business_area:
        conditions.append(Restaurant.business_area == business_area)
    if cuisine_type:
        conditions.append(Restaurant.cuisine_type == cuisine_type)
    if min_price is not None:
        conditions.append(Restaurant.avg_price >= min_price)
    if max_price is not None:
        conditions.append(Restaurant.avg_price <= max_price)

    # 基础查询
    query = db.query(Restaurant)
    if conditions:
        query = query.filter(and_(*conditions))

    # 排序
    if sort_by == "rating":
        # 需要关联评论表计算平均评分
        query = query.outerjoin(Review).group_by(Restaurant.restaurant_id)
        query = query.order_by(desc(func.avg(Review.rating_overall)))
    elif sort_by == "price":
        query = query.order_by(Restaurant.avg_price)
    elif sort_by == "hot":
        # 按评论数量排序（热度）
        query = query.outerjoin(Review).group_by(Restaurant.restaurant_id)
        query = query.order_by(desc(func.count(Review.review_id)))
    # default 不排序，按数据库默认顺序

    # 总数
    total = query.count()

    # 分页
    offset = (page - 1) * page_size
    items = query.offset(offset).limit(page_size).all()

    return success(data={
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": items
    })


# === 餐厅详情 ===

@router.get("/{restaurant_id}")
def get_restaurant_detail(
        restaurant_id: str,
        db: Session = Depends(get_db)
):
    """
    餐厅详情接口

    返回:
        {"code": 200, "message": "success", "data": {...}}
    """
    restaurant = db.query(Restaurant).filter(Restaurant.restaurant_id == restaurant_id).first()

    if not restaurant:
        return error(msg="餐厅不存在", code=404)

    # 获取平均评分
    avg_rating = db.query(func.avg(Review.rating_overall)).filter(
        Review.restaurant_id == restaurant_id
    ).scalar()

    # 获取评论数量
    review_count = db.query(func.count(Review.review_id)).filter(
        Review.restaurant_id == restaurant_id
    ).scalar()

    return success(data={
        "restaurant": restaurant,
        "avg_rating": float(avg_rating) if avg_rating else 0,
        "review_count": review_count or 0
    })


# === 餐厅评论列表 ===

@router.get("/{restaurant_id}/reviews")
def get_restaurant_reviews(
        restaurant_id: str,
        page: int = Query(1, ge=1, description="页码"),
        page_size: int = Query(20, ge=1, le=100, description="每页数量"),
        min_rating: Optional[Decimal] = Query(None, description="最低评分"),
        sort_by: str = Query("time", description="排序方式：time/rating/like"),
        db: Session = Depends(get_db)
):
    """
    餐厅评论列表接口

    返回:
        {"code": 200, "message": "success", "data": {"total": 100, "page": 1, "items": [...]}}
    """
    # 检查餐厅是否存在
    restaurant = db.query(Restaurant).filter(Restaurant.restaurant_id == restaurant_id).first()
    if not restaurant:
        return error(msg="餐厅不存在", code=404)

    # 构建查询条件
    conditions = [Review.restaurant_id == restaurant_id]
    if min_rating is not None:
        conditions.append(Review.rating_overall >= min_rating)

    # 基础查询
    query = db.query(Review).filter(and_(*conditions))

    # 排序
    if sort_by == "rating":
        query = query.order_by(desc(Review.rating_overall))
    elif sort_by == "like":
        query = query.order_by(desc(Review.like_count))
    else:  # time
        query = query.order_by(desc(Review.review_time))

    # 总数
    total = query.count()

    # 分页
    offset = (page - 1) * page_size
    items = query.offset(offset).limit(page_size).all()

    return success(data={
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": items
    })


# === 收藏/取消收藏餐厅 ===

@router.post("/favorites")
def toggle_favorite(
        restaurant_id: str,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """
    收藏/取消收藏餐厅

    需要：Authorization: Bearer <token>

    参数:
        restaurant_id: 餐厅 ID

    返回:
        {"code": 200, "message": "success", "data": {"action": "add/remove", "favorite_id": "xxx"}}
    """
    # 检查餐厅是否存在
    restaurant = db.query(Restaurant).filter(Restaurant.restaurant_id == restaurant_id).first()
    if not restaurant:
        return error(msg="餐厅不存在", code=404)

    # 检查是否已收藏
    existing_favorite = db.query(UserFavorite).filter(
        UserFavorite.user_id == current_user.user_id,
        UserFavorite.restaurant_id == restaurant_id
    ).first()

    if existing_favorite:
        # 取消收藏
        db.delete(existing_favorite)
        db.commit()
        return success(data={
            "action": "remove",
            "message": "已取消收藏"
        })
    else:
        # 添加收藏
        new_favorite = UserFavorite(
            user_id=current_user.user_id,
            restaurant_id=restaurant_id
        )
        db.add(new_favorite)
        db.commit()
        return success(data={
            "action": "add",
            "message": "已收藏"
        })


# === 获取用户收藏列表 ===

@router.get("/favorites")
def get_user_favorites(
        page: int = Query(1, ge=1, description="页码"),
        page_size: int = Query(20, ge=1, le=100, description="每页数量"),
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """
    获取当前用户收藏的餐厅列表

    需要：Authorization: Bearer <token>

    返回:
        {"code": 200, "message": "success", "data": {"total": 10, "page": 1, "items": [...]}}
    """
    # 查询收藏记录
    query = db.query(UserFavorite).filter(UserFavorite.user_id == current_user.user_id)
    total = query.count()

    # 分页
    offset = (page - 1) * page_size
    favorites = query.offset(offset).limit(page_size).all()

    # 获取餐厅详情
    restaurant_ids = [fav.restaurant_id for fav in favorites]
    restaurants = db.query(Restaurant).filter(
        Restaurant.restaurant_id.in_(restaurant_ids)
    ).all() if restaurant_ids else []

    # 构建返回数据
    items = []
    for fav in favorites:
        restaurant = next((r for r in restaurants if r.restaurant_id == fav.restaurant_id), None)
        if restaurant:
            items.append({
                "restaurant": restaurant,
                "favorite_time": fav.create_time.isoformat() if fav.create_time else None
            })

    return success(data={
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": items
    })
