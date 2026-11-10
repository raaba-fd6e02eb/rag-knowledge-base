"""把流水线每一步"打印出来"，让你看见数据长什么样。

不用理解代码，只看输出：同一个文件，在五个阶段分别是五种形态。
每一步后面都标了「对应哪个文件」，想深究再去看那里。
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.chunking.splitter import split_text
from app.ingest.loader import load_file

TARGET = Path("data/docs/运维值班备忘录.txt")

print("=" * 58)
print("① 磁盘上的一个文件      【对应：你的文件夹 data/docs/】")
print("=" * 58)
print("   文件名:", TARGET.name)
print("   大小:", TARGET.stat().st_size, "字节")
print("   形态：一堆字节，程序不知道里面是什么")

print()
print("=" * 58)
print("② 读成一段文字（字符串）  【对应：_read_text()】")
print("=" * 58)
raw = TARGET.read_text(encoding="utf-8")
print("   类型:", type(raw).__name__)
print("   长度:", len(raw), "个字符")
print("   开头:", raw[:28].replace("\n", " ⏎ "))
print("   形态：一整段文字，还是没有结构")

print()
print("=" * 58)
print("③ 装进 Document 对象     【对应：load_file() + schemas.py】")
print("=" * 58)
doc = load_file(TARGET)
print("   类型:", type(doc).__name__)
print("   有哪几个格子:", list(doc.__dict__.keys()))
print("   doc_id  =", doc.doc_id, "  ← 给这篇文档的编号")
print("   text    =", len(doc.text), "个字符  ← 就是上一步那段文字")
print("   metadata=", doc.metadata)
print("   形态：文字被装进一个盒子，盒子上贴了标签")

print()
print("=" * 58)
print("④ 切成 Chunk 列表        【对应：split_text()】")
print("=" * 58)
chunks = split_text(doc, chunk_size=100, overlap=50)
print("   切成了", len(chunks), "块")
for i, c in enumerate(chunks):
    head = c.text[:26].replace("\n", " ⏎ ")
    print(f"   第{i+1}块: {len(c.text):>3} 字  start={c.start:<4} end={c.end:<4} 开头「{head}…」")
print("   形态：一个列表，里面每个元素是一个小盒子")
print("   start/end 记的是「这一块在全文里的位置」，用来回头找原文")

print()
print("=" * 58)
print("⑤ 变成一串数字（向量）    【对应：embedder.py】")
print("=" * 58)
print("   正在加载模型，约 5 秒…")
from app.embedding.embedder import Embedder

embedder = Embedder()
vec = embedder.encode_documents([chunks[0].text])[0]
print("   类型:", type(vec).__name__)
print("   长度:", len(vec), "个数字（这就是 512 维）")
print("   前 6 个数字:", [round(float(x), 4) for x in vec[:6]])
print("   形态：一段文字 → 512 个数字。模型认为，意思相近的文字，这 512 个数字也相近")
print()
print("整条链路到此为止。剩下的事，就是拿这串数字去比大小。")
