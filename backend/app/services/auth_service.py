# 认证授权业务服务
# 功能：
# - register_user()       用户注册（校验用户名唯一性，BCrypt加密密码，写入数据库）
# - authenticate_user()   用户登录验证（校验密码/验证码，生成JWT Token）
# - refresh_token()       刷新Token
# - get_current_user()    从Token解析当前用户信息
# - check_permission()    检查用户角色权限（RBAC）
