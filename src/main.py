from contextlib import asynccontextmanager
from fastapi import FastAPI, Response

from src.core.config import settings
from src.core.exception import register_exception_handlers
from src.lifespan import lifespan # 🟢 关键：导入生命周期管理

# 导入各个模块的路由
# 注意：你需要确保 src/dishes/router.py 已经写好了（我们之前还没写这个文件，下一步必须补上）
#from src.dishes.router import router as dishes_router
# from src.collections.router import router as collections_router
# from src.weather.router import router as weather_router

# 如果你有 FastAPI Users，取消注释
# from src.auth.user_manager import fastapi_users
# from src.auth.router import register_fastapi_users_routes


app = FastAPI(
    title=settings.app_name, # 使用 title 而不是 app_name
    version="0.1.0",
    description="FastAPI + SQLModel 练习项目实战",
    lifespan=lifespan, # 🟢 绑定生命周期，启动时会自动建表
)

# 1. 注册全局异常处理
register_exception_handlers(app)

# 2. 注册路由 (建议加上 api 前缀)
# 这样访问路径变成: POST /api/v1/dishes
#app.include_router(dishes_router, prefix="/api/v1", tags=["Dishes"])

# 以后写好了 Collection 再解开
# app.include_router(collections_router, prefix="/api/v1", tags=["Collections"])
# app.include_router(weather_router, prefix="/api/v1", tags=["Weather"])

# 3. 注册 Auth 路由 (如果有)
# register_fastapi_users_routes(app, fastapi_users)

@app.get("/health")
async def health_check():
    """健康检查接口"""
    return {"status": "ok", "app_name": settings.app_name}