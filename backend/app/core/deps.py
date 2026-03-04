# FastAPI 依赖注入
# 功能：
# - get_db()            获取数据库会话（yield模式，自动关闭）
# - get_current_user()  从请求Header中提取Token，解析当前用户（依赖 security.verify_token）
# - require_role()      角色权限校验装饰器（admin/analyst/editor）
# - get_redis()         获取 Redis 连接
