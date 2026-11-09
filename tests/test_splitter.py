"""分块器测试。

这几个用例已经写好了，先跑一遍看它们通过：

    pytest tests/ -v

然后你的任务是：给 D3 改进后的分块器补测试。
每修一个 bug 就补一个用例 —— 这叫回归测试，是"项目"和"作业"的分界线。
"""

import pytest

from app.chunking.splitter import split_text
from app.schemas import Document


def make_doc(text: str) -> Document:
    return Document(doc_id="test", text=text, metadata={"source": "test.txt"})


def test_short_text_single_chunk():
    """短文本应该只有一个块，不该被硬切。"""
    chunks = split_text(make_doc("这是一段很短的文本。"), chunk_size=100, overlap=10)
    assert len(chunks) == 1
    assert chunks[0].text == "这是一段很短的文本。"


def test_long_text_multiple_chunks():
    """长文本要切成多块，且每块不超过 chunk_size。"""
    doc = make_doc("字" * 1000)
    chunks = split_text(doc, chunk_size=100, overlap=10)
    assert len(chunks) > 1
    assert all(len(c.text) <= 100 for c in chunks)


def test_overlap_creates_shared_content():
    """相邻块必须有重叠，否则边界上的句子会被切断丢失。"""
    doc = make_doc("0123456789" * 20)  # 200 字
    chunks = split_text(doc, chunk_size=100, overlap=10)
    assert chunks[0].end > chunks[1].start


def test_chunk_ids_unique():
    doc = make_doc("内容" * 500)
    chunks = split_text(doc, chunk_size=100, overlap=10)
    ids = [c.chunk_id for c in chunks]
    assert len(ids) == len(set(ids))


def test_invalid_overlap_raises():
    """overlap >= chunk_size 会死循环，必须挡住。"""
    with pytest.raises(ValueError):
        split_text(make_doc("abc" * 100), chunk_size=50, overlap=50)


# ============ TODO: D3 改进分块器后，补充这些用例 ============
#
# def test_no_chunk_ends_mid_sentence():
#     """每个块的结尾应该落在句末标点上（或文本末尾）。"""
#
# def test_chunks_cover_entire_text():
#     """所有块拼起来（考虑重叠）应该覆盖原文，不能丢字。"""
