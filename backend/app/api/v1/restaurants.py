# 餐厅相关 API 路由
# 功能：
# - GET  /search          多维度搜索
# - GET  /{restaurant_id} 餐厅详情
# - GET  /{restaurant_id}/reviews  餐厅评论列表
# - POST /favorites        收藏/取消收藏餐厅（需登录）
# - GET  /favorites        获取用户收藏列表（需登录）

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_, func, desc
from typing import Optional, List
from decimal import Decimal

# 相对导入
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
    """餐厅搜索接口"""
    conditions = []

    if keyword:
        conditions.append(Restaurant.restaurant_name.like(f"%{keyword}%"))
    if district:
        conditions.append(Restaurant.district.like(f"%{district}%"))
    if business_area:
        conditions.append(Restaurant.business_area.like(f"%{business_area}%"))
    if cuisine_type:
        conditions.append(Restaurant.cuisine_type == cuisine_type)
    if min_price is not None:
        conditions.append(Restaurant.avg_price >= min_price)
    if max_price is not None:
        conditions.append(Restaurant.avg_price <= max_price)

    query = db.query(Restaurant)
    if conditions:
        query = query.filter(and_(*conditions))

    if sort_by == "rating":
        query = query.outerjoin(Review).group_by(Restaurant.restaurant_id)
        query = query.order_by(desc(func.avg(Review.rating_overall)))
    elif sort_by == "price":
        query = query.order_by(Restaurant.avg_price)
    elif sort_by == "hot":
        query = query.outerjoin(Review).group_by(Restaurant.restaurant_id)
        query = query.order_by(desc(func.count(Review.review_id)))

    total = query.count()
    offset = (page - 1) * page_size
    items = query.offset(offset).limit(page_size).all()

    return success(data={
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": items
    })


# === 收藏/取消收藏餐厅（移到前面！）===

@router.post("/favorites")
def toggle_favorite(
        restaurant_id: str,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """收藏/取消收藏餐厅"""
    restaurant = db.query(Restaurant).filter(Restaurant.restaurant_id == restaurant_id).first()
    if not restaurant:
        return error(message="餐厅不存在", code=404)

    existing_favorite = db.query(UserFavorite).filter(
        UserFavorite.user_id == current_user.user_id,
        UserFavorite.restaurant_id == restaurant_id
    ).first()

    if existing_favorite:
        db.delete(existing_favorite)
        db.commit()
        return success(data={"action": "remove", "message": "已取消收藏"})
    else:
        new_favorite = UserFavorite(user_id=current_user.user_id, restaurant_id=restaurant_id)
        db.add(new_favorite)
        db.commit()
        return success(data={"action": "add", "message": "已收藏"})


# === 获取用户收藏列表（移到前面！）===

@router.get("/favorites")
def get_user_favorites(
        page: int = Query(1, ge=1, description="页码"),
        page_size: int = Query(20, ge=1, le=100, description="每页数量"),
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """获取当前用户收藏的餐厅列表"""
    query = db.query(UserFavorite).filter(UserFavorite.user_id == current_user.user_id)
    total = query.count()

    offset = (page - 1) * page_size
    favorites = query.offset(offset).limit(page_size).all()

    restaurant_ids = [fav.restaurant_id for fav in favorites]
    restaurants = db.query(Restaurant).filter(
        Restaurant.restaurant_id.in_(restaurant_ids)
    ).all() if restaurant_ids else []

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


# === 餐厅详情（动态路径，放最后！）===

@router.get("/{restaurant_id}")
def get_restaurant_detail(
        restaurant_id: str,
        db: Session = Depends(get_db)
):
    """餐厅详情接口"""
    restaurant = db.query(Restaurant).filter(Restaurant.restaurant_id == restaurant_id).first()

    if not restaurant:
        return error(message="餐厅不存在", code=404)

    avg_rating = db.query(func.avg(Review.rating_overall)).filter(
        Review.restaurant_id == restaurant_id
    ).scalar()

    review_count = db.query(func.count(Review.review_id)).filter(
        Review.restaurant_id == restaurant_id
    ).scalar()

    return success(data={
        "restaurant": restaurant,
        "avg_rating": float(avg_rating) if avg_rating else 0,
        "review_count": review_count or 0
    })


# === 餐厅评论列表（动态路径，放最后！）===

@router.get("/{restaurant_id}/reviews")
def get_restaurant_reviews(
        restaurant_id: str,
        page: int = Query(1, ge=1, description="页码"),
        page_size: int = Query(20, ge=1, le=100, description="每页数量"),
        min_rating: Optional[Decimal] = Query(None, description="最低评分"),
        sort_by: str = Query("time", description="排序方式：time/rating/like"),
        db: Session = Depends(get_db)
):
    """餐厅评论列表接口"""
    restaurant = db.query(Restaurant).filter(Restaurant.restaurant_id == restaurant_id).first()
    if not restaurant:
        return error(message="餐厅不存在", code=404)

    conditions = [Review.restaurant_id == restaurant_id]
    if min_rating is not None:
        conditions.append(Review.rating_overall >= min_rating)

    query = db.query(Review).filter(and_(*conditions))

    if sort_by == "rating":
        query = query.order_by(desc(Review.rating_overall))
    elif sort_by == "like":
        query = query.order_by(desc(Review.like_count))
    else:
        query = query.order_by(desc(Review.review_time))

    total = query.count()
    offset = (page - 1) * page_size
    items = query.offset(offset).limit(page_size).all()

    return success(data={
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": items
    })
