# 餐厅相关 API 路由
# 功能：
# - GET  /search          多维度搜索
# - GET  /{restaurant_id} 餐厅详情
# - GET  /{restaurant_id}/reviews  餐厅评论列表
# - POST /favorites        收藏/取消收藏餐厅（需登录）
# - GET  /favorites        获取用户收藏列表（需登录）

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session
from sqlalchemy import and_, func, desc
from typing import Optional
from decimal import Decimal

# 相对导入
from ...database import get_db
from ...models.restaurant import Restaurant
from ...models.review import Review
from ...models.favorite import UserFavorite
from ...models.user import User
from ...core.deps import get_current_user
from ...core.security import verify_token
from ...response import success, error

router = APIRouter()


def _r_to_dict(r: Restaurant) -> dict:
    """将 Restaurant ORM 对象转换为前端期望的字段格式"""
    return {
        "id": r.restaurant_id,
        "name": r.restaurant_name,
        "address": r.address,
        "phone": r.phone,
        "business_hours": r.business_hours,
        "avg_price": float(r.avg_price) if r.avg_price is not None else 0,
        "rating": float(r.rating_overall) if r.rating_overall is not None else 0,
        "review_count": r.review_count or 0,
        "cuisine_type": r.cuisine_type,
        "district": r.district,
        "business_area": r.business_area,
        "latitude": float(r.latitude) if r.latitude is not None else None,
        "longitude": float(r.longitude) if r.longitude is not None else None,
        "data_source": r.data_source,
    }


# === 餐厅搜索 ===

@router.get("/search")
def search_restaurants(
        keyword: Optional[str] = Query(None, description="关键词（餐厅名/菜系/区域模糊匹配）"),
        district: Optional[str] = Query(None, description="行政区"),
        cuisine: Optional[str] = Query(None, alias="cuisine", description="菜系类型"),
        cuisine_type: Optional[str] = Query(None, description="菜系类型（兼容字段）"),
        price_min: Optional[Decimal] = Query(None, description="最低人均消费"),
        price_max: Optional[Decimal] = Query(None, description="最高人均消费"),
        rating_min: Optional[Decimal] = Query(None, description="最低评分"),
        sort_by: str = Query("default", description="排序：default/rating/price"),
        favorites_only: bool = Query(False, description="只看已收藏"),
        exclude_favorites: bool = Query(False, description="排除已收藏"),
        page: int = Query(1, ge=1, description="页码"),
        page_size: int = Query(20, ge=1, le=100, description="每页数量"),
        request: Request = None,
        db: Session = Depends(get_db)
):
    """餐厅搜索接口"""
    conditions = []

    # cuisine 和 cuisine_type 两个参数都支持（前端用 cuisine）
    cuisine_filter = cuisine or cuisine_type
    if keyword:
        conditions.append(Restaurant.restaurant_name.like(f"%{keyword}%"))
    if district:
        conditions.append(Restaurant.district.like(f"%{district}%"))
    if cuisine_filter:
        conditions.append(Restaurant.cuisine_type == cuisine_filter)
    if price_min is not None:
        conditions.append(Restaurant.avg_price >= price_min)
    if price_max is not None:
        conditions.append(Restaurant.avg_price <= price_max)
    if rating_min is not None:
        conditions.append(Restaurant.rating_overall >= rating_min)

    query = db.query(Restaurant)
    if conditions:
        query = query.filter(and_(*conditions))

    # 收藏筛选：从 Authorization header 解析用户（可选鉴权）
    if favorites_only or exclude_favorites:
        current_user_id = None
        auth_header = request.headers.get("authorization", "") if request else ""
        if auth_header.startswith("Bearer "):
            payload = verify_token(auth_header[7:])
            if payload:
                current_user_id = payload.get("sub")

        if current_user_id is not None:
            fav_ids = [
                row.restaurant_id
                for row in db.query(UserFavorite.restaurant_id).filter(
                    UserFavorite.user_id == int(current_user_id)
                ).all()
            ]
            if favorites_only:
                query = query.filter(Restaurant.restaurant_id.in_(fav_ids)) if fav_ids else query.filter(False)
            elif exclude_favorites:
                if fav_ids:
                    query = query.filter(Restaurant.restaurant_id.notin_(fav_ids))

    if sort_by == "rating":
        query = query.order_by(desc(Restaurant.rating_overall))
    elif sort_by == "price":
        query = query.order_by(Restaurant.avg_price)
    else:
        query = query.order_by(desc(Restaurant.rating_overall))

    total = query.count()
    offset = (page - 1) * page_size
    items = query.offset(offset).limit(page_size).all()

    return success(data={
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": [_r_to_dict(r) for r in items]
    })


# === 收藏/取消收藏餐厅（具体路径，放前面！）===

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



# === 获取用户收藏列表 ===

@router.get("/favorites")
def get_user_favorites(
        page: int = Query(default=1, ge=1, description="页码"),
        page_size: int = Query(default=20, ge=1, le=100, description="每页数量"),
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
                "restaurant": _r_to_dict(restaurant),
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

    return success(data=_r_to_dict(restaurant))


# === 餐厅评论列表（动态路径，放最后！）===

@router.get("/{restaurant_id}/reviews")
def get_restaurant_reviews(
        restaurant_id: str,
        page: int = Query(1, ge=1, description="页码"),
        page_size: int = Query(20, ge=1, le=100, description="每页数量"),
        sort_by: str = Query("time", description="排序方式：time/rating"),
        db: Session = Depends(get_db)
):
    """餐厅评论列表接口"""
    restaurant = db.query(Restaurant).filter(Restaurant.restaurant_id == restaurant_id).first()
    if not restaurant:
        return error(message="餐厅不存在", code=404)

    query = db.query(Review).filter(Review.restaurant_id == restaurant_id)

    if sort_by == "rating":
        query = query.order_by(desc(Review.rating_overall))
    else:
        query = query.order_by(desc(Review.review_time))

    total = query.count()
    offset = (page - 1) * page_size
    items = query.offset(offset).limit(page_size).all()

    def _review_to_dict(rv: Review) -> dict:
        return {
            "review_id": rv.review_id,
            "restaurant_id": rv.restaurant_id,
            "rating_overall": float(rv.rating_overall) if rv.rating_overall else None,
            "review_content": rv.review_content,
            "review_time": rv.review_time.isoformat() if rv.review_time else None,
            "sentiment_score": float(rv.sentiment_score) if rv.sentiment_score else None,
        }

    return success(data={
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": [_review_to_dict(rv) for rv in items]
    })
