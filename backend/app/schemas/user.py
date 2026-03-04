# 用户相关 Pydantic Schema
# 包含：
# - UserRegisterRequest  注册请求（username, password, phone）
# - UserLoginRequest     登录请求（username + password / phone + code）
# - TokenResponse        登录响应（access_token, token_type, expires_in）
# - UserInfoResponse     用户信息响应（user_id, username, role, create_time）
# - UserUpdateRequest    用户信息更新请求
