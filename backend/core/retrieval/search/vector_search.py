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

class VectorSearch(BaseSearch):
    def process(self):
        '''
        执行向量检索，并获取文本
        '''
        vector_chunks = super().query_vector_db(super().vector_db, super().query, top_k=3)
        extended_chunks = []
        merged_context = super().get_merged_context(vector_chunks, extended_chunks)
        return merged_context,vector_chunks,extended_chunks
