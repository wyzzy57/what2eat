# /src/core/config.py
from typing import Literal

from pydantic import computed_field, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# 这个文件是应用的配置中心，使用Pydantic Settings管理：

# - 定义应用基本信息（名称、调试模式）
# - 支持两种数据库类型：PostgreSQL和SQLite
# - 包含完整的数据库连接参数和连接池配置
# - 提供Redis连接配置（认证和缓存）
# - 配置JWT密钥
# - 使用计算属性动态生成：
#   - 数据库连接URL
#   - SQLAlchemy引擎选项
#   - Redis连接URL
# - 从.env文件加载环境变量


class Settings(BaseSettings):
    """应用配置（支持 PostgreSQL 和 SQLite，含连接池设置，兼容 SQLModel 异步使用）"""

    app_name: str = "What to Eat"
    debug: bool = False

    # 数据库类型
    db_type: Literal["postgres", "sqlite"] = "postgres"

    # PostgreSQL 配置
    db_host: str = "localhost"
    db_port: int = Field(ge=1, le=65535, default=5432, description="数据库端口")
    db_user: str = "postgres"
    db_password: str = Field(..., description="数据库密码，必须通过环境变量设置")
    db_name: str = "what2eat"

    # 连接池配置（仅 PostgreSQL 有效）
    pool_size: int = Field(ge=1, le=100, default=20, description="连接池大小")
    max_overflow: int = 10
    pool_timeout: int = 30
    pool_pre_ping: bool = True
    pool_recycle: int = 3600
    pool_use_lifo: bool = False
    echo: bool = False

    # SQLite 配置
    sqlite_db_path: str = "./data/what2eat.sqlite3"

    # Redis 配置
    redis_host: str = "localhost"
    redis_port: int = Field(ge=1, le=65535, default=6379, description="Redis端口")
    auth_redis_db: int = 0
    cache_redis_db: int = 1

    @computed_field
    @property
    def database_url(self) -> str:
        """根据数据库类型生成对应的数据库连接URL"""
        if self.db_type == "postgres":
            return (
                f"postgresql+psycopg://{self.db_user}:{self.db_password}"
                f"@{self.db_host}:{self.db_port}/{self.db_name}"
            )
        elif self.db_type == "sqlite":
            return f"sqlite+aiosqlite:///{self.sqlite_db_path}"
        else:
            raise ValueError(f"Unsupported DB_TYPE: {self.db_type}")

    @computed_field
    @property
    def engine_options(self) -> dict:
        """统一封装 engine options，供 create_async_engine 使用（SQLModel 兼容）"""
        if self.db_type == "postgres":
            return {
                "pool_size": self.pool_size,
                "max_overflow": self.max_overflow,
                "pool_timeout": self.pool_timeout,
                "pool_recycle": self.pool_recycle,
                "pool_use_lifo": self.pool_use_lifo,
                "echo": self.echo,
                "pool_pre_ping": self.pool_pre_ping,
            }
        # SQLite 不支持连接池参数
        return {"echo": self.echo}

    @computed_field
    @property
    def auth_redis_url(self) -> str:
        """认证服务的Redis连接URL"""
        return f"redis://{self.redis_host}:{self.redis_port}/{self.auth_redis_db}"

    @computed_field
    @property
    def cache_redis_url(self) -> str:
        """缓存服务的Redis连接URL"""
        return f"redis://{self.redis_host}:{self.redis_port}/{self.cache_redis_db}"

    # JWT configuration
    jwt_secret: str = Field(..., description="JWT 密钥，必须通过环境变量设置")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        env_prefix="",  # 添加前缀，避免环境变量冲突
    )


settings = Settings()