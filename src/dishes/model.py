from typing import TYPE_CHECKING, Optional, List
from sqlmodel import SQLModel, Field, Relationship, Text

# 假设你已经定义好了 DateTimeMixin
from src.core.base_model import DateTimeMixin

if TYPE_CHECKING:
    from model import Collection


# ==========================================
# 1. 定义中间表 (Link Model)
# 🟢【核心必修】多对多关系必须显式定义这个“桥梁”
# ==========================================
class CollectionDishLink(SQLModel, table=True):
    __tablename__ = "collection_dish"  # 指定表名，对应原代码的 secondary

    # 这两个字段既是外键，联合起来又是主键
    collection_id: Optional[int] = Field(
        default=None,
        foreign_key="collections.id",
        primary_key=True
    )
    dish_id: Optional[int] = Field(
        default=None,
        foreign_key="dishes.id",
        primary_key=True
    )


# ==========================================
# 2. Dish 模型
# ==========================================
class Dish(SQLModel, DateTimeMixin, table=True):
    __tablename__ = "dishes"

    # id: 在 Python 侧创建对象时是 None (因为还没存库)，数据库自动生成 ID
    id: Optional[int] = Field(default=None, primary_key=True) #ptional 要么是指定类型要么不填

    # String(255) -> max_length=255
    name: str = Field(max_length=255, unique=True, nullable=False)

    # Text 类型 -> sa_type=Text (如果只是普通短文本，不加 sa_type 也可以)
    description: Optional[str] = Field(default=None, sa_type=Text) #sa_type 指定数据库中特有的长文本类型

    # 🟢【核心必修】多对多关系定义
    # 这里的 Relationship 是 SQLModel 提供的，用于定义多对多关系
    # back_populates="dishes" 表示在 Collection 模型中也有一个 dishes 属性，用于反向引用
    # link_model=CollectionDishLink 表示使用 CollectionDishLink 作为中间表
    collections: List["Collection"] = Relationship(
        back_populates="dishes", #建立双向联系
        link_model=CollectionDishLink  # <--- 这里必须传入中间表类，指定去哪查找
    )
