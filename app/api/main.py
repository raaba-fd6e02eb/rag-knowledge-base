"""模块 7：HTTP 接口。

三个设计点值得你留意：
1. 模型和索引在 lifespan 里加载一次，不是每个请求都 load —— 这是新手最常见的性能错误
2. 请求/响应用 pydantic 校验，非法输入在入口就被挡住
3. 检索为空和 LLM 报错要分开返回不同状态码
"""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from app.config import settings
from app.embedding.embedder import Embedder
from app.generation.generator import Generator
from app.retrieval.retriever import Retriever
from app.store.vector_store import VectorStore

# 进程级单例。真实项目里用 app.state 挂载更规范，这样测试时可以替换。
state: dict = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """启动时加载一次，关闭时释放。

    SentenceTransformer 加载要 1~3 秒，模型占几百 MB。
    如果写在路由函数里，每个请求都要加载一次，QPS 直接归零。
    """
    print("加载索引与模型...")
    state["store"] = VectorStore.load(settings.index_file)
    state["embedder"] = Embedder()
    state["retriever"] = Retriever(state["store"], state["embedder"])
    state["generator"] = Generator()
    print(f"就绪：{len(state['store'])} 个片段，维度 {state['embedder'].dim}")
    yield
    state.clear()


app = FastAPI(title="RAG 知识库问答", version="0.1.0", lifespan=lifespan)


class AskRequest(BaseModel):
    question: str = Field(min_length=1, max_length=1000)
    top_k: int = Field(default=settings.top_k, ge=1, le=20)


class Citation(BaseModel):
    source: str
    score: float
    text: str


class AskResponse(BaseModel):
    answer: str
    citations: list[Citation]


@app.get("/health")
def health() -> dict:
    return {
        "status": "ok",
        "chunks": len(state.get("store", [])),
        "model": settings.llm_model,
    }


@app.post("/ask", response_model=AskResponse)
def ask(req: AskRequest) -> AskResponse:
    """问答主接口。已实现。"""
    retriever: Retriever = state["retriever"]
    generator: Generator = state["generator"]

    chunks = retriever.retrieve(req.question, top_k=req.top_k)
    try:
        result = generator.answer(req.question, chunks)
    except Exception as exc:  # noqa: BLE001
        # LLM 调用失败（超时、额度、网络）不应该返回 200 加一句错误文本，
        # 要让调用方从状态码就知道是我们这边的问题。
        raise HTTPException(status_code=502, detail=f"生成失败: {exc}") from exc

    return AskResponse(
        answer=result.text,
        citations=[
            Citation(
                source=c.chunk.metadata.get("source", "未知"),
                score=round(c.score, 4),
                text=c.chunk.text,
            )
            for c in result.citations
        ],
    )


# ============ 留给你的任务：文档上传接口 ============
#
# @app.post("/documents")
# async def upload(file: UploadFile) -> dict:
#     """上传文档 → 解析 → 分块 → 向量化 → 增量写入索引。
#
#     需要想清楚的四件事（面试会问）：
#     1. 增量写入：现有索引在内存里，新文档追加后要重新 save()，
#        怎么保证写一半崩了不会毁掉旧索引？（提示：先写临时文件再 rename，原子替换）
#     2. 大文件：await file.read() 会把整个文件读进内存，100MB 的文件就危险了。
#        怎么分块读？思考 File 的 read(size) 循环。
#     3. 并发：两个请求同时上传，都去改 state["store"]，会怎样？
#        提示：加锁（threading.Lock 或 asyncio.Lock），或者干脆排队。
#     4. 幂等：同一个文件上传两次，会不会产生重复片段？
#        提示：doc_id 已经是内容无关的路径 hash，可以先删旧的再插新的。
#
#     先别一次做完。先做最小版：接收文件 → 存到 data/docs → 重建全量索引 → 返回片段数。
#     跑通之后再逐个解决上面四个问题，每一个都是一次 commit。
#     """
#     raise NotImplementedError
