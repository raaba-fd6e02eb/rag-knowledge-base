"""单独测一下 PDF 解析：只看这一份文件，别被整条流水线干扰。

用法：
    python scripts/probe_pdf.py

它会把 data/docs 里所有 PDF 挨个读一遍，打印「抽到多少字 + 有没有告警」。
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.ingest.loader import load_file

docs_dir = Path("data/docs")
pdf_files = sorted(docs_dir.glob("*.pdf"))

if not pdf_files:
    print("data/docs 里没有 PDF")
    sys.exit(0)

for path in pdf_files:
    print("=" * 50)
    print("文件:", path.name)
    doc = load_file(path)

    print("抽到字数:", len(doc.text))
    print("开头 40 字:", doc.text[:40].replace("\n", " ⏎ "))

    got_warnings = doc.metadata.get("warnings")
    if got_warnings:
        for one in got_warnings:
            print("告警:", one)
    else:
        print("告警: 无")
