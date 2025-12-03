from datetime import datetime, timezone
from typing import Optional

# 这个文件定义了应用中所有数据模型的基础结构：
# - 设置了数据库对象（索引、唯一约束、外键等）的命名约定
# - 创建了 Base 基类，所有SQLModel模型都可以继承它
# - 定义了 DateTimeMixin 混入类，为模型提供时间戳功能：
#   - created_at ：记录创建时间
#   - updated_at ：记录最后更新时间
#   - 针对PostgreSQL和SQLite提供了不同的实现方式，确保兼容性
# 1. 引入 Column
from sqlalchemy import Column, DateTime, func
from sqlmodel import Field, SQLModel

from src.core.config import settings

# 定义命名约定
database_naming_convention = {
    "ix": "%(column_0_label)s_idx",
    "uq": "%(table_name)s_%(column_0_name)s_key",
    "ck": "%(table_name)s_%(constraint_name)s_check",
    "fk": "%(table_name)s_%(column_0_name)s_fkey",
    "pk": "%(table_name)s_pkey",
}

# 应用命名约定
SQLModel.metadata.naming_convention = database_naming_convention


class Base(SQLModel):
    pass


class DateTimeMixin:
    if settings.db_type == "postgres":
        # Postgres: 使用 sa_column 封装 SQLAlchemy 的 Column 定义
        # 这样可以避免 IDE 报 "类型不匹配" 的错误，因为 Column 明确接受 TypeEngine 实例
        created_at: Optional[datetime] = Field(
            default=None,
            sa_type=DateTime(timezone=True),  # 指定数据库类型
            sa_column_kwargs={
                "server_default": func.now(),  # 数据库自动生成时间
                "nullable": False
            },
            index=True,
        )
        updated_at: Optional[datetime] = Field(
            default=None,
            sa_type=DateTime(timezone=True),
            sa_column_kwargs={
                "server_default": func.now(),
                "onupdate": func.now(),  # 数据库自动更新时间
                "nullable": False
            },
        )
    else:
        # SQLite: 混合使用 Pydantic 的 default_factory 和 SQLAlchemy 的 Column
        created_at: datetime = Field(
            default_factory=lambda: datetime.now(timezone.utc),
            sa_column=Column(
                DateTime(timezone=True),
                nullable=False,
                index=True
            ),
        )
        updated_at: datetime = Field(
            default_factory=lambda: datetime.now(timezone.utc),
            sa_column=Column(
                DateTime(timezone=True),
                nullable=False,
                onupdate=lambda: datetime.now(timezone.utc) # SQLite 需要在 SQLAlchemy 层处理更新钩子
            ),
        )
