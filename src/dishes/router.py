from typing import Annotated, List

from fastapi import APIRouter, Depends, Path, status
from sqlalchemy.ext.asyncio import AsyncSession

# 🟢 导入我们在 database.py 定义的获取 session 的函数
from src.core.database import get_db
from src.dishes.repository import DishRepository

# 🟢 导入 Schema (注意文件名是 schemas 不是 schema)
# DishResponse -> 改名为 DishPublic (SQLModel 规范命名)
from src.dishes.schema import DishCreate, DishPublic, DishQueryParams, DishUpdate

# 导入 Service 和 Repository
from src.dishes.service import DishService

# 暂未实现 Auth，先注释掉，防报错
# from src.auth.user_manager import get_current_user, current_superuser

# 1. 初始化路由
# prefix="/dishes": 这里的路径前缀。如果 main.py 挂载在 /api/v1，最终路径是 /api/v1/dishes
#tags=["Dishes"]: 用于分组，方便在 Swagger UI 中查看
router = APIRouter(tags=["Dishes"])

# =====================================================================
# 🟢 依赖注入核心 (The Glue)
# 作用：自动组装 Session -> Repository -> Service
# =====================================================================
async def get_dish_service(session: AsyncSession = Depends(get_db)) -> DishService:
    """
    依赖注入工厂函数：
    1. FastAPI 自动注入数据库 Session
    2. 创建 Repository 实例
    3. 创建 Service 实例并返回
    """
    repository = DishRepository(session)
    return DishService(repository)

# 定义一个类型别名，方便后面写参数类型，让代码更短
DishServiceDep = Annotated[DishService, Depends(get_dish_service)]


# =====================================================================
# 🟢 API 接口定义
# =====================================================================
#201 Created: 表示资源创建成功，返回新创建的资源
#200 OK: 表示请求成功，返回请求的数据
#@router.post: 表示这是一个 POST 请求
@router.post(
    "/",  # URL: POST /api/v1/dishes/
    response_model=DishPublic,      # 🟢 滤镜：告诉 FastAPI 用 DishPublic 过滤返回数据
    status_code=status.HTTP_201_CREATED, # 成功时返回 201 而不是 200
    summary="创建新菜品" #summary什么作用：用于在 Swagger UI 中显示接口的摘要信息
)
async def create_dish(
    dish_in: DishCreate,            # 🟢 保安：自动校验用户传来的 JSON 是否符合 DishCreate
    service: DishServiceDep         # 🟢 注入：拿到组装好的 Service
):
    """
    创建一个新的菜品。
    - **name**: 菜品名称（必须唯一）
    - **description**: 描述（可选）
    """
    # 直接调用 Service，逻辑非常干净
    return await service.create_dish(dish_in)
#DishServiceDep 只是个类型注释为什么可以直接被 FastAPI 识别并注入？
#因为 FastAPI 有一个叫做 "依赖注入" 的机制，它可以自动识别并注入 Annotated 类型的参数。
#在这个例子中，DishServiceDep 是一个 Annotated 类型，它的第一个参数是 DishService，第二个参数是 Depends(get_dish_service)。
#FastAPI 会自动调用 get_dish_service 函数，获取一个 DishService 实例，并将其注入到 create_dish 函数的 service 参数中。
#返回了一个service实例，service实例里有create_dish方法，所以可以直接调用service.create_dish(dish_in)
#如何使用这个接口：
#1. 发送 POST 请求到 /api/v1/dishes/
#2. 在请求体中 JSON 格式提交菜品数据，例如：
#{
#    "name": "鱼香肉丝",
#    "description": "鱼香肉丝是一道传统的中国名菜"
#}
#3. 如果数据验证通过，会返回新创建的菜品信息，例如：
#{
#    "id": 1,
#    "name": "鱼香肉丝",
#    "description": "鱼香肉丝是一道传统的中国名菜"
#}
@router.get("/{dish_id}", response_model=DishPublic, summary="获取单个菜品")
async def get_dish(service: DishServiceDep,
    dish_id: int = Path(..., description="菜品ID"), # Path 表示这是 URL 路径里的参数
    ):
    # 🟢 注意：我删掉了这里的 try...except
    # 原因：我们已经写了全局异常处理 (src/core/exception.py)。
    # 如果 Service 抛出 NotFoundException，全局处理器会自动捕获并返回 404。
    # 这里不需要再手动 try 了，代码更简洁。
    return await service.get_dish_by_id(dish_id)

