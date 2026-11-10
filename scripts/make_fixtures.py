"""生成测试用文档（PDF / DOCX / TXT 各一份）。

为什么需要这个脚本：
真实项目里，你不会拿"随便一个 PDF"去调试解析器 —— 你需要**内容已知**的材料，
才能判断"抽出来的文字对不对"。这三份文档的内容是编的（虚构的公司制度），
但结构是真实的：PDF 有分页、DOCX 有标题层级、TXT 是裸文本。

用法：
    python scripts/make_fixtures.py

生成到 data/docs/，这些文件已被 .gitignore 挡住，不会进仓库。
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

DOCS_DIR = ROOT / "data" / "docs"
FONT_PATH = Path("C:/Windows/Fonts/simhei.ttf")

# 三份文档的内容刻意互不重叠，方便后面对比检索效果
PAGES = [
    (
        "一、年假制度",
        [
            "公司全体正式员工享有带薪年假。年假天数按累计工龄计算："
            "工龄满一年不满十年的，每年 5 天；满十年不满二十年的，每年 10 天；"
            "满二十年的，每年 15 天。",
            "年假以自然年为周期计算，当年未休完的部分最多结转 5 天至次年，"
            "结转部分须在次年第一季度内使用完毕，逾期作废。",
            "新入职员工当年年假按在职月份折算，不足一天的部分不计。"
            "离职时未休年假按日工资的 300% 折算补偿。",
        ],
    ),
    (
        "二、费用报销流程",
        [
            "员工因公产生的费用，应在费用发生后 3 个工作日内提交报销申请，"
            "超过 30 天未提交的，原则上不予受理。",
            "报销须提供合规发票原件，发票抬头须为公司全称，"
            "并注明税号。餐饮类发票还需附消费明细与参与人名单。",
            "单笔金额超过 5000 元的支出，须在发生前提交预算申请，"
            "经部门负责人与财务双重审批后方可执行。",
        ],
    ),
    (
        "三、考勤与远程办公",
        [
            "公司实行弹性工作制，核心工作时间为上午 10:00 至下午 16:00，"
            "员工可在 9:00 至 10:00 之间自行选择上班时间。",
            "每周可申请不超过 2 天的远程办公，需提前一个工作日在系统中提交申请，"
            "由直属主管审批。远程办公期间须保持通讯畅通。",
            "迟到超过 30 分钟按事假半天计算。当月累计迟到 3 次以上，"
            "扣发当月全勤奖。",
        ],
    ),
]


def make_pdf() -> Path:
    """生成一份带文字层的中文 PDF —— 用来和扫描件做对照。"""
    from fpdf import FPDF

    pdf = FPDF(format="A4")
    pdf.set_auto_page_break(auto=True, margin=20)
    pdf.add_font("SimHei", "", str(FONT_PATH))

    for title, paragraphs in PAGES:
        pdf.add_page()
        pdf.set_font("SimHei", size=18)
        pdf.cell(0, 12, "员工手册（测试样例）", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(4)
        pdf.set_font("SimHei", size=14)
        pdf.cell(0, 10, title, new_x="LMARGIN", new_y="NEXT")
        pdf.ln(2)

        pdf.set_font("SimHei", size=11)
        for para in paragraphs:
            pdf.multi_cell(0, 7, para)
            pdf.ln(2)

    out = DOCS_DIR / "员工手册.pdf"
    pdf.output(str(out))
    return out


def make_docx() -> Path:
    """生成一份带标题层级的 Word 文档。"""
    from docx import Document

    doc = Document()
    doc.add_heading("产品需求说明（测试样例）", level=1)
    doc.add_paragraph(
        "本文档描述一个内部知识库问答工具的第一版需求，用于验证解析器对 Word 标题层级的处理。"
    )

    doc.add_heading("1. 背景", level=2)
    doc.add_paragraph(
        "客服团队每天要回答大量重复问题，答案散落在数十份 Word 和 PDF 文档里，"
        "检索靠人工翻找，平均响应时间超过 8 分钟。"
    )

    doc.add_heading("2. 功能范围", level=2)
    for item in [
        "支持上传 PDF、Word、纯文本三类文件",
        "对上传内容建立索引，供自然语言检索",
        "回答必须附带原文出处，便于人工核对",
        "无法从文档中找到答案时，明确回复“未找到”，不得编造",
    ]:
        doc.add_paragraph(item, style="List Bullet")

    doc.add_heading("3. 非目标", level=2)
    doc.add_paragraph("第一版不做多轮对话、不做权限控制、不做文档在线编辑。")

    out = DOCS_DIR / "产品需求说明.docx"
    doc.save(str(out))
    return out


def make_txt() -> Path:
    """生成一份纯文本 —— 最简单的格式，用来验证基线。"""
    content = """运维值班备忘录（测试样例）

一、值班时间
工作日 18:00 至次日 09:00，周末全天。值班人员需在 30 分钟内响应告警。

二、常见故障处理
1. 磁盘使用率超过 85%：先清理日志目录，保留最近 7 天。
2. 数据库连接池耗尽：检查是否有慢查询，必要时重启应用实例。
3. 接口大面积超时：先看下游依赖状态，再排查自身线程池。

三、升级与回滚
发布前必须准备回滚包。回滚窗口为发布后 30 分钟内，超时需走变更审批。

四、交接要求
交接必须写清未闭环的告警、正在进行的变更、以及次日待办事项。
"""
    out = DOCS_DIR / "运维值班备忘录.txt"
    out.write_text(content, encoding="utf-8")
    return out


def main() -> None:
    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    for maker in (make_pdf, make_docx, make_txt):
        path = maker()
        print(f"生成 {path.name}  ({path.stat().st_size / 1024:.1f} KB)")


if __name__ == "__main__":
    main()
