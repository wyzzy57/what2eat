# app/lifespan.py
# lifespan 文件是 FastAPI 应用的生命周期管理文件
# 它定义了应用在启动和关闭时需要执行的操作
# 例如，连接数据库、初始化 Redis 连接、创建 HTTP 客户端等
# 为什么后面的代码没有连接数据库？
# 因为在 lifespan 函数中，我们只需要创建数据库表，而不需要连接数据库
# 连接数据库的操作会在 create_db_and_tables 函数中执行
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import TypedDict

from fastapi import FastAPI
from httpx import AsyncClient
from loguru import logger
from redis.asyncio import Redis

from src.core.database import create_db_and_tables
from src.core.redis_db import create_auth_redis, create_cache_redis


# 定义应用状态类型
# 用于在应用运行时传递 Redis 连接、HTTP 客户端等资源
# 每个请求都可以通过依赖注入获取到这些资源
# 这是返回类型验证，用于确保在应用运行时传递的资源类型是正确的
class State(TypedDict):
    auth_redis: Redis # 认证 Redis 连接
    cache_redis: Redis # 缓存 Redis 连接
    http_client: AsyncClient # HTTP 客户端，用于发送请求


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[State]:
    # -------- 启动 --------
    logger.info("应用启动，开始加载所有资源...")
    # 创建数据库表
    await create_db_and_tables()

    auth_redis = create_auth_redis()
    cache_redis = create_cache_redis()
    logger.info("Redis 已就绪。")
    http_client = AsyncClient(timeout=10)

    # -------- 运行 --------
    yield State(auth_redis=auth_redis, cache_redis=cache_redis, http_client=http_client)

    # -------- 关闭 --------
    await auth_redis.aclose()
    await cache_redis.aclose()
    await http_client.aclose()

    logger.info("应用关闭，资源已释放。")
