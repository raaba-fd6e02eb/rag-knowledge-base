"""D1 冒烟测试：验证 .env 配对了、网络通了、模型名没错。

用法：
    python scripts/smoke_llm.py

这一步单独做，是为了把"配置问题"和"代码问题"分开。
否则你写业务代码时遇到报错，会分不清是逻辑错了还是 key 错了 —— 排查成本翻倍。
"""

import sys
from pathlib import Path

# 直接运行 `python scripts/xxx.py` 时，Python 只把 scripts/ 放进模块搜索路径，
# 项目根目录下的 app 包就找不到。这里手动把根目录插到最前面。
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.config import settings
from openai import OpenAI


def main() -> None:
    print(f"base_url = {settings.llm_base_url}")
    print(f"model    = {settings.llm_model}")
    print(f"api_key  = {settings.llm_api_key[:6]}...{settings.llm_api_key[-4:] if len(settings.llm_api_key) > 10 else ''}")

    if not settings.llm_api_key or settings.llm_api_key.startswith("sk-your-key"):
        raise SystemExit("还没填 LLM_API_KEY，去改 .env")

    client = OpenAI(api_key=settings.llm_api_key, base_url=settings.llm_base_url)
    resp = client.chat.completions.create(
        model=settings.llm_model,
        messages=[{"role": "user", "content": "用一句话说明什么是向量检索。"}],
        temperature=0,
    )
    print("\n--- 模型回复 ---")
    print(resp.choices[0].message.content)
    print("\nLLM 链路正常。")


if __name__ == "__main__":
    main()
