# 用户 ORM 模型
# 对应数据表：sys_user
# 字段：
# - user_id       INT PK AUTO_INCREMENT  用户ID
# - username      VARCHAR(50) UNIQUE      用户名
# - password_hash VARCHAR(128)            密码哈希（BCrypt）
# - phone         VARCHAR(20)             手机号
# - email         VARCHAR(100)            邮箱
# - role          VARCHAR(20)             角色（admin/analyst/editor/user）
# - is_active     BOOLEAN                 是否启用
# - create_time   DATETIME                创建时间
# - last_login    DATETIME                最后登录时间
#
# 关联表：user_favorites（用户收藏）
# - user_id, restaurant_id, create_time
# 用户 ORM 模型
# 对应数据表：sys_user
# 字段：
# - user_id       INT PK AUTO_INCREMENT  用户 ID
# - username      VARCHAR(50) UNIQUE      用户名
# - password_hash VARCHAR(128)            密码哈希（BCrypt）
# - phone         VARCHAR(20)             手机号
# - email         VARCHAR(100)            邮箱
# - role          VARCHAR(20)             角色（admin/analyst/editor/user）
# - is_active     BOOLEAN                 是否启用
# - create_time   DATETIME                创建时间
# - last_login    DATETIME                最后登录时间
#
# 关联表：user_favorites（用户收藏）
# 用户 ORM 模型
# 对应数据表：sys_user
from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.orm import relationship
from ..database import Base
from datetime import datetime

# 用户 ORM 模型
# 对应数据表：sys_user

from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.orm import relationship
from ..database import Base
from datetime import datetime


class User(Base):
    """用户模型 - 对应 sys_user 表"""

    __tablename__ = "sys_user"

    # === 主键 ===
    user_id = Column(Integer, primary_key=True, autoincrement=True, index=True)

    # === 基本信息 ===
    username = Column(String(50), unique=True, nullable=False, index=True, comment="用户名")
    password_hash = Column(String(128), nullable=False, comment="密码哈希（BCrypt）")
    email = Column(String(100), nullable=True, comment="邮箱")

    # === 权限控制 ===
    role = Column(String(20), nullable=False, default="user", comment="角色（admin/analyst/editor/user）")
    is_active = Column(Boolean, nullable=False, default=True, comment="是否启用")

    # === 时间戳 ===
    create_time = Column(DateTime, nullable=True, default=datetime.utcnow, comment="创建时间")
    last_login = Column(DateTime, nullable=True, comment="最后登录时间")

    # === 关联关系 ===
    favorites = relationship(
        "UserFavorite",
        foreign_keys="UserFavorite.user_id",
        cascade="all, delete-orphan"
    )

    # === 模型配置 ===
    __table_args__ = {
        'comment': '用户信息表'
    }

    def __repr__(self):
        return f"<User(user_id={self.user_id}, username={self.username}, role={self.role})>"

    def is_admin(self) -> bool:
        """检查是否为管理员"""
        return self.role == "admin"
