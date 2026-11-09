"""命令行入口。开发期用它验证整条链路，比每次都起服务快得多。

用法：
    python -m app.cli "员工年假多少天？"
    python -m app.cli "报销流程是什么" --top-k 8
"""

from __future__ import annotations

import argparse

from app.config import settings
from app.embedding.embedder import Embedder
from app.generation.generator import Generator
from app.retrieval.retriever import Retriever
from app.store.vector_store import VectorStore


def main() -> None:
    parser = argparse.ArgumentParser(description="知识库问答")
    parser.add_argument("question", help="你的问题")
    parser.add_argument("--top-k", type=int, default=settings.top_k)
    parser.add_argument("--show-context", action="store_true", help="打印检索到的原文片段")
    args = parser.parse_args()

    store = VectorStore.load(settings.index_file)
    embedder = Embedder()
    retriever = Retriever(store, embedder)
    generator = Generator()

    chunks = retriever.retrieve(args.question, top_k=args.top_k)

    if args.show_context:
        print(f"\n--- 检索到 {len(chunks)} 个片段 ---")
        for i, c in enumerate(chunks, 1):
            print(f"[{i}] score={c.score:.4f} source={c.chunk.metadata.get('source')}")
            print(f"    {c.chunk.text[:120]}...")
        print("-" * 40)

    result = generator.answer(args.question, chunks)
    print(f"\n{result.text}\n")

    if result.citations:
        print("出处：")
        for i, c in enumerate(result.citations, 1):
            meta = c.chunk.metadata
            print(f"  [{i}] {meta.get('source', '未知')} · 相似度 {c.score:.3f}")


if __name__ == "__main__":
    main()
