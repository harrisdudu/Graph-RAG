import sys
import os

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
pre_parent_dir = os.path.dirname(parent_dir)
sys.path.insert(0, current_dir)
sys.path.insert(0, parent_dir)
sys.path.insert(0, pre_parent_dir)

from config import Settings
from langchain_milvus import Milvus
from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document  

from pymilvus import MilvusClient, settings
from langchain.embeddings.base import Embeddings

from pymilvus import Collection, utility, connections, FieldSchema, CollectionSchema, DataType
from typing import Any

class VectorDB:
    def __init__(self, settings: Settings, embeddings: Embeddings):
        self.settings = settings
        self.embeddings = embeddings
        # self.chroma_db = self.init_chroma_db(settings)
        self.milvus_db = self.init_milvus_db(settings, embeddings)

    def init_chroma_db(self, settings: Settings) -> Chroma:
        """
        初始化向量数据库（Chroma）
        
        Args:
            settings: 配置对象
            
        Returns:
            Chroma: 初始化后的Chroma向量数据库实例
        """
        chroma_db = Chroma(
            collection_name="graphrag_complete",
            embedding_function=embeddings,
            persist_directory="./chroma/data",
            client_settings={
                "chroma_api_impl": "rest",
                "chroma_server_host": "localhost",
                "chroma_server_http_port": 8000
            }
        )
        return chroma_db

    def init_milvus_db(self, settings: Settings, embeddings: Embeddings) -> Milvus:
        """初始化Milvus向量数据库"""
        try:
            # 打印实际连接信息用于调试
            host = settings.vector_store.host
            port = settings.vector_store.port
            print(f"正在连接Milvus: http://{host}:{port}")
            
            milvus_db = Milvus(
                embedding_function=embeddings,
                collection_name=settings.vector_store.collection_name,
                connection_args={
                    "uri": f"http://{host}:{port}",  # 使用uri
                },
                index_params={
                    "metric_type": "COSINE",
                    "index_type": "IVF_FLAT",
                    "params": {"nlist": 1024}
                },
                search_params={
                    "metric_type": "COSINE",
                    "params": {"nprobe": 16}
                },
                drop_old=False,
                enable_dynamic_field=True,
            )
            
            return milvus_db
            
        except Exception as e:
            print(f"初始化Milvus失败: {e}")
            raise


# 获取初始化后的向量数据库实例    
def get_vector_db(settings: Settings, embeddings: Embeddings) -> Milvus:
    """获取Milvus向量数据库实例"""
    vector_db = VectorDB(settings, embeddings)
    return vector_db.init_milvus_db(settings, embeddings)

def quick_verify(settings: Settings, milvus_db: Milvus) -> bool:
    """30秒快速验证"""
    try:
        # 测试写入
        # ids = milvus_db.add_texts(
        #     texts=["测试"],
        #     metadatas=[{"source": "test"}],  # metadata字段必须与Schema一致
        #     ids=["1234567889"],
        #     id_field="pk"
        # )
        # print("✅ 写入成功")
        
        # 测试查询
        results = milvus_db.similarity_search("测试", k=1)
        print(f"✅ 查询成功，返回 {len(results)} 条结果")
        print(results)
        
        # 清理
        # milvus_db.delete(ids)
        # print("✅ 删除成功")
        
        return True
    except Exception as e:
        print(f"❌ 验证失败: {e}")
        return False

# ---------------------- 核心：纯 ID 精确查询方法 ----------------------
def query_by_ids(settings: Settings, ids: list) -> list[Document]:
    """
    纯 ID 精确查询，无任何向量计算，返回 LangChain Document 列表
    :param ids: 要查询的 ID 列表（如 [1,2,3] 或 ["chunk_1", "chunk_2"]）
    :return: LangChain Document 列表（兼容原有 LangChain 流程）
    """
    MILVUS_URI = f"http://{settings.vector_store.host}:{settings.vector_store.port}"
    COLLECTION_NAME = settings.vector_store.collection_name
    ID_FIELD = "pk"
    TEXT_FIELD = "text"
    METADATA_FIELD = "metadata"
    milvus_client = MilvusClient(uri=MILVUS_URI)
    # 边界检查
    if not isinstance(ids, list) or len(ids) == 0:
        return []
    
    # 调用 Milvus 官方 query 方法（纯 ID 匹配，无向量）
    raw_results = milvus_client.query(
        collection_name=COLLECTION_NAME,
        ids=ids,  # 直接指定 ID 列表，精准匹配
        output_fields=[ID_FIELD, TEXT_FIELD]  # 只返回需要的字段
    )
    
    # 转换为 LangChain Document 格式（保持和原有流程兼容）
    docs = []
    for item in raw_results:
        doc = Document(
            page_content=item.get(TEXT_FIELD, "").replace('\r\n', '').replace('\n', '').replace('\r', ''),  # 文本内容
            metadata=item.get(METADATA_FIELD, {})    # 元数据
        )
        # 可选：把 ID 加入元数据，方便后续使用
        doc.metadata[ID_FIELD] = item.get(ID_FIELD)
        docs.append(doc)
    
    return docs


if __name__ == "__main__":
    from core.tools.init_embed import get_embedding
    settings = Settings()
    settings.vector_store.port = "29530"

    embeddings = get_embedding(settings)
    vector_db = VectorDB(settings, embeddings)

    milvus_db = vector_db.init_milvus_db(settings, embeddings)
    if quick_verify(settings, milvus_db):
        print("🎉 Milvus正常工作！")

    # docs = vector_db.query_by_ids(["7bedd6ab-c76e-4ae0-aef3-f7bd6e70c352"])
    # print(docs)