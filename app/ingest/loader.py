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
    """读 PDF：把每一页的文字抽出来，拼成一整段。

    怎么读这个函数：
    1. 它收什么、给什么 —— 收一个文件路径，给「整段文字 + 告警清单」
    2. 中间那几个变量各装什么 —— warnings 装问题，pieces 装每页的文字
    3. 循环在重复做什么 —— 一页一页地取字
    """
    from pypdf import PdfReader

    warnings = []                    # 空列表，准备装"出了什么问题"的记录
    reader = PdfReader(str(path))    # 打开这份 PDF
    pages = reader.pages             # 所有页
    page_count = len(pages)          # 一共几页

    pieces = []                      # 准备装每一页取出来的文字

    # 一页一页处理。i 是这页的编号，从 0 开始
    for i in range(page_count):
        page = pages[i]

        # ┌──────────────────────────────────────────────────────┐
        # │ 填空 A：取出这一页的文字，存进 text                       │
        # │   提示：取文字的方法是 page.extract_text()               │
        # │        注意是 page 的方法，不是 reader 的                 │
        # └──────────────────────────────────────────────────────┘
        text = page.extract_text()

        # 抽不到字时它会给 None，兜成空字符串，免得后面崩
        if text is None:
            text = ""

        # 去掉首尾的空白和换行
        text = text.strip()

        # 只有这页真的有字，才拼进结果
        if text != "":
            pieces.append("[第" + str(i + 1) + "页]\n" + text)

    # 把每页的文字用空行连起来，变成一整段
    all_text = "\n\n".join(pieces)

    # ┌──────────────────────────────────────────────────────┐
    # │ 填空 B：判断它是不是扫描件                                │
    # │   条件：平均每页不到 20 个字                              │
    # │   平均每页字数 = 总字数 ÷ 页数                            │
    # │   把 False 换成你这个条件                                 │
    # └──────────────────────────────────────────────────────┘
    if len(all_text)/page_count<20:
        warnings.append(
            path.name + "：几乎抽不到文字（平均每页不足 20 字），"
            "很可能是扫描件或图片型 PDF，需要 OCR 才能读取"
        )

    return all_text, warnings


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
