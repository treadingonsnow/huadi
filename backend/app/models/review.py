# 评分评论 ORM 模型
# 对应数据表：restaurant_review
# 字段：
# - review_id         VARCHAR(50) PK  评论唯一标识
# - restaurant_id     VARCHAR(50) FK  关联餐厅 ID
# - user_id           VARCHAR(50)     用户 ID（已脱敏）
# - rating_overall    DECIMAL(3,1)    综合评分 (1-5)
# - rating_taste      DECIMAL(3,1)    口味评分
# - rating_environment DECIMAL(3,1)   环境评分
# - rating_service    DECIMAL(3,1)    服务评分
# - review_content    TEXT            评论内容
# - review_time       DATETIME        评论时间
# - like_count        INT             点赞数
# - sentiment_score   DECIMAL(3,2)    情感得分 (-1 到 1)
# - data_source       VARCHAR(50)     数据来源
# - create_time       DATETIME        创建时间
# 索引：restaurant_id, review_time

from sqlalchemy import Column, String, Integer, DateTime, Text, ForeignKey, Index
from sqlalchemy.dialects.mysql import DECIMAL
from ..database import Base
from datetime import datetime


class Review(Base):
    """评论模型 - 对应 restaurant_review 表"""

    __tablename__ = "restaurant_review"

    # === 主键 ===
    review_id = Column(String(50), primary_key=True, index=True, comment="评论唯一标识")

    # === 外键 ===
    restaurant_id = Column(String(50), ForeignKey("restaurant_info.restaurant_id"), nullable=False, index=True,
                           comment="关联餐厅 ID")

    # === 用户信息 ===
    user_id = Column(String(50), nullable=True, comment="用户 ID（已脱敏）")

    # === 评分 ===
    rating_overall = Column(DECIMAL(3, 1), nullable=True, comment="综合评分 (1-5)")
    rating_taste = Column(DECIMAL(3, 1), nullable=True, comment="口味评分")
    rating_environment = Column(DECIMAL(3, 1), nullable=True, comment="环境评分")
    rating_service = Column(DECIMAL(3, 1), nullable=True, comment="服务评分")

    # === 评论内容 ===
    review_content = Column(Text, nullable=True, comment="评论内容")
    review_time = Column(DateTime, nullable=True, index=True, comment="评论时间")
    like_count = Column(Integer, nullable=True, comment="点赞数")
    sentiment_score = Column(DECIMAL(3, 2), nullable=True, comment="情感得分 (-1 到 1)")

    # === 数据来源 ===
    data_source = Column(String(50), nullable=True, comment="数据来源")
    create_time = Column(DateTime, nullable=True, default=datetime.utcnow, comment="创建时间")

    # === 索引 ===
    __table_args__ = (
        Index('idx_restaurant_time', 'restaurant_id', 'review_time'),
        {'comment': '餐厅评分评论表'}
    )

    def __repr__(self):
        return f"<Review(review_id={self.review_id}, restaurant_id={self.restaurant_id}, rating={self.rating_overall})>"
