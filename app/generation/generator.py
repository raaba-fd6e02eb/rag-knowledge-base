"""模块 6：生成。

RAG 的效果，一半在检索，另一半就在这个 prompt 上。
下面这段 system prompt 的每一句都是为了防止一种具体的失败，注释里写了原因。
"""

from __future__ import annotations

from openai import OpenAI

from app.config import settings
from app.schemas import Answer, RetrievedChunk

# 别小看这一段。删掉任何一句，你都会在真实使用中看到对应的坏结果。
SYSTEM_PROMPT = """你是一个严谨的文档问答助手，必须遵守以下规则：

1. 只能依据【参考资料】中的内容回答，不得使用你自己的知识补充或推断。
   （不写这句，模型会拿训练数据里的常识覆盖资料，答得流畅但错。）
2. 如果参考资料不足以回答问题，直接回答"根据现有资料无法回答"，并说明缺少什么信息。
   绝对不要猜测或编造。
   （不写这句，模型宁可编一个也不肯说不知道 —— 这就是幻觉。）
3. 每一个来自资料的事实性陈述后面必须标注来源编号，格式为 [1] 或 [1][3]。
   编号必须与参考资料列表中的编号严格对应。
   （不写这句，答案无法溯源，等于没有出处。）
4. 用简体中文回答，条理清晰，不要重复或复述问题本身。
5. 如果不同资料之间存在矛盾，要指出矛盾，不要自己选一个。"""


def build_context(chunks: list[RetrievedChunk]) -> str:
    """把检索结果拼成带编号的参考资料块。

    编号顺序 = chunks 的顺序，必须和 Answer.citations 保持一致，
    否则答案里的 [2] 会指向错误的内容。
    """
    blocks: list[str] = []
    for i, item in enumerate(chunks, start=1):
        source = item.chunk.metadata.get("source", "未知来源")
        page = item.chunk.metadata.get("page")
        label = f"{source}" + (f" 第{page}页" if page else "")
        blocks.append(f"[{i}] 来源：{label}\n{item.chunk.text}")
    return "\n\n".join(blocks)


class Generator:
    def __init__(self) -> None:
        if not settings.llm_api_key:
            raise RuntimeError("未配置 LLM_API_KEY，请检查 .env")
        # OpenAI 兼容接口：换 DeepSeek / 智谱 / 通义只改 base_url 和 model
        self.client = OpenAI(
            api_key=settings.llm_api_key,
            base_url=settings.llm_base_url,
        )

    def answer(self, question: str, chunks: list[RetrievedChunk]) -> Answer:
        """检索结果 + 问题 → 带出处的回答。已实现。"""
        if not chunks:
            # 检索为空时不要调模型 —— 没有资料还调模型，它一定会编。
            # 这是"最小化幻觉面"的工程手段：能用代码拦住的，不要交给 prompt。
            return Answer(
                text="根据现有资料无法回答，知识库中没有检索到相关内容。",
                citations=[],
            )

        user_prompt = f"【参考资料】\n{build_context(chunks)}\n\n【问题】\n{question}"

        resp = self.client.chat.completions.create(
            model=settings.llm_model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            temperature=settings.llm_temperature,
        )
        text = (resp.choices[0].message.content or "").strip()
        return Answer(text=text, citations=chunks)

    # TODO（增量阶段）：实现流式输出。
    # 思路：把 create(...) 换成 create(..., stream=True)，遍历 chunk，
    # 每次取 chunk.choices[0].delta.content，非空就 yield 出去。
    # 接口层用 StreamingResponse 包一层即可。
    # 为什么重要：首字延迟从 3 秒降到 0.5 秒，体验差距巨大，面试也常问。
