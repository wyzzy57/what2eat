# src/core/database.py （建议重命名文件为 database.py）
from typing import AsyncGenerator

from loguru import logger
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlmodel import SQLModel

from config import settings

# 注意：确保所有模型（如 Dish）已正确导入，否则 metadata 为空


# 创建异步引擎
engine = create_async_engine(settings.database_url, **settings.engine_options)
#异步引擎是是所有异步数据库操作（如会话、连接、事务）的基础。

# 创建异步会话工厂 创建会话（Session）的作用是：
# 提供一个与数据库交互的“工作区”或“对话上下文”，用于执行查询、增删改操作、管理事务和对象状态。
SessionFactory = async_sessionmaker(
    class_=AsyncSession,#异步会话
    autoflush=False,#控制是否在每次查询前自动将待处理的变更同步（flush）到数据库
    expire_on_commit=False,#提交后，对象保持“新鲜”,别把对象清空。
    bind=engine,
)


# FastAPI 依赖注入用的数据库会话
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with SessionFactory() as session:
        yield session


# 初始化数据库表（仅用于开发/测试！生产请用 Alembic）
#SQLModel.metadata 就像一个花名册。当你定义了 class User(SQLModel, table=True) 时，User 就自动签到进了这个花名册。
async def create_db_and_tables():
    async with engine.begin() as conn:
        # 使用 SQLModel 的 metadata 创建所有表
        await conn.run_sync(SQLModel.metadata.create_all)
    logger.info("数据库表创建成功。")