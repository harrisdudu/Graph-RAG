from pydantic_settings import BaseSettings
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any


class GraphStoreConfig(BaseModel):
    type: str = "neo4j"
    uri: str = "bolt://192.168.0.197:7687"
    # uri: str = "bolt://192.168.0.197:27687"
    user: str = "neo4j"
    password: str = "kps@2025"
    database: str = "neo4j"
    # 通过label对库进行隔离，重要参数
    biz_label: str = "kb_flfg" 

class VectorStoreConfig(BaseModel):
    type: str = "milvus"
    host: str = "192.168.0.197"
    port: str = "19530"
    # port: str = "29530"
    collection_name: str = "kb_flfg"
    dim: int = 1024

class LLMConfig(BaseModel):
    model: str = "Qwen3-32B"
    # base_url: str = "http://172.16.0.211:23001/v1/chat/completions"
    base_url: str = "http://172.16.0.211:23001/v1"
    api_key: Optional[str] = "dummy-key"

class EmbedConfig(BaseModel):
    model: str = "bge-m3"
    base_url: str = "http://172.16.0.211:10000/v1/embeddings"
    # base_url: str = "http://172.16.0.211:10000"
    config: Dict[str, Any] = Field(default_factory=dict)

class PgConfig(BaseModel):
    host: str = "192.168.0.197"
    port: int = 15432
    user: str = "kps"
    password: str = "Kps@2025"
    database: str = "kb"

class SplitConfig(BaseModel):
    chunk_size: int = 1500
    chunk_overlap: int = 150

class SearchConfig(BaseModel):
    top_k: int = 3
    expand_depth: int = 2
    score: float = 0.5

class rerankConfig(BaseModel):
    model: str = "bge-rerank"
    base_url: str = "http://172.16.0.211:10000/v1/rerank"


class Settings(BaseSettings):
    split: SplitConfig = Field(default_factory=SplitConfig)
    search: SearchConfig = Field(default_factory=SearchConfig)
    rerank: rerankConfig = Field(default_factory=rerankConfig)

    llm: LLMConfig = Field(default_factory=LLMConfig)
    embed: EmbedConfig = Field(default_factory=EmbedConfig)
    graph_store: GraphStoreConfig = Field(default_factory=GraphStoreConfig)
    vector_store: VectorStoreConfig = Field(default_factory=VectorStoreConfig)
    pg: PgConfig = Field(default_factory=PgConfig)


if __name__ == "__main__":
    st = Settings()
    print(st.split)
    st.split.chunk_size = 1100
    print(st.split)
    print(st.search)
    print(st.rerank)
    print(st.llm)
    print(st.embed)
    print(st.graph_store)
    print(st.vector_store)
    print(st.pg)
