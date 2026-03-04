# 数据库连接管理
# 功能：
# - 使用 SQLAlchemy 创建 MySQL 异步连接引擎
# - 定义 SessionLocal 会话工厂
# - 定义 Base 声明基类（所有 ORM 模型继承）
# - 提供 get_db 依赖注入函数，用于 API 路由获取数据库会话
# - Redis 连接池初始化
