# RAG 知识库问答系统

一个从零实现的文档智能问答服务：接入 PDF / Word / TXT，自建向量索引，检索增强生成，答案带出处。

> **第一次做项目？先读 [docs/新手起步.md](docs/新手起步.md)** —— 名词词典 + 环境搭建的每一步（含报错急救表）。

不是调 LangChain 的 Demo —— 核心链路全部手写，为了搞清楚每一层到底在做什么。

## 架构

```
离线建库（只跑一次）
  文档集 → 解析 → 分块 → 向量化 → 向量索引(落盘)
                                        │
在线问答（每次请求）                      │
  用户问题 → 检索 top-k ←────────────────┘
           → 组装 prompt → LLM → 回答 + 出处
```

## 技术栈

| 层 | 选型 | 为什么 |
|---|---|---|
| Web | FastAPI + uvicorn | 自带 OpenAPI 文档，异步，生态标准 |
| 配置 | pydantic-settings | 类型安全，环境变量与 .env 统一 |
| 文档解析 | pypdf / python-docx | 够用、纯 Python、无外部依赖 |
| Embedding | BAAI/bge-small-zh-v1.5 | 中文效果好、体积小、CPU 可跑、免费 |
| 向量索引 | numpy 手写 | 理解本质；后期与 Chroma 做性能对比 |
| LLM | OpenAI 兼容接口 | 一套代码切换 DeepSeek / 智谱 / 通义 |
| 测试 | pytest | 单元测试 + 后续的评估脚本 |

## 快速开始

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env               # 填入你的 API Key
```

```bash
# 1. 把文档放进 data/docs/
# 2. 建索引
python scripts/build_index.py
# 3. 提问
python -m app.cli "你的问题"
```

## 开发进度

勾掉一项就是一次 commit。

- [x] D1 环境跑通，能打印一次 LLM 回复
- [ ] D2 模块 1 文档接入（PDF / Word / TXT）
- [ ] D3 模块 2 分块器 + 单元测试
- [ ] D4 模块 3+4 向量化与索引，能存盘读回
- [ ] D5 模块 5+6 检索 + 生成，闭环跑通
- [ ] D6 模块 7 FastAPI 接口
- [ ] D7 README + 架构图 + 代码整理

## 目录

```
app/
  config.py            全局配置（环境变量）
  schemas.py           数据契约：Document / Chunk / RetrievedChunk
  ingest/loader.py     模块1 各类文档 → 纯文本 + 元数据
  chunking/splitter.py 模块2 长文本 → 带重叠的 chunk
  embedding/embedder.py 模块3 文本 → 归一化向量
  store/vector_store.py 模块4 向量索引的增、查、持久化
  retrieval/retriever.py 模块5 问题 → top-k 相关片段
  generation/generator.py 模块6 片段 + 问题 → 带出处的回答
  api/main.py          模块7 HTTP 接口
  cli.py               命令行入口（开发期用）
scripts/build_index.py 建库脚本
tests/                 单元测试
data/docs/             放你的文档
storage/               索引文件（不入库）
```

## 面试能讲什么

写在这里的东西，必须是你能展开讲 5 分钟的：

- 分块大小怎么定的，试过哪些值，对召回的影响
- 为什么向量要归一化，归一化后点积等价于余弦相似度
- 一万条向量的暴力检索要多久，为什么这个量级不需要 ANN
- 检索不准时你的排查顺序：分块 → embedding → 相似度阈值 → prompt
- 评估集怎么造的，指标怎么算的，改进前后差多少
