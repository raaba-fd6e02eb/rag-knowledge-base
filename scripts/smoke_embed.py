"""D1 冒烟测试：验证 embedding 模型能下载、能编码、维度对得上。

用法：
    python scripts/smoke_embed.py

首次运行会下载 bge-small-zh-v1.5（约 100MB），之后走本地缓存。
如果卡在下载上，先确认网络；如果报 torch 安装问题，见 README 的环境说明。
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np

from app.embedding.embedder import Embedder


def main() -> None:
    print("加载模型（首次会下载）...")
    emb = Embedder()

    query = "年假有几天"
    docs = [
        "员工每年享有 5 天带薪年假。",
        "报销需要提交发票原件和审批单。",
        "公司食堂中午 11:30 开餐。",
    ]

    q_vec = emb.encode_query(query)
    d_vecs = emb.encode_documents(docs)
    scores = d_vecs @ q_vec

    print(f"\n向量维度 = {emb.dim}（bge-small-zh-v1.5 应为 512）")
    print(f"余弦相似度 = {np.round(scores, 4)}")
    print(f"最相关 = {docs[int(np.argmax(scores))]}")
    print("\n若第一句分数最高，说明模型和归一化都正常。")
    print("如果三条分数都差不多（比如都在 0.6 附近），先别慌 —— 短句之间本就相似，")
    print("等接上真实文档再看。但如果你忘了 normalize，分数会出现 >1 或异常接近。")


if __name__ == "__main__":
    main()
