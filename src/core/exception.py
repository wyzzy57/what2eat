# app/core/exceptions.py
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.responses import JSONResponse
from loguru import logger


# ------------------ 业务异常 ------------------
# 404 资源不存在
class NotFoundException(HTTPException):
    def __init__(self, detail: str = "Resource not found"):
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=detail)


# 409 资源已存在    
class AlreadyExistsException(HTTPException):
    def __init__(self, detail: str = "Resource already exists"):
        super().__init__(status_code=status.HTTP_409_CONFLICT, detail=detail)

# 401 未授权
class UnauthorizedException(HTTPException):
    def __init__(self, detail: str = "Unauthorized access"):
        super().__init__(status_code=status.HTTP_401_UNAUTHORIZED, detail=detail)

# 403 禁止访问
class ForbiddenException(HTTPException):
    def __init__(self, detail: str = "Access forbidden"):
        super().__init__(status_code=status.HTTP_403_FORBIDDEN, detail=detail)


# ------------------ 全局兜底 ------------------
# 500 内部服务器错误
# 当 FastAPI 应用抛出未被捕获的异常时，会调用这个处理器。
# request: Request 是 FastAPI 提供的请求对象，包含了请求的所有信息。
# exc: Exception 是抛出的异常对象。
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception(f"Unhandled exception at {request.url.path}: {exc}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error"},
    )


# 专门用于注册全局异常的函数
# 这个函数的作用是向 FastAPI app 实例注册全局异常处理器。
def register_exception_handlers(app: FastAPI) -> None:
    """向 FastAPI app 实例注册全局异常处理器。"""
    # 注册全局异常处理器
    # Exception 是所有异常的基类，包括我们定义的业务异常。
    # 当 FastAPI 应用抛出任何异常时，会调用 global_exception_handler 处理器。
    app.add_exception_handler(Exception, global_exception_handler)
