"""模块 2：分块器。

为什么必须分块：embedding 模型有输入长度上限，而且一整篇文档压成一个向量，
语义会被"平均掉"，检索精度极差。分块就是确定"检索的最小语义单位"。

这里先给你一个能跑的笨版本（固定窗口），D3 的任务是把它改好。
"""

from __future__ import annotations

from app.schemas import Chunk, Document


def split_text(
    doc: Document,
    chunk_size: int = 500,
    overlap: int = 80,
) -> list[Chunk]:
    """把 Document 切成若干 Chunk。

    ===== 当前版本：固定窗口（能跑，但烂） =====
    每 chunk_size 个字符切一刀，相邻块重叠 overlap 个字符。

    它的问题（D3 要解决的）：
    - 在句子中间切断，一个 chunk 前半句讲 A、后半句讲 B，语义污染
    - 表格被切得七零八落
    - 标题和正文被切开，chunk 失去上下文

    改进方向（按性价比排序）：
    1. 优先在句末标点（。！？；\\n）处切 —— 改动最小，收益最大
    2. 段落优先：先按空行分段，段落超长再按句子切
    3. 带上标题：每个 chunk 前面拼上所在章节标题，让 chunk 自带上下文
    4. 相邻块 overlap 是为了不让关键句正好落在边界上被切断 —— 但 overlap 太大会让
       检索结果里出现大量重复内容，挤占 top-k 名额
    """
    if chunk_size <= 0:
        raise ValueError("chunk_size 必须为正")
    if overlap < 0:
        raise ValueError("overlap 不能为负")
    if overlap >= chunk_size:
        # 这个校验很关键：不校验的话 while 循环步长为 0 或负数，直接死循环卡死
        raise ValueError("overlap 必须小于 chunk_size，否则会死循环")

    text = doc.text
    chunks: list[Chunk] = []
    step = chunk_size - overlap

    start = 0
    index = 0
    while start < len(text):
        end = min(start + chunk_size, len(text))
        piece = text[start:end].strip()
        if piece:
            chunks.append(
                Chunk(
                    chunk_id=f"{doc.doc_id}:{index}",
                    doc_id=doc.doc_id,
                    text=piece,
                    start=start,
                    end=end,
                    metadata={**doc.metadata, "chunk_index": index},
                )
            )
            index += 1
        if end >= len(text):
            break
        start += step

    return chunks
