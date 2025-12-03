from typing import TYPE_CHECKING, List, Optional

from sqlmodel import Field, Relationship

from src.core.base_model import Base, DateTimeMixin

# 🟢【修正 1】必须在运行时导入中间表类！
# (不用担心循环导入，因为 dishes/model.py 里只在 TYPE_CHECKING 时导入了 Collection)
from src.dishes.model import CollectionDishLink

if TYPE_CHECKING:
    from src.dishes.model import Dish


class Collection(Base, DateTimeMixin, table=True):
    __tablename__ = "collections"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(max_length=255, nullable=False)

    # 🟢【修正 2】link_model 必须传类 (CollectionDishLink)，不能传字符串
    dishes: List["Dish"] = Relationship(
        back_populates="collections",
        link_model=CollectionDishLink  # <--- 去掉引号！
    )
