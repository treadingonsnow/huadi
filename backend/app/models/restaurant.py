# 餐厅信息 ORM 模型
# 对应数据表：restaurant_info
# 字段：
# - restaurant_id   VARCHAR(50) PK  餐厅唯一标识
# - restaurant_name VARCHAR(200)    餐厅名称
# - address         VARCHAR(500)    餐厅地址
# - phone           VARCHAR(20)     联系电话（已脱敏）
# - business_hours  VARCHAR(100)    营业时间
# - avg_price       DECIMAL(10,2)   人均消费（元）
# - cuisine_type    VARCHAR(50)     菜系类型
# - district        VARCHAR(50)     所属行政区
# - business_area   VARCHAR(100)    所属商圈
# - latitude        DECIMAL(10,6)   纬度
# - longitude       DECIMAL(10,6)   经度
# - subway_distance INT             地铁距离（米）
# - data_source     VARCHAR(50)     数据来源
# - crawl_time      DATETIME        采集时间
# - create_time     DATETIME        创建时间
# - update_time     DATETIME        更新时间
# 索引：district, business_area, cuisine_type, (latitude, longitude)
# 餐厅信息 ORM 模型
# 对应数据表：restaurant_info

from sqlalchemy import Column, String, Integer, DateTime, Index, Numeric
from sqlalchemy.dialects.mysql import DECIMAL
from sqlalchemy.orm import relationship
from ..database import Base
from datetime import datetime


class Restaurant(Base):
    """餐厅模型 - 对应 restaurant_info 表"""

    __tablename__ = "restaurant_info"

    # === 主键 ===
    restaurant_id = Column(String(50), primary_key=True, index=True, comment="餐厅唯一标识")

    # === 基本信息 ===
    restaurant_name = Column(String(200), nullable=False, index=True, comment="餐厅名称")
    address = Column(String(500), nullable=True, comment="餐厅地址")
    phone = Column(String(20), nullable=True, comment="联系电话（已脱敏）")
    business_hours = Column(String(100), nullable=True, comment="营业时间")

    # === 消费信息 ===
    avg_price = Column(DECIMAL(10, 2), nullable=True, comment="人均消费（元）")
    cuisine_type = Column(String(50), nullable=True, index=True, comment="菜系类型")
    district = Column(String(50), nullable=True, index=True, comment="所属行政区")
    business_area = Column(String(100), nullable=True, index=True, comment="所属商圈")

    # === 地理位置 ===
    latitude = Column(DECIMAL(10, 6), nullable=True, comment="纬度")
    longitude = Column(DECIMAL(10, 6), nullable=True, comment="经度")
    subway_distance = Column(Integer, nullable=True, comment="地铁距离（米）")

    # === 数据来源 ===
    data_source = Column(String(50), nullable=True, comment="数据来源")
    crawl_time = Column(DateTime, nullable=True, comment="采集时间")

    # === 时间戳 ===
    create_time = Column(DateTime, nullable=False, default=datetime.utcnow, comment="创建时间")
    update_time = Column(DateTime, nullable=True, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间")

    # === 关联关系 ===
    # 用户收藏（多对多，通过 user_favorites 表）
    favorites = relationship(
        "UserFavorite",
        foreign_keys="UserFavorite.restaurant_id",
        cascade="all, delete-orphan"
    )

    # === 索引 ===
    __table_args__ = (
        Index('idx_location', 'latitude', 'longitude'),
        {'comment': '餐厅基础信息表'}
    )

    def __repr__(self):
        return f"<Restaurant(restaurant_id={self.restaurant_id}, name={self.restaurant_name}, district={self.district})>"

    def get_location(self) -> tuple:
        """获取经纬度坐标"""
        if self.latitude and self.longitude:
            return (float(self.latitude), float(self.longitude))
        return None
