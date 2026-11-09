"""数据契约。

整条流水线的传递物只有这三种对象。先把它们定清楚，
后面每个模块的输入输出就都不用猜了。

为什么用 dataclass 而不是 pydantic BaseModel：
dataclass 更轻、更"纯数据"，适合在模块间流转；
pydantic 留给 API 层做校验（app/api/main.py 里再定义）。
两者职责分开，是一个可以讲的设计取舍。
"""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Document:
    """一篇原始文档，解析后的结果。"""

    doc_id: str                      # 稳定唯一标识，建议用文件相对路径的 hash
    text: str                        # 全文纯文本
    metadata: dict[str, Any] = field(default_factory=dict)
    # metadata 里至少放：source（文件名）、suffix（扩展名）
    # 可选：pages（页数）、warnings（解析过程中的告警）


@dataclass
class Chunk:
    """检索的最小单位。"""

    chunk_id: str                    # 建议 f"{doc_id}:{index}"
    doc_id: str
    text: str
    start: int                       # 在 Document.text 中的起始偏移，用于溯源
    end: int
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class RetrievedChunk:
    """带分数的检索结果。"""

    chunk: Chunk
    score: float                     # 余弦相似度，越大越相关


@dataclass
class Answer:
    """最终回答。"""

    text: str
    citations: list[RetrievedChunk] = field(default_factory=list)
    # citations 的顺序 = 答案里 [1] [2] 的编号顺序
