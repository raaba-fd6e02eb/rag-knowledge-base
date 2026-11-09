"""模块 1：文档接入。

职责：把任意格式的文件变成统一的 Document 对象。
这一层是整条链路的地基 —— 解析出错，后面全白搭。

已给你写好的：TXT / Markdown / DOCX
留给你写的：PDF（见文件末尾的 TODO）
"""

from __future__ import annotations

import hashlib
from pathlib import Path

from app.schemas import Document

SUPPORTED_SUFFIXES = {".txt", ".md", ".pdf", ".docx"}


def _make_doc_id(path: Path, root: Path | None) -> str:
    """用相对路径做稳定 ID。

    为什么不用文件名：不同目录下可能有同名文件，会撞。
    为什么用 md5 截断而不是自增：内容换了位置不变，ID 就不变，索引可以增量更新。
    """
    rel = path.relative_to(root).as_posix() if root else path.name
    return hashlib.md5(rel.encode("utf-8")).hexdigest()[:12]


def _read_text(path: Path) -> tuple[str, list[str]]:
    """读纯文本，返回 (内容, 告警列表)。

    中文文档常见 GBK/GB18030 编码，直接 utf-8 读会炸。
    这里做一次降级尝试 —— 这是真实项目里必须处理的事。
    """
    warnings: list[str] = []
    for enc in ("utf-8", "utf-8-sig", "gb18030"):
        try:
            return path.read_text(encoding=enc), warnings
        except UnicodeDecodeError:
            continue
    warnings.append(f"{path.name}: 编码无法识别，已按 utf-8 忽略错误读取")
    return path.read_text(encoding="utf-8", errors="ignore"), warnings


def _read_docx(path: Path) -> tuple[str, list[str]]:
    """读 Word。只取段落文本，表格后面再说。"""
    from docx import Document as DocxDocument

    doc = DocxDocument(str(path))
    parts: list[str] = [p.text for p in doc.paragraphs if p.text.strip()]
    return "\n".join(parts), []


def _read_pdf(path: Path) -> tuple[str, list[str]]:
    """读 PDF。TODO: 你来实现。

    提示（按顺序想，别一次全做）：
    1. 用 pypdf.PdfReader 打开，遍历 pages，每页 extract_text()
    2. 页之间用 "\\n\\n" 连接 —— 为什么？因为分块器把换行当段落边界
    3. 页码信息很有价值：把 {"pages": n} 塞进 metadata，回答时可以标"第 3 页"
    4. 关键判断：如果全文字符数 < 页数 * 20，几乎可以断定是扫描版
       （图片型 PDF 抽不出文字），此时要往 warnings 里加一条，不要静默返回空串
       —— 静默失败是工程里最贵的 bug

    思考题：扫描版 PDF 怎么处理？（提示：OCR，但那是另一个故事，先记录告警即可）
    """
    raise NotImplementedError("实现 _read_pdf")


def load_file(path: Path, root: Path | None = None) -> Document:
    """加载单个文件。

    注意这里没有用 if/elif 堆分支，而是查表 + 分派 —— 加格式时只改表，不动流程。
    """
    suffix = path.suffix.lower()
    if suffix not in SUPPORTED_SUFFIXES:
        raise ValueError(f"不支持的格式: {suffix}")

    readers = {
        ".txt": _read_text,
        ".md": _read_text,
        ".pdf": _read_pdf,
        ".docx": _read_docx,
    }
    text, warnings = readers[suffix](path)

    metadata = {
        "source": path.name,
        "suffix": suffix,
        "chars": len(text),
    }
    if warnings:
        metadata["warnings"] = warnings

    return Document(doc_id=_make_doc_id(path, root), text=text, metadata=metadata)


def load_dir(docs_dir: Path) -> list[Document]:
    """加载目录下所有支持的文档。

    单个文件失败不应该让整批失败 —— 收集错误，继续跑，
    最后统一报告。这是批处理的通用原则。
    """
    docs: list[Document] = []
    for path in sorted(docs_dir.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in SUPPORTED_SUFFIXES:
            continue
        try:
            docs.append(load_file(path, root=docs_dir))
        except Exception as exc:  # noqa: BLE001
            print(f"[跳过] {path.name}: {exc}")
    return docs
