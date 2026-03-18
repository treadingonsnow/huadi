# 数据库连接管理
# 功能：
# - 使用 SQLAlchemy 创建 MySQL 异步连接引擎
# - 定义 SessionLocal 会话工厂
# - 定义 Base 声明基类（所有 ORM 模型继承）
# - 提供 get_db 依赖注入函数，用于 API 路由获取数据库会话
# - Redis 连接池初始化
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# 使用相对导入（同一目录下的 config.py）
from .config import settings

# 创建数据库引擎
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,  # 连接前检查
    pool_recycle=3600,  # 连接回收时间（秒）
    pool_size=10,  # 连接池大小
    max_overflow=20,  # 最大溢出连接数
    echo=settings.APP_ENV == "development"  # 开发环境打印 SQL
)

# 创建会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 模型基类
Base = declarative_base()


def get_db():
    """
    依赖注入：获取数据库会话

    使用方式：
    @router.get("/xxx")
    def xxx(db: Session = Depends(get_db)):
        ...
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()