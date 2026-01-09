# segments.py
from dataclasses import dataclass
from typing import List

@dataclass
class Segment:
    header_chain: List[str]  # 例如 ["# 总标题", "## 第一章", "### 第一条"]
    text: str                # 该标题到下一个标题之间的正文（不含子标题行本身）
