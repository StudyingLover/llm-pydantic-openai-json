# 实体类转换为json字符串
from pydantic import BaseModel
from typing import List


class Point(BaseModel):
    x: float
    y: float
    z: float


class Item(BaseModel):
    id: int
    name: str
    description: str
    number: int
    price: float
    position: List[Point]


item = Item(
    id=1,
    name="example",
    description="example description",
    number=1,
    price=1.0,
    position=[Point(x=1.0, y=2.0, z=3.0)],
)
print(item.model_dump_json())
