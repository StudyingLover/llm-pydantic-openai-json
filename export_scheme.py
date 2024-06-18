# 导出模型的 JSON 格式
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


print(Item.model_json_schema())
