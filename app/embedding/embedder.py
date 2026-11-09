"""模块 3：向量化。

这是整条链路里唯一"没有太多可写"的模块 —— 它就是把文本交给模型换成向量。
但有两个细节，90% 的教程没讲清楚，而面试官恰好爱问。
"""

from __future__ import annotations

import numpy as np
from sentence_transformers import SentenceTransformer

from app.config import settings

# BGE 中文模型官方推荐的检索指令前缀。
# 原因：BGE 训练时 query 侧带了这句指令、doc 侧没带，模型学的是"带指令的 query"
# 去匹配"不带指令的 doc"。推理时不一致，效果会掉。
# 这就是"训练/推理一致性"的一个具体例子，面试可以讲。
QUERY_INSTRUCTION = "为这个句子生成表示以用于检索相关文章："


class Embedder:
    """文本 → 归一化向量。

    为什么必须归一化：
    - 归一化后向量长度为 1，此时 点积 == 余弦相似度，检索就退化成一次矩阵乘法，
      这是向量检索能做到毫秒级的根本原因
    - 不归一化的话，长文本的向量模长天然更大，点积会被"长度"污染，排序就歪了

    为什么 doc 和 query 必须用同一个模型：
    不同模型训练出来的向量空间毫无关系，跨模型算相似度等于随机数。
    这是新手最常犯、也最难自查的错。
    """

    def __init__(
        self,
        model_name: str | None = None,
        batch_size: int | None = None,
    ) -> None:
        self.model_name = model_name or settings.embedding_model
        self.batch_size = batch_size or settings.embedding_batch_size
        # 首次运行会下载模型（bge-small-zh 约 100MB），之后走本地缓存
        self.model = SentenceTransformer(self.model_name)

    @property
    def dim(self) -> int:
        """向量维度。bge-small-zh-v1.5 是 512。存索引时要记下来做校验。"""
        return int(self.model.get_sentence_embedding_dimension())

    def encode_documents(self, texts: list[str]) -> np.ndarray:
        """批量编码文档片段，返回 (N, dim) 的 float32 数组。"""
        return self.model.encode(
            texts,
            batch_size=self.batch_size,
            normalize_embeddings=True,
            show_progress_bar=len(texts) > 64,
            convert_to_numpy=True,
        ).astype(np.float32)

    def encode_query(self, query: str) -> np.ndarray:
        """编码单个问题，返回 (dim,) 的向量。

        注意这里加了 QUERY_INSTRUCTION，而 encode_documents 没有。
        不对称是故意的，不是 bug。
        """
        vec = self.model.encode(
            [QUERY_INSTRUCTION + query],
            normalize_embeddings=True,
            convert_to_numpy=True,
        )
        return vec[0].astype(np.float32)
