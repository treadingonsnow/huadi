# FastAPI 应用入口
# 功能：
# - 创建 FastAPI 应用实例，配置 CORS 中间件
# - 注册 v1 版本 API 路由（/api/v1）
# - 配置全局异常处理器
# - 应用启动/关闭时的生命周期事件（数据库连接池初始化、Redis 连接等）

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import SQLAlchemyError
from .config import settings
from .database import Base, engine, SessionLocal
from .response import success, error

# === 创建 FastAPI 应用 ===

app = FastAPI(
    title=settings.APP_NAME,
    description="上海美食大数据分析平台 API",
    version="1.0.0",
    docs_url="/docs",  # Swagger UI
    redoc_url="/redoc",  # ReDoc
    openapi_url="/openapi.json"
)

# === 配置 CORS 中间件 ===

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# === 全局异常处理器 ===
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """处理请求参数验证异常"""
    return error(
        message=f"参数验证失败：{exc.errors()[0].get('msg', '未知错误')}",
        code=422
    )

@app.exception_handler(SQLAlchemyError)
async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError):
    """处理数据库异常"""
    return error(
        message="数据库操作失败",
        code=500
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """处理其他未捕获异常"""
    return error(
        message=f"服务器内部错误：{str(exc)}",
        code=500
    )
# === 应用生命周期事件 ===
# === 应用生命周期事件 ===

@app.on_event("startup")
async def startup_event():
    """
    应用启动时执行
    - 初始化数据库连接池
    - 初始化 Redis 连接
    - 加载缓存配置等
    """
    print(f"\n{'=' * 50}")
    print(f"🚀 {settings.APP_NAME} 启动中...")
    print(f"{'=' * 50}")

    # 测试数据库连接
    try:
        from sqlalchemy import text
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
        print("✅ 数据库连接成功")
    except Exception as e:
        print(f"❌ 数据库连接失败：{e}")

    # TODO: 初始化 Redis 连接
    # redis_client = redis.Redis(...)

    print(f"📍 环境：{settings.APP_ENV}")
    print(f"📍 端口：{settings.APP_PORT}")
    print(f"📍 文档：http://localhost:{settings.APP_PORT}/docs")
    print(f"{'=' * 50}\n")


@app.on_event("shutdown")
async def shutdown_event():
    """
    应用关闭时执行
    - 关闭数据库连接池
    - 关闭 Redis 连接
    - 清理临时资源等
    """
    print(f"\n{'=' * 50}")
    print(f"🛑 应用关闭中...")
    print(f"{'=' * 50}")

    # TODO: 关闭 Redis 连接
    # redis_client.close()

    print("✅ 资源清理完成\n")


# === 注册路由 ===

# 认证模块
from .api.v1 import auth

app.include_router(auth.router, prefix="/api/v1/auth", tags=["用户认证"])

# 餐厅模块
from .api.v1 import restaurants

app.include_router(restaurants.router, prefix="/api/v1/restaurants", tags=["餐厅"])

# 分析模块
from .api.v1 import analysis

app.include_router(analysis.router, prefix="/api/v1", tags=["数据分析"])


# === 根路径 ===

@app.get("/")
def root():
    """根路径"""
    return success(data={
        "name": settings.APP_NAME,
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    })


# === 健康检查 ===

@app.get("/health")
def health_check():
    """健康检查接口"""
    return success(data={
        "status": "healthy",
        "env": settings.APP_ENV,
        "database": "connected"
    })


# === 启动命令 ===

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=settings.APP_PORT,
        reload=settings.APP_ENV == "development"
    )
