import sys
import os

# 将backend目录添加到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import Settings
from core.tools.init_llm import get_llm
from core.tools.init_embed import get_embedding
from core.tools.init_vector_db import get_vector_db
from core.tools.init_graph_db import get_graph_db, check_neo4j_details
from core.retrieval.generate import generate_answer

from core.retrieval.search.vector_graph_search import VectorGraphSearch
from core.retrieval.search.vector_search import VectorSearch
from core.retrieval.rerank import rerank_candidates


class RetrievalService:
    def __init__(self, settings: Settings):
        self.llm = get_llm(settings)
        self.embeddings = get_embedding(settings)
        self.vector_db = get_vector_db(settings, self.embeddings)
        self.graph_db = get_graph_db(settings)
        self.settings = settings

    def process_query(self, query, search_method: str = "vector"):
        # 预处理查询
        # preprocessed_query = preprocess_query(query)

        # 执行检索
        if search_method == "vector-graph":
            VectorGraphSearchClazz = VectorGraphSearch(self.vector_db, self.graph_db, query, self.settings);
            vector_results, extended_chunks_results = VectorGraphSearchClazz.process()
        else:
            # 默认全部向量化查询
            VectorSearchClazz = VectorSearch(self.vector_db, query, self.settings);
            vector_results, extended_chunks_results = VectorSearchClazz.process()
        # 后处理结果
        extended_topk_chunks_results = rerank_candidates(query, extended_chunks_results)
        # 合并上下文
        merged_context = VectorGraphSearchClazz.get_merged_context(vector_results, extended_topk_chunks_results)
        # 生成回答
        answer = generate_answer(query, merged_context, self.llm)
        return answer,vector_results, extended_topk_chunks_results


# 使用示例
if __name__ == "__main__":
    # 创建检索服务实例
    settings = Settings()
    settings.graph_store.uri = "bolt://192.168.0.197:27687"
    settings.vector_store.port = "29530"
    
    settings.graph_store.biz_label = "kb_flfg"
    settings.vector_store.collection_name = "kb_flfg"
    retrieval_service = RetrievalService(settings)
    # 待处理的查询
    query = "金融人才引进政策有哪些？"
    
    # 处理查询
    results,vector_chunks,extended_chunks = retrieval_service.process_query(query)
    print(results)
