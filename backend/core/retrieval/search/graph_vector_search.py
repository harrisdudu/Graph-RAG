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

class GraphVectorSearch(BaseSearch):
    def process(self):
        '''
        执行图->向量检索，并获取文本
        '''
        vector_chunks, vector_chunk_ids = super().query_vector_db(self.vector_db, self.query, top_k=3)
        related_entities = super().get_graph_entity(self.graph_db, vector_chunk_ids)
        extended_chunk_ids = super().query_graph_extend(self.graph_db, related_entities, expand_depth=1, vector_chunk_ids=vector_chunk_ids)
        extended_chunks = super().get_chunk_text_by_id(self.graph_db, extended_chunk_ids)
        merged_context = super().get_merged_context(vector_chunks, extended_chunks)
        return merged_context,vector_chunks,extended_chunks
