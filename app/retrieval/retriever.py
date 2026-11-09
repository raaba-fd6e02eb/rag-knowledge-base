"""模块 5：检索。

这一层很薄，但它承担了一个容易被忽视的责任：
把"用户的一句话"翻译成"检索器能理解的东西"。

之所以还要单独一层而不是在 API 里直接调 store.search，
是因为后面增量阶段要做混合检索（向量 + BM25 + rerank），
那时你只需要改这个文件，上层一行都不用动。这就是分层的价值。
"""

from __future__ import annotations

from app.embedding.embedder import Embedder
from app.schemas import RetrievedChunk
from app.store.vector_store import VectorStore


class Retriever:
    def __init__(self, store: VectorStore, embedder: Embedder) -> None:
        self.store = store
        self.embedder = embedder

    def retrieve(self, query: str, top_k: int = 5) -> list[RetrievedChunk]:
        """问题 → 相关片段。已实现。

        只有三步，但每一步都是坑：
        1. query 走 encode_query（带指令前缀），不是 encode_documents
        2. 用同一个 embedder 实例，保证模型一致
        3. 检索完按分数降序 —— search 里已经做了

        TODO（增量阶段）：加一个相似度阈值。
        现在的结果永远返回 top_k 条，哪怕全是无关内容。
        用户问一个知识库里根本没有的问题时，模型会硬凑答案 —— 这是幻觉的头号来源。
        """
        if not query.strip():
            return []
        query_vector = self.embedder.encode_query(query)
        return self.store.search(query_vector, top_k=top_k)
