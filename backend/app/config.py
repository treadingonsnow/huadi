# 应用配置管理
# 功能：
# - 使用 pydantic-settings 从 .env 文件加载配置
# - 定义数据库连接参数（MySQL、Redis）
# - 定义 JWT 密钥、Token 过期时间等安全配置
# - 定义爬虫相关配置（采集频率、代理池地址）
# - 定义高德地图 API Key 等第三方服务配置

import os
import yaml
from pathlib import Path
from functools import lru_cache
from pydantic_settings import BaseSettings

# 获取项目根目录路径 (huadi/)
# backend/app/config.py → 向上 3 级 = huadi/
BASE_DIR = Path(__file__).resolve().parent.parent.parent
ENV_PATH = BASE_DIR / ".env"
CONFIG_PATH = BASE_DIR / "config" / "config.yaml"


class Settings(BaseSettings):
    # === 应用配置 ===
    APP_NAME: str = "上海美食大数据分析平台"
    APP_ENV: str = "development"
    APP_PORT: int = 8000

    # === 数据库配置 (从 .env 读取) ===
    MYSQL_HOST: str
    MYSQL_PORT: int
    MYSQL_USER: str
    MYSQL_PASSWORD: str
    MYSQL_DATABASE: str

    # === Redis 配置 ===
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: str = ""
    REDIS_DB: int = 0

    # === Elasticsearch 配置 ===
    ES_HOST: str = "localhost"
    ES_PORT: int = 9200

    # === 安全配置 ===
    APP_SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 天

    # === 高德地图 API ===
    AMAP_API_KEY: str = ""

    # === 爬虫配置 ===
    CRAWL_DELAY: float = 1.0
    PROXY_POOL_URL: str = ""

    # === 数据库连接 URL ===
    @property
    def DATABASE_URL(self) -> str:
        return (
            f"mysql+pymysql://{self.MYSQL_USER}:{self.MYSQL_PASSWORD}@"
            f"{self.MYSQL_HOST}:{self.MYSQL_PORT}/{self.MYSQL_DATABASE}"
            f"?charset=utf8mb4"
        )

    # === Redis 连接 URL ===
    @property
    def REDIS_URL(self) -> str:
        if self.REDIS_PASSWORD:
            return f"redis://:{self.REDIS_PASSWORD}@{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"

    # === CORS 配置 ===
    @property
    def CORS_ORIGINS(self) -> list:
        if self.APP_ENV == "production":
            return ["http://your-production-domain.com"]
        return ["*"]  # 开发环境允许所有

    class Config:
        env_file = str(ENV_PATH)
        case_sensitive = True
        extra = "ignore"  # 忽略 .env 中未定义的字段


@lru_cache()
def get_settings() -> Settings:
    """获取配置单例"""
    return Settings()


def load_yaml_config() -> dict:
    """加载 config.yaml 配置（可选）"""
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    return {}


# 全局配置实例
settings = get_settings()
yaml_config = load_yaml_config()

# 开发环境打印配置信息
if settings.APP_ENV == "development":
    print(f"✅ 配置加载完成")
    print(f"   📍 环境：{settings.APP_ENV}")
    print(f"   📍 数据库：{settings.MYSQL_HOST}:{settings.MYSQL_PORT}/{settings.MYSQL_DATABASE}")
