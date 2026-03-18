# 依赖注入模块
# 功能：
# - get_db()          获取数据库会话
# - get_current_user() 获取当前登录用户（需要 JWT Token）

from __future__ import annotations

from collections.abc import Generator
from typing import TYPE_CHECKING
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

# 条件导入（避免循环依赖，同时让 IDE 识别）
if TYPE_CHECKING:
    from sqlalchemy.orm import Session
    # 使用相对导入：.. 表示向上 1 级（core → app → models）
    from ..models.user import User


# === 数据库依赖 ===

def get_db() -> Generator[Session, None, None]:
    """获取数据库会话"""
    # 相对导入：.. 表示向上 1 级（core → app）
    from ..database import get_db as database_get_db
    yield from database_get_db()


# === 认证依赖 ===

# OAuth2 密码流方案（用于从 Header 获取 Token）
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


def get_current_user(
        token: str = Depends(oauth2_scheme),
        db: Session = Depends(get_db)
) -> "User":
    """
    获取当前登录用户

    参数:
        token: JWT Token（从 Authorization Header 自动获取）
        db: 数据库会话

    返回:
        User: 当前用户对象

    异常:
        HTTPException 401: Token 无效或用户不存在
    """
    # 相对导入
    from .security import verify_token
    from ..models.user import User

    # 验证 Token
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    # 解码 Token
    payload = verify_token(token)
    if payload is None:
        raise credentials_exception

    # 获取用户 ID
    user_id = payload.get("sub")
    if user_id is None:
        raise credentials_exception

    # 查询用户
    user = db.query(User).filter(User.user_id == int(user_id)).first()
    if user is None:
        raise credentials_exception

    # 检查用户是否启用
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is disabled",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


def get_current_active_user(
        current_user: "User" = Depends(get_current_user)
) -> "User":
    """获取当前激活用户"""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is disabled",
        )
    return current_user


def get_current_admin_user(
        current_user: "User" = Depends(get_current_user)
) -> "User":
    """获取当前管理员用户"""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )
    return current_user