#如何调用这个接口：
#1. 发送 GET 请求到 /api/v1/dishes/123
#2. 如果 ID 为 123 的菜品存在，会返回该菜品的信息，例如：
#{
#    "id": 123,
#    "name": "鱼香肉丝",
#    "description": "鱼香肉丝是一道传统的中国名菜"
#}
#3. 如果 ID 不存在，会返回 404 错误，例如：
#{
#    "detail": "Dish with id 123 not found"
#}
@router.get("/", response_model=List[DishPublic], summary="查询菜品列表")
async def list_dishes(
    service: DishServiceDep,
    # 🟢 技巧：使用 Pydantic 模型接收查询参数
    # 这样你就不用写 search: str, limit: int... 一大堆参数了
    # Depends() 会自动把 URL 里的 ?limit=10&search=xxx 映射到 DishQueryParams 模型里
    params: DishQueryParams = Depends() #depends中没有参数，所以会使用默认值，默认值是DishQueryParams()
):
    """
    获取菜品列表，支持分页、搜索、排序。
    """
    return await service.list_dishes(
        search=params.search,
        order_by=params.order_by,
        direction=params.direction,
        limit=params.limit,
        offset=params.offset,
    ) #list_dishes返回一个包含多个 DishPublic 模型的列表


@router.patch("/{dish_id}", response_model=DishPublic, summary="更新菜品")
async def update_dish(
    dish_id: int,
    dish_in: DishUpdate, # 接收更新的数据（所有字段都是可选的）
    service: DishServiceDep, #为什么需要依赖注入：因为需要调用service.update_dish方法
):
    """
    更新 ID 为 dish_id 的菜品信息。
    - **name**: 菜品名称（可选）
    - **description**: 描述（可选）
    """
    return await service.update_dish(dish_id, dish_in)

#如何调用这个接口：
#1. 发送 PATCH 请求到 /api/v1/dishes/123
#2. 在请求体中 JSON 格式提交更新数据，例如：
#{
#    "name": "鱼香肉丝",
#    "description": "鱼香肉丝是一道传统的中国名菜"
#}
#3. 如果 ID 为 123 的菜品存在，会返回更新后的菜品信息，例如：
#{
#    "id": 123,
#    "name": "鱼香肉丝",
#    "description": "鱼香肉丝是一道传统的中国名菜"
#}
#4. 如果 ID 不存在，会返回 404 错误，例如：
#{
#    "detail": "Dish with id 123 not found"
#}
#如何调用这个接口：
#1. 发送 DELETE 请求到 /api/v1/dishes/123
#2. 如果 ID 为 123 的菜品存在，会返回 204 状态码，说明删除成功。
#3. 如果 ID 不存在，会返回 404 错误，例如：
#{
#    "detail": "Dish with id 123 not found"
#}
#如何调用这个接口：
#1. 发送 DELETE 请求到 /api/v1/dishes/123
#2. 如果 ID 为 123 的菜品存在，会返回 204 状态码，说明删除成功。
#3. 如果 ID 不存在，会返回 404 错误，例如：
#{
#    "detail": "Dish with id 123 not found"
#}
@router.delete(
    "/{dish_id}",
    status_code=status.HTTP_204_NO_CONTENT, # 204 表示删除成功，没有内容返回
    summary="删除菜品"
    # dependencies=[Depends(current_superuser)], # 等你有 Auth 了再解开
)
async def delete_dish(
    dish_id: int,
    service: DishServiceDep,
):
    await service.delete_dish(dish_id)
