"""模块 4：向量索引。

自己用 numpy 实现，而不是直接上 Chroma/FAISS —— 因为这一层只有 50 行，
但它包含了你必须理解的全部东西：存储、相似度、排序、持久化。
写一遍之后再看 Chroma，你会发现"哦，它也就是这么回事"。

===== 你唯一的任务：实现 search() =====
"""

from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

import numpy as np

from app.schemas import Chunk, RetrievedChunk


class VectorStore:
    def __init__(self) -> None:
        self.vectors: np.ndarray | None = None  # (N, dim)，已归一化
        self.chunks: list[Chunk] = []

    def __len__(self) -> int:
        return len(self.chunks)

    def add(self, chunks: list[Chunk], vectors: np.ndarray) -> None:
        """追加写入。已实现。"""
        if len(chunks) != len(vectors):
            raise ValueError(f"chunk 数 {len(chunks)} 与向量数 {len(vectors)} 不一致")
        vectors = np.asarray(vectors, dtype=np.float32)
        if vectors.ndim != 2:
            raise ValueError(f"向量应为二维数组，收到 shape={vectors.shape}")
        if self.vectors is not None and self.vectors.shape[1] != vectors.shape[1]:
            raise ValueError(
                f"维度不一致：已有 {self.vectors.shape[1]}，新来 {vectors.shape[1]}。"
                "换了 embedding 模型就必须重建整个索引。"
            )
        self.vectors = vectors if self.vectors is None else np.vstack([self.vectors, vectors])
        self.chunks.extend(chunks)

    def search(self, query_vector: np.ndarray, top_k: int = 5) -> list[RetrievedChunk]:
        """检索最相似的 top_k 个片段。TODO: 你来实现。

        输入：query_vector shape=(dim,)，已归一化
        输出：list[RetrievedChunk]，按 score 从高到低

        实现提示（先自己想，卡住再看）：
        1. 空索引要直接返回 []
        2. 因为两边都归一化了，相似度 = self.vectors @ query_vector，一步得到 (N,) 的分数数组
        3. 取 top-k 不要全排序。np.argsort 是 O(N log N)，
           np.argpartition 是 O(N)，只要前 k 个时用它，再对 k 个元素排一次
           —— 这个细节是"你知道自己在写什么"的证据
        4. 用分数倒序，把 (score, chunk) 组装成 RetrievedChunk 返回
        5. 过滤掉 score < settings.min_score 的结果（配置文件里已经给了这个字段）

        跑通后自己算一下：1 万个 512 维向量，一次检索多少毫秒？
        把这个数字记下来，增量阶段要拿它和 Chroma 比。

        思考题：如果索引有 100 万条，这个实现还能用吗？瓶颈在哪？
        （答出来就能自然引出 HNSW / IVF 这些 ANN 索引）
        """
        raise NotImplementedError("实现 VectorStore.search")

    # ---------- 持久化：已实现 ----------

    def save(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        np.savez_compressed(
            path,
            vectors=self.vectors if self.vectors is not None else np.zeros((0, 0), dtype=np.float32),
        )
        # chunk 是结构化数据，用 json 存，人可读、可 diff。
        # 注意文件名要和 npz 对得上：index.npz <-> index.json
        meta_path = path.with_suffix(".json")
        meta_path.write_text(
            json.dumps([asdict(c) for c in self.chunks], ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    @classmethod
    def load(cls, path: Path) -> "VectorStore":
        if not path.exists():
            raise FileNotFoundError(f"索引不存在：{path}，先跑 python scripts/build_index.py")
        store = cls()
        data = np.load(path)
        store.vectors = data["vectors"].astype(np.float32)
        if store.vectors.size == 0:
            store.vectors = None

        meta_path = path.with_suffix(".json")
        raw = json.loads(meta_path.read_text(encoding="utf-8"))
        store.chunks = [Chunk(**item) for item in raw]
        return store
