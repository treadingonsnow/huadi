# 用户收藏 ORM 模型
# 对应数据表：user_favorites

# 用户收藏 ORM 模型
# 对应数据表：user_favorites

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, PrimaryKeyConstraint
from ..database import Base
from datetime import datetime


class UserFavorite(Base):
    """用户收藏模型 - 对应 user_favorites 表"""

    __tablename__ = "user_favorites"

    # === 联合主键 ===
    user_id = Column(Integer, ForeignKey("sys_user.user_id"), primary_key=True)
    restaurant_id = Column(String(50), ForeignKey("restaurant_info.restaurant_id"), primary_key=True)

    # === 其他字段 ===
    create_time = Column(DateTime, nullable=False, default=datetime.utcnow, comment="收藏时间")

    # === 模型配置 ===
    __table_args__ = {
        'comment': '用户收藏表'
    }

    def __repr__(self):
        return f"<UserFavorite(user_id={self.user_id}, restaurant_id={self.restaurant_id})>"
