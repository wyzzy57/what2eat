from datetime import datetime
from typing import Literal, Optional
from sqlmodel import SQLModel, Field

#这就是pydantic模型
# 它的作用是定义数据模型的结构和验证规则。
# 比如这里的 DishBase 模型，定义了一个 name 字段，类型是 str，最大长度是 255，
# 并且在 Swagger 文档中显示为 "菜品名称"，并提供一个示例 "番茄炒蛋"。
#
# ==========================================
# 1. 基础模型 (Base Schema)
# 🟢 用途：存放 Create, Read, Update 都共用的字段
# 🔴 注意：这里的 name 字段是必填的 (str)，因为在数据库中它是 NOT NULL
# ==========================================
class DishBase(SQLModel):
    # Field 参数说明：
    # max_length: 对应数据库 varchar长度限制
    # schema_extra (可选):用于生成 Swagger 文档的示例
    name: str = Field(
        max_length=255,
        description="菜品名称",
        schema_extra={"example": "番茄炒蛋"}
    )
    description: Optional[str] = Field(
        default=None,
        description="菜品描述",
        schema_extra={"example": "家常做法，酸甜口"}
    )


# ==========================================
# 2. 创建模型 (Create Schema)
# 🟢 用途：POST /dishes 请求体
# ==========================================
class DishCreate(DishBase):
    """
    直接继承 DishBase。
    如果有只有创建时才需要的字段（比如 'password'），可以在这里加。
    """
    pass


# ==========================================
# 3. 更新模型 (Update Schema)
# 🟢 用途：PATCH /dishes/{id} 请求体
# ==========================================
class DishUpdate(SQLModel):
    # 注意：这里不继承 DishBase，因为 Base 里的 name 是必填的 (str)。
    # 而更新时，用户可能只想改描述，不传名字。所以所有字段都要设为 Optional。
    name: Optional[str] = Field(default=None, max_length=255)
    description: Optional[str] = Field(default=None)


# ==========================================
# 4. 响应模型 (Public / Response Schema)
# 🟢 用途：API 返回给前端的数据
# ==========================================
class DishPublic(DishBase):
    id: int
    created_at: datetime

    # 对应 dishes 表里的关联数据，如果你希望返回该菜品所属的收藏夹，可以在这里加：
    # collections: List["CollectionPublic"] = []


# ==========================================
# 5. 查询参数模型 (Filter Schema)
# 🟡 用途：GET /dishes?search=xxx&limit=10
# ==========================================
class DishQueryParams(SQLModel):
    search: Optional[str] = Field(
        default=None,
        description="搜索关键词"
    )
    order_by: Literal["id", "name", "created_at"] = Field(
        default="id",
        description="排序字段"
    )
    direction: Literal["asc", "desc"] = Field(
        default="asc",
        description="排序方向"
    )
    limit: int = Field(
        default=10,
        ge=1, le=500,
        description="分页大小"
    )
    offset: int = Field(
        default=0,
        ge=0,
        description="分页偏移"
    )