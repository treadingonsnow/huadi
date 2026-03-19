# 安全相关工具
# 功能：
# - create_access_token()   生成 JWT Token（payload: user_id, role, exp）
# - verify_token()          验证并解析 JWT Token
# - hash_password()         BCrypt 密码加密
# - verify_password()       BCrypt 密码验证

from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext

# 使用相对导入：.. 表示向上 1 级（core → app）
from ..config import settings

# === 密码加密上下文 ===
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# === 密码哈希 ===

def hash_password(password: str) -> str:
    """
    BCrypt 密码加密

    参数:
        password: 明文密码

    返回:
        str: 哈希后的密码
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    BCrypt 密码验证

    参数:
        plain_password: 明文密码
        hashed_password: 哈希密码

    返回:
        bool: 密码是否匹配
    """
    return pwd_context.verify(plain_password, hashed_password)


# === JWT Token ===

def create_access_token(user_id: int, username: str, role: str, expires_delta: Optional[timedelta] = None) -> str:
    """
    生成 JWT Token

    参数:
        user_id: 用户 ID
        username: 用户名
        role: 用户角色
        expires_delta: 过期时间增量（可选）

    返回:
        str: JWT Token
    """
    to_encode = {
        "sub": str(user_id),  # 用户 ID
        "username": username,  # 用户名
        "role": role,  # 用户角色
        "iat": datetime.utcnow()  # 签发时间
    }

    # 设置过期时间
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode["exp"] = expire

    # 生成 Token
    encoded_jwt = jwt.encode(
        to_encode,
        settings.APP_SECRET_KEY,
        algorithm=settings.ALGORITHM
    )

    return encoded_jwt


def verify_token(token: str) -> Optional[dict]:
    """
    验证并解析 JWT Token

    参数:
        token: JWT Token

    返回:
        dict: 解码后的 payload（包含 user_id, username, role, exp），验证失败返回 None
    """
    try:
        payload = jwt.decode(
            token,
            settings.APP_SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        return payload
    except JWTError:
        return None
