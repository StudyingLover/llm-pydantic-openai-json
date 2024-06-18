# pydantic+openai+json: 控制大模型输出的最佳范式

调用大模型已经是如今做 ai 项目习以为常的工作的，但是大模型的输出很多时候是不可控的，我们又需要使用大模型去做各种下游任务，实现可控可解析的输出。我们探索了一种和 python 开发可以紧密合作的开发方法。

大模型输出是按照 token 逐个预测然后解码成文本，就跟说话一样，但是有的时候我们需要用大模型做一些垂直领域的工作，例如给定一段文本，我们想知道他属于正向的还是负向的？最简单的方法就是给大模型写一段 prompt 告诉大模型请你告诉我这段文本是正向的还是负向的，只输出正向的还是负向的不要输出多余的东西。这种方法其实有两个问题

1. 大模型有的时候挺犟的，你告诉他不要输出多余的他会说好的我不会输出多余的，这段文本的正向的/负向的
2. 如果我们希望同时有多个输出，例如正向的还是负向的，以及对应的分数，这样的输出会很麻烦

所以，我们需要一种格式，大模型很擅长写，我们解析起来很方便，我们使用 python 开发的话也很方便，有没有呢？还真有，python 有一个库叫 pydantic，可以实现类->json->类的转换。

这里补充一个知识叫做 json scheme 是一种基于 JSON 的格式，用来描述 JSON 数据的结构。它提供了一种声明性的方式来验证 JSON 数据是否符合某种结构，这对于数据交换、数据存储以及 API 的交互等方面都非常有用。一个 JSON Schema 本身也是一个 JSON 对象，它定义了一系列的规则，这些规则说明了 JSON 数据应该满足的条件。例如，它可以指定一个 JSON 对象中必须包含哪些属性，这些属性的数据类型是什么，是否有默认值，以及其他一些约束条件。下面是一个 json scheme 的例子。

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "properties": {
    "name": {
      "type": "string"
    },
    "age": {
      "type": "integer",
      "minimum": 0
    },
    "email": {
      "type": "string",
      "format": "email"
    }
  },
  "required": ["name", "age"]
}
```

ok，那怎么得到一个 json scheme，我们可以给描述或者一段 json 让大模型写，但是不够优雅，每次需要打开一个网页写写写然后复制粘贴回来。一种更优雅的方式是用 pydantic 导出，下面是一个例子, 定义一个`Item` 类然后使用`Item.model_json_scheme()`可以导出这个类的 json scheme 描述

```python
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
```

他的输出是

```json
{
  "$defs": {
    "Point": {
      "properties": {
        "x": {
          "title": "X",
          "type": "number"
        },
        "y": {
          "title": "Y",
          "type": "number"
        },
        "z": {
          "title": "Z",
          "type": "number"
        }
      },
      "required": ["x", "y", "z"],
      "title": "Point",
      "type": "object"
    }
  },
  "properties": {
    "id": {
      "title": "Id",
      "type": "integer"
    },
    "name": {
      "title": "Name",
      "type": "string"
    },
    "description": {
      "title": "Description",
      "type": "string"
    },
    "number": {
      "title": "Number",
      "type": "integer"
    },
    "price": {
      "title": "Price",
      "type": "number"
    },
    "position": {
      "items": {
        "$ref": "#/$defs/Point"
      },
      "title": "Position",
      "type": "array"
    }
  },
  "required": ["id", "name", "description", "number", "price", "position"],
  "title": "Item",
  "type": "object"
}
```

通过这种方式我们可以解决前面提出的第二个问题，将我们需要的多个答案写成一个 pydantic 的类，然后将 json scheme 以及问题描述作为 prompt 给大模型例如下面的这个 prompt

```python
user_prompt = f"""
请帮我把这个物品的描述转换成json格式的数据，
json scheme格式如下：
{Item.model_json_schema()}
物品描述如下：
{item_desc}
请你分析上面的描述，按照json schema，填写信息。请一定要按照json schema的格式填写，否则会导致数据无法解析，你会被狠狠地批评的。
只需要输出可以被解析的json就够了，不需要输出其他内容。
"""

```

那第一个问题怎么解决呢？首先是大模型不止输出 json 还会输出一堆废话，我们可以观察到 json 前后是大括号，这个符号是一般不会出现的，所有我们可以从输出的字符串前后开始遍历，分别找到一个前大括号和一个后大括号，然后舍弃掉无关的

```python
def extract_json(text):
    try:
        json_start = text.find("{")
        json_end = text.rfind("}") + 1
        json_content = text[json_start:json_end].replace("\\_", "_")
        return json_content
    except Exception as e:
        return f"Error extracting JSON: {e}"

```

获取到 json 之后，使用`Item.model_validate_json(json字符串)` 来构造一个实体类

当然我们也可以定义一个对象然后将他转换成 json

```python
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

```

输出是

```Plain Text
{"id":1,"name":"example","description":"example description","number":1,"price":1.0,"position":[{"x":1.0,"y":2.0,"z":3.0}]}
```

下面我给出了一个完整的例子，使用质谱的 glm-4-air 模型，解析一个物体的描述

```python
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
这个物品是戒指，它非常受人欢迎，它的价格是1000.7美元，编号是123456，现在还有23个库存，他的位置在(1.0, 2.0, 3.0)，非常值得购买。
"""

user_prompt = f"""
请帮我把这个物品的描述转换成json格式的数据，
json scheme格式如下：
{Item.model_json_schema()}
物品描述如下：
{item_desc}
请你分析上面的描述，按照json schema，填写信息。请一定要按照json schema的格式填写，否则会导致数据无法解析，你会被狠狠地批评的。
只需要输出可以被解析的json就够了，不需要输出其他内容。
"""

resp = client.chat.completions.create(
    model="glm-4-air",
    messages=[
        {
            "role": ChatRole.SYSTEM,
            "content": "你是一个结构化数据的处理器，你精通json格式的数据，并且可以输出结构化的json数据。你可以根据给定的文字和json scheme，输出符合scheme的json数据。请注意，你的输出会直接被解析，如果格式不正确，会导致解析失败，你会被狠狠地批评的。",
        },
        {"role": ChatRole.USER, "content": user_prompt},
    ],
)

item = Item.model_validate_json(extract_json(resp.choices[0].message.content))
print(f"解析的物品信息：{item}")

json_item = item.model_dump_json()
print(f"转换成json格式：{json_item}")

```

输出是

```Plain Text
解析的物品信息：id=123456 name='戒指' description='这个物品是戒指，它非常受人欢迎，它的价格是1000.7美元，编号是123456，现在还有23个库存，他的位置在(1.0, 2.0, 3.0)，非常值得购买。' number=23 price=1000.7 position=[Point(x=1.0, y=2.0, z=3.0)]
转换成json格式：{"id":123456,"name":"戒指","description":"这个物品是戒指，它非常受人欢迎，它的价格是1000.7美元，编号是123456，现在还有23个库存，他的位置在(1.0, 2.0, 3.0)，非常值得购买。","number":23,"price":1000.7,"position":[{"x":1.0,"y":2.0,"z":3.0}]}
```
