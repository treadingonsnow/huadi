# 用户认证 API 路由
# 功能：
# - POST /register        用户注册（用户名+密码，密码 BCrypt 加密存储）
# - POST /login           用户登录（用户名密码 / 手机验证码），返回 JWT Token
# - POST /refresh         刷新 Token（Token有效期24小时）
# - GET  /me              获取当前用户信息
# - PUT  /me              更新用户信息
