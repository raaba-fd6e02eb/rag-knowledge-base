"""离线建库脚本：文档 → 分块 → 向量 → 索引落盘。

这个脚本是幂等的 —— 每次全量重建。数据量小的时候这是最省心的做法。
（增量更新留到 API 的 /documents 接口去实现，那才需要想幂等和并发。）
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.chunking.splitter import split_text
from app.config import settings
from app.embedding.embedder import Embedder
from app.ingest.loader import load_dir
from app.schemas import Chunk
from app.store.vector_store import VectorStore


def main() -> None:
    t0 = time.perf_counter()

    docs_dir = settings.docs_dir
    if not docs_dir.exists():
        raise SystemExit(f"文档目录不存在：{docs_dir}")

    print(f"[1/4] 读取文档：{docs_dir}")
    docs = load_dir(docs_dir)
    if not docs:
        raise SystemExit("没读到任何文档。把 PDF/Word/TXT 放进 data/docs/ 再试。")
    print(f"      {len(docs)} 篇")

    for d in docs:
        if warn := d.metadata.get("warnings"):
            print(f"      [告警] {d.metadata['source']}: {warn}")
        if not d.text.strip():
            print(f"      [空文档] {d.metadata['source']} 解析结果为空，检查是否为扫描版")

    print(f"[2/4] 分块：size={settings.chunk_size} overlap={settings.chunk_overlap}")
    chunks: list[Chunk] = []
    for doc in docs:
        chunks.extend(
            split_text(doc, settings.chunk_size, settings.chunk_overlap)
        )
    print(f"      {len(chunks)} 个片段，平均 {sum(len(c.text) for c in chunks) // max(len(chunks), 1)} 字")

    print(f"[3/4] 向量化：{settings.embedding_model}")
    embedder = Embedder()
    vectors = embedder.encode_documents([c.text for c in chunks])
    print(f"      shape={vectors.shape}")

    print("[4/4] 写入索引")
    store = VectorStore()
    store.add(chunks, vectors)
    store.save(settings.index_file)
    print(f"      已保存 → {settings.index_file}")

    print(f"\n完成，耗时 {time.perf_counter() - t0:.1f}s")
    print('试试：python -m app.cli "你的问题" --show-context')


if __name__ == "__main__":
    main()
