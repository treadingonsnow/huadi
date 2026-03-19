# 用户认证 API 路由
# 功能：
# - POST /register        用户注册（用户名 + 密码，密码 BCrypt 加密存储）
# - POST /login           用户登录（用户名密码），返回 JWT Token
# - POST /refresh         刷新 Token（Token 有效期 24 小时）
# - GET  /me              获取当前用户信息
# - PUT  /me              更新用户信息

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import timedelta

# 相对导入
from ...database import get_db
from ...core.security import hash_password, verify_password, create_access_token, verify_token
from ...core.deps import get_current_user
from ...response import success, error
from ...models.user import User

router = APIRouter()


# === 用户注册 ===

@router.post("/register")
def register(
        username: str,
        password: str,
        db: Session = Depends(get_db)
):
    """
    用户注册

    参数:
        username: 用户名
        password: 密码

    返回:
        {"code": 200, "message": "success", "data": {"user_id": 1, "username": "xxx"}}
    """
    # 检查用户名是否已存在
    existing_user = db.query(User).filter(User.username == username).first()
    if existing_user:
        return error(msg="用户名已存在", code=400)

    # 创建新用户
    new_user = User(
        username=username,
        password_hash=hash_password(password),
        role="user",
        is_active=True
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return success(data={
        "user_id": new_user.user_id,
        "username": new_user.username,
        "role": new_user.role
    })


# === 用户登录 ===

@router.post("/login")
def login(
        username: str,
        password: str,
        db: Session = Depends(get_db)
):
    """
    用户登录

    参数:
        username: 用户名
        password: 密码

    返回:
        {"code": 200, "message": "success", "data": {"access_token": "xxx", "token_type": "bearer"}}
    """
    # 查询用户
    user = db.query(User).filter(User.username == username).first()

    # 验证用户是否存在
    if not user or not user.is_active:
        return error(msg="用户名或密码错误", code=401)

    # 验证密码
    if not verify_password(password, user.password_hash):
        return error(msg="用户名或密码错误", code=401)

    # 生成 Token
    access_token = create_access_token(
        user_id=user.user_id,
        username=user.username,
        role=user.role,
        expires_delta=timedelta(minutes=60 * 24)  # 24 小时
    )

    # 更新最后登录时间
    from datetime import datetime
    user.last_login = datetime.utcnow()
    db.commit()

    return success(data={
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": 60 * 60 * 24  # 24 小时（秒）
    })


# === 刷新 Token ===

@router.post("/refresh")
def refresh_token(
        token: str,
        db: Session = Depends(get_db)
):
    """
    刷新 Token

    参数:
        token: 当前有效的 Token

    返回:
        {"code": 200, "message": "success", "data": {"access_token": "xxx", "token_type": "bearer"}}
    """
    # 验证 Token
    payload = verify_token(token)
    if payload is None:
        return error(msg="Token 无效或已过期", code=401)

    # 获取用户信息
    user_id = payload.get("sub")
    user = db.query(User).filter(User.user_id == int(user_id)).first()

    if not user or not user.is_active:
        return error(msg="用户不存在或已禁用", code=401)

    # 生成新 Token
    new_token = create_access_token(
        user_id=user.user_id,
        username=user.username,
        role=user.role,
        expires_delta=timedelta(minutes=60 * 24)  # 24 小时
    )

    return success(data={
        "access_token": new_token,
        "token_type": "bearer",
        "expires_in": 60 * 60 * 24  # 24 小时（秒）
    })


# === 获取当前用户信息 ===

# === 获取当前用户信息 ===

@router.get("/me")
def get_current_user_info(
        current_user: User = Depends(get_current_user)
):
    """
    获取当前登录用户信息

    需要：Authorization: Bearer <token>

    返回:
        {"code": 200, "message": "success", "data": {"user_id": 1, "username": "xxx", ...}}
    """
    return success(data={
        "user_id": current_user.user_id,
        "username": current_user.username,
        "email": getattr(current_user, 'email', None),
        "role": getattr(current_user, 'role', 'user'),
        "is_active": getattr(current_user, 'is_active', True),
        "create_time": current_user.create_time.isoformat() if current_user.create_time else None,
        "last_login": current_user.last_login.isoformat() if current_user.last_login else None
    })


# === 更新用户信息 ===


@router.put("/me")
def update_current_user(
        email: str = None,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """
    更新当前登录用户信息
    """
    # 更新字段
    if email is not None:
        current_user.email = email

    db.commit()
    db.refresh(current_user)

    return success(data={
        "user_id": current_user.user_id,
        "username": current_user.username,
        "email": getattr(current_user, 'email', None),
        "role": getattr(current_user, 'role', 'user'),
        "is_active": getattr(current_user, 'is_active', True)
    })
