import sys
import os

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
pre_parent_dir = os.path.dirname(parent_dir)
sys.path.insert(0, current_dir)
sys.path.insert(0, parent_dir)
sys.path.insert(0, pre_parent_dir)

from core.retrieval.search.base_search import BaseSearch
from core.retrieval.retrieve.rrf_fusion import rrf_fusion



class VectorGraphSearch(BaseSearch):
    def process(self):
        '''
        执行向量检索并扩展上下文(向量->图->文本)
        '''
        vector_chunk_ids, vector_results = super().query_vector_db(self.vector_db, self.query, top_k=self.settings.search.top_k,score=self.settings.search.score)
        related_entities = super().get_graph_entity(self.graph_db, vector_chunk_ids)
        extend_sorted_result = super().query_graph_extend(self.graph_db, related_entities, expand_depth=1, vector_chunk_ids=vector_chunk_ids)
        extended_chunks_results = super().get_chunk_text_by_id(extend_sorted_result)
        # retrieve 召回融合(Retrieve): 采用RRF算法
        # fusion_results = rrf_fusion(vector_results, extended_chunks_results, k=60, weights=[0.6, 0.4])
        
        return vector_results, extended_chunks_results
