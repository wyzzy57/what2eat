# src/core/redis_db.py
from typing import cast

from fastapi import Request
from redis.asyncio import Redis

from src.core.config import settings


# 创建认证 Redis 连接
# 认证 Redis 连接用于存储用户认证信息，例如会话 ID、访问令牌等
def create_auth_redis() -> Redis:
    return Redis.from_url(
        settings.auth_redis_url,
        max_connections=20,
        decode_responses=True,
    )


# 创建缓存 Redis 连接
# 缓存 Redis 连接用于存储临时数据，例如用户会话、缓存结果等
def create_cache_redis() -> Redis:
    return Redis.from_url(
        settings.cache_redis_url,
        max_connections=20,
        decode_responses=True,
    )

# 获取认证 Redis 连接
# 从请求状态中获取认证 Redis 连接
async def get_auth_redis(request: Request) -> Redis:
    return cast(Redis, request.state.auth_redis)


# 获取缓存 Redis 连接
# 从请求状态中获取缓存 Redis 连接
async def get_cache_redis(request: Request) -> Redis:
    return cast(Redis, request.state.cache_redis)
