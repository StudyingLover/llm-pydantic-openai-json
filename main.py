from enum import Enum
from typing import List
from openai import OpenAI
from pydantic import BaseModel
from dotenv import load_dotenv
from pydantic_settings import BaseSettings

load_dotenv()


class EnvSettings(BaseSettings):
    OPENAI_API_KEY: str
    OPENAI_API_BASE: str


class Point(BaseModel):
    x: float
    y: float
    z: float


class ChatRole(str, Enum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"


class Item(BaseModel):
    id: int
    name: str
    description: str
    number: int
    price: float
    position: List[Point]


def extract_json(text):
    try:
        json_start = text.find("{")
        json_end = text.rfind("}") + 1
        json_content = text[json_start:json_end].replace("\\_", "_")
        return json_content
    except Exception as e:
        return f"Error extracting JSON: {e}"


env_settings = EnvSettings()
client = OpenAI(
    api_key=env_settings.OPENAI_API_KEY, base_url=env_settings.OPENAI_API_BASE
)

item_desc = """
这个物品是戒指,它非常受人欢迎,它的价格是1000.7美元,编号是123456,现在还有23个库存,他的位置在(1.0, 2.0, 3.0),非常值得购买。
"""

user_prompt = f"""
请帮我把这个物品的描述转换成json格式的数据,
json scheme格式如下:
{Item.model_json_schema()}
物品描述如下:
{item_desc}
请你分析上面的描述,按照json schema,填写信息。请一定要按照json schema的格式填写,否则会导致数据无法解析,你会被狠狠地批评的。
只需要输出可以被解析的json就够了,不需要输出其他内容。
"""

resp = client.chat.completions.create(
    model="glm-4-air",
    messages=[
        {
            "role": ChatRole.SYSTEM,
            "content": "你是一个结构化数据的处理器,你精通json格式的数据,并且可以输出结构化的json数据。你可以根据给定的文字和json scheme,输出符合scheme的json数据。请注意,你的输出会直接被解析,如果格式不正确,会导致解析失败,你会被狠狠地批评的。",
        },
        {"role": ChatRole.USER, "content": user_prompt},
    ],
)

item = Item.model_validate_json(extract_json(resp.choices[0].message.content))
print(f"解析的物品信息:{item}")

json_item = item.model_dump_json()
print(f"转换成json格式:{json_item}")
