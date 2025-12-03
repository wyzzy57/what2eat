    # 导入你在 schemas.py 里定义的模型      
from src.dishes.schema import (
    DishCreate,
    DishPublic,  # 注意：之前我们定义的是 DishPublic，你这里叫 DishResponse，我都兼容
    DishUpdate,
)
from sqlalchemy.exc import IntegrityError

# 假设你定义了这些自定义异常
from src.core.exception import (
    AlreadyExistsException,
    NotFoundException,
)
from src.dishes.repository import DishRepository


class DishService:
    """
    业务逻辑层 (Service Layer)
    职责：
    1. 协调 Repository 进行数据操作
    2. 处理业务规则（比如：计算价格、校验权限）
    3. 转换异常（把 DB 错误转为业务错误）
    """
    # 这行代码的作用是初始化一个新的菜品服务。
    # 它的参数是一个 DishRepository 实例，用于操作数据库。
    def __init__(self, repository: DishRepository):
        self.repository = repository
    # 这行代码的作用是创建一个新的菜品。
    # 它的参数是一个 DishCreate 模型，包含了菜品的名称、价格等信息。
    # 它的返回值是一个 DishPublic 模型，包含了菜品的 ID、名称、价格等信息。
    async def create_dish(self, dish_in: DishCreate) -> DishPublic:
        try:
            # 直接把 Schema 扔给 Repository
            new_dish = await self.repository.create(dish_in)

            # 把数据库实体 (Dish) 转回 响应模型 (DishPublic)
            return DishPublic.model_validate(new_dish)
        # 这行代码的作用是捕获数据库层面的“唯一性冲突”。
        # 当尝试创建一个已存在的菜品时，数据库会抛出 IntegrityError。
        # 我们捕获这个异常，转抛为 AlreadyExistsException，
        # 这样 API 层只需要捕获这个异常就能返回 400 错误。
        except IntegrityError as e:
            # 🟡 捕获数据库层面的“唯一性冲突”，转抛为业务异常
            # 这样 API 层只需要捕获 AlreadyExistsException 就能返回 400 错误
            raise AlreadyExistsException(f"Dish with name '{dish_in.name}' already exists") from e

    async def get_dish_by_id(self, dish_id: int) -> DishPublic:
        dish = await self.repository.get_by_id(dish_id)
        if not dish:
            raise NotFoundException(f"Dish with id {dish_id} not found")

        return DishPublic.model_validate(dish)
    # 这行代码的作用是获取所有菜品。
    # 它的参数是一些查询参数，用于分页、搜索、排序等。
    # 它的返回值是一个包含多个 DishPublic 模型的列表。
    async def list_dishes(
        self,
        *,
        search: str | None = None,
        order_by: str = "id",
        direction: str = "asc",
        limit: int = 10,
        offset: int = 0,
    ) -> list[DishPublic]:

        dishes = await self.repository.get_all(
            search=search,
            order_by=order_by,
            direction=direction,
            limit=limit,
            offset=offset,
        )

        # 列表推导式：把一堆 DB Model 转成一堆 Public Schema
        #model_validate() 方法的作用是把一个 DB Model 实例转换为一个 Public Schema 实例。
        # 这样做的好处是：
        # 1. 隐藏了数据库的实现细节，前端只需要知道 DishPublic 模型的字段。
        # 2. 可以对数据进行验证和转换，确保数据的完整性和一致性。
        return [DishPublic.model_validate(dish) for dish in dishes]

    # 这行代码的作用是更新数据库中 ID 为 dish_id 的记录。
    # 如果找到，就返回一个 DishPublic 对象；如果没有找到，就返回 None。
    async def update_dish(self, dish_id: int, dish_in: DishUpdate) -> DishPublic:
        # 这里的 dish_in 是 Update Schema (全都是 Optional 的)
        # 我们不需要在 Service 层做 dump，直接传给 Repo
        try:
            updated_dish = await self.repository.update(dish_id, dish_in)

            if not updated_dish:
                raise NotFoundException(f"Dish with id {dish_id} not found")

            return DishPublic.model_validate(updated_dish)

        except IntegrityError as e:
            # 比如更新名字时，和别的菜名冲突了
            raise AlreadyExistsException("Dish with this name already exists") from e

    async def delete_dish(self, dish_id: int) -> None:
        deleted = await self.repository.delete(dish_id)
        if not deleted:
            raise NotFoundException(f"Dish with id {dish_id} not found")
