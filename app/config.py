"""全局配置。

这一层已经在替你解决一个问题：把"配什么"和"怎么实现"分开。
换模型、调分块大小，只改 .env，不动代码。
"""

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # LLM（OpenAI 兼容接口）
    llm_api_key: str = ""
    llm_base_url: str = "https://api.deepseek.com/v1"
    llm_model: str = "deepseek-chat"
    llm_temperature: float = 0.0

    # Embedding
    embedding_model: str = "BAAI/bge-small-zh-v1.5"
    embedding_batch_size: int = 32

    # 分块
    chunk_size: int = 500
    chunk_overlap: int = 80

    # 检索
    top_k: int = 5
    min_score: float = 0.0  # 低于此分数的片段直接丢掉，避免硬凑 top-k

    # 路径
    data_dir: Path = PROJECT_ROOT / "data"
    storage_dir: Path = PROJECT_ROOT / "storage"

    @property
    def docs_dir(self) -> Path:
        return self.data_dir / "docs"

    @property
    def index_file(self) -> Path:
        return self.storage_dir / "index.npz"


@lru_cache
def get_settings() -> Settings:
    """单例。配置只在进程内解析一次，避免每个请求都读文件。"""
    return Settings()


settings = get_settings()
