import sys
import os

from langchain_milvus import Milvus

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
pre_parent_dir = os.path.dirname(parent_dir)
sys.path.insert(0, current_dir)
sys.path.insert(0, parent_dir)
sys.path.insert(0, pre_parent_dir)

from deprecation import deprecated
from core.tools.init_vector_db import query_by_ids
from config import Settings

class BaseSearch:
    def __init__(self, vector_db:Milvus, graph_db, query, settings: Settings) :
        self.vector_db = vector_db
        self.graph_db = graph_db
        self.query = query
        self.biz_label = settings.graph_store.biz_label
        self.settings = settings
    
    def process(self):
        # 默认返回空集合
        vector_chunks = []
        extended_chunks = []
        merged_context = self.get_merged_context(vector_chunks, extended_chunks)
        return merged_context,vector_chunks,extended_chunks


    def query_vector_db(self, vector_db:Milvus, query, top_k:int, score:float):
        """
        查询向量数据库，返回相似度最高的文本块
        
        Args:
            vector_db: 向量存储实例
            query: 查询字符串
            top_k: 召回的结果数量
            
        Returns:
            list: 包含文本块ID和相似度分数的元组列表
        """
        print("\n=== 向量检索召回文本块 ===")
        vector_results = vector_db.similarity_search_with_score(query, k=top_k)
        vector_chunk_ids = []

        for doc,score in vector_results:
            # 格式化处理内容
            formatted_content = doc.page_content.replace('\r\n', '').replace('\n', '').replace('\r', '')
            doc.page_content = formatted_content
            vector_chunk_ids.append(doc.metadata["pk"])

        print(f"向量检索召回{len(vector_chunk_ids)}个文本块，ID：{vector_chunk_ids}")
        # 按照score排序
        vector_results = sorted(vector_results, key=lambda x: x[1], reverse=True)
        return vector_chunk_ids, vector_results

    def get_chunk_text_by_id(self, extend_sorted_result):
        """
        根据文本块ID查询文本内容
        
        Args:
            extend_sorted_result: 包含文本块ID和相似度分数的元组列表
            
        Returns:
            list: 包含文本内容的列表
        """
        print("\n=== 回查vectordb获取扩展文本内容 ===")
        extended_chunks_results = []
        for chunkid, score in extend_sorted_result:
            vector_db_res = query_by_ids(self.settings, ids=[chunkid])
            for doc in vector_db_res:
                clean_content = doc.page_content.replace('\r\n', '').replace('\n', '').replace('\r', '')
                extended_chunks_results.append((chunkid, clean_content, score))

        print(f"扩展文本块内容：{extended_chunks_results}")
        return extended_chunks_results

    def get_graph_entity(self, graph_db, vector_chunk_ids=[]):
        """
        查询图数据库，返回与查询ID匹配的实体
        
        Args:
            graph_db: 图存储实例
            vector_chunk_ids: 向量检索得到的文本块ID列表
            
        Returns:
            list: 包含实体名称的列表
        """
        print("\n=== 图查询关联实体 ===")
        related_entities = []
        for chunk_id in vector_chunk_ids:
            res = graph_db.query(f"""
            MATCH (c:Chunk:{self.biz_label} {{chunk_id: $chunk_id}})-[:CONTAINS]->(e:Entity)
            RETURN e.name AS entity_name;
            """, params={"chunk_id": chunk_id})
            related_entities.extend([item["entity_name"] for item in res])
        related_entities = list(set(related_entities))
        print(f"关联实体：{related_entities}")
        return related_entities
    
    def query_graph_extend(self, graph_db, related_entities, expand_depth, vector_chunk_ids=[], top_k=3):
        """
        从关联实体扩展文本块ID（支持多深度扩展）
        
        Args:
            graph_db: 图存储实例
            related_entities: 关联实体名称列表
            expand_depth: 实体扩展深度，默认1（仅直接关联），2表示两跳关联，以此类推
            vector_chunk_ids: 原始向量检索得到的chunk_id列表，用于去重
        
        Returns:
            list: 扩展得到的文本块ID列表（已去除原始ID）
        """
        print("\n=== 从关联实体扩展文本块ID ===")
        
        # 校验扩展深度的合法性
        if not isinstance(expand_depth, int) or expand_depth < 1:
            raise ValueError("expand_depth必须是大于等于1的整数")
        

        temp_extended_chunk_ids = []
        cypher_query = f"""
            MATCH (e:Entity {{name: $entity_name}})-[*1..{expand_depth}]-(related_e:Entity:{self.biz_label})
            RETURN collect(DISTINCT related_e.chunk_ids) AS all_chunk_ids;
            """
        
        for entity in related_entities:
            try:
                res = graph_db.query(cypher_query, params={"entity_name": entity})
                # 提取并处理返回的chunk_ids
                if res and res[0]["all_chunk_ids"] and isinstance(res[0]["all_chunk_ids"], list):
                    chunk_ids = res[0]["all_chunk_ids"]
                    temp_extended_chunk_ids.extend(chunk_ids)
            except Exception as e:
                print(f"从实体 {entity} 扩展chunk_id时出错：{str(e)}")
                continue
        
        print(f"扩展文本块ID（扩展深度{expand_depth}）获取的所有文本块ID：{temp_extended_chunk_ids}")


        # 去重并移除原始vector_chunk_ids中的ID
        extended_chunk_ids = []
        extended_chunk_ids = list(set(self.flatten_nested_list(temp_extended_chunk_ids)) - set(vector_chunk_ids))
        print(f"扩展文本块ID（扩展深度{expand_depth}）去重后：{extended_chunk_ids}")

        # 统计文档被实体匹配的次数（关联度）
        doc_count = {}
        for chunk_id in extended_chunk_ids:
            chunk_entities = self.get_graph_entity(graph_db, [chunk_id])
            common_elements = set(related_entities) & set(chunk_entities)    
            count = len(common_elements)
            raw_value = (doc_count.get(chunk_id, 0) + count) / len(related_entities)
            # 保留小数位，默认5位
            doc_count[chunk_id] = round(raw_value, 5) 

        # 按关联度降序排序，取top_k
        sorted_docs = sorted(doc_count.items(), key=lambda x: x[1], reverse=True)
        extend_sorted_result = [(doc_id, score) for doc_id, score in sorted_docs[:top_k]]
        
        return extend_sorted_result
        
    def query_es_db(self, es_db, query, top_k=3):
        """
        查询ES数据库，返回与查询匹配的文档
        
        Args:
            es_db: ES存储实例
            query: 查询字符串
            top_k: 召回的结果数量
            
        Returns:
            list: 包含文档内容的列表
        """
        res = es_db.search(index="kps", body={
            "query": {
                "bool": {
                    "must": [
                        {"match": {"content": query}}
                    ]
                }
            },
            "size": top_k
        })
        return [item["_source"]["content"] for item in res["hits"]["hits"]]

    def get_merged_context(self, vector_chunks, extended_chunks):
        """
        合并向量检索和图扩展的上下文
        
        Args:
            vector_chunks: 向量检索得到的文本块列表
            extended_chunks: 图扩展得到的文本块列表
            
        Returns:
            str: 合并后的上下文字符串
        """

        core_content_list = [doc.page_content for doc,score in vector_chunks]  
        core_text = chr(10).join(core_content_list)

        if extended_chunks:
            # 适配扩展文本元组/字符串混合场景
            extended_content_list = []
            for doc,score in extended_chunks:
                if isinstance(doc, (list, tuple)):
                    extended_content_list.append(doc[1])  # 元组取第2个元素
                else:
                    extended_content_list.append(doc)     # 纯字符串直接用
            extended_text = chr(10).join(extended_content_list)
        else:
            extended_text = "无扩展文本"



        print("\n=== 融合上下文 ===")
        merged_context = f"""
        【核心文本（向量检索）】：
        {core_text}
        
        【扩展文本（图关联）】：
        {extended_text}
        """
        print("融合后上下文：", merged_context)
        return merged_context

    def flatten_nested_list(self, nested_list):
            """
            递归展平任意深度的嵌套列表
            参数:
                nested_list: 可能包含多层嵌套列表的列表（如 [[1, [2, 3]], [4, [5, [6]]]]）
            返回:
                展平后的单层列表（如 [1, 2, 3, 4, 5, 6]）
            """
            flattened = []
            for item in nested_list:
                # 如果当前元素是列表，递归展平；否则直接添加
                if isinstance(item, list):
                    flattened.extend(self.flatten_nested_list(item))
                else:
                    # 过滤空值（可选，根据你的业务需求调整）
                    if item is not None and item != "":
                        flattened.append(item)
            return flattened

    @deprecated(deprecated_in="1.0", removed_in="2.0", current_version="1.5", details="请使用 new_function 替代")
    def double_layer_retrieval(vector_db, graph_db, query, top_k=3, expand_depth=2):
        """
        执行检索，结合图存储和向量存储
        
        Args:
            vector_db: 向量存储实例
            graph_db: 图存储实例
            query: 查询字符串
            top_k: 召回的结果数量
            expand_depth: 图遍历深度
            
        Returns:
            list: 检索结果列表
        """
        print("\n=== 向量检索召回文本块 ===")
        vector_results = vector_db.similarity_search_with_score(query, k=top_k)
        vector_chunks = []
        vector_chunk_ids = []
        for doc, score in vector_results:
            if score < 0.8:
                vector_chunks.append(doc.page_content.replace('\r\n', '').replace('\n', '').replace('\r', ''))
                vector_chunk_ids.append(doc.metadata["pk"])
        print(f"向量检索召回{len(vector_chunks)}个文本块，ID：{vector_chunk_ids}")

        print("\n=== 图查询关联实体 ===")
        related_entities = []
        for chunk_id in vector_chunk_ids:
            res = graph_db.query("""
            MATCH (c:Chunk {chunk_id: $chunk_id})-[:CONTAINS]->(e:Entity)
            RETURN e.name AS entity_name;
            """, params={"chunk_id": chunk_id})
            related_entities.extend([item["entity_name"] for item in res])
        related_entities = list(set(related_entities))
        print(f"关联实体：{related_entities}")

        print("\n=== 从关联实体扩展文本块ID ===")
        extended_chunk_ids = []
        for entity in related_entities:
            res = graph_db.query("""
            MATCH (e:Entity {name: $entity_name})
            RETURN e.chunk_ids AS chunk_ids;
            """, params={"entity_name": entity})
            if res and res[0]["chunk_ids"]:
                extended_chunk_ids.extend(res[0]["chunk_ids"])
        extended_chunk_ids = list(set(extended_chunk_ids) - set(vector_chunk_ids))
        print(f"扩展文本块ID：{extended_chunk_ids}")

        print("\n=== 回查vectordb获取扩展文本内容 ===")
        extended_chunks = []
        if extended_chunk_ids:
            vectot_db_res = query_by_ids(ids=extended_chunk_ids)
            for doc in vectot_db_res:
                extended_chunks.append(doc.page_content.replace('\r\n', '').replace('\n', '').replace('\r', ''))
        print(f"扩展文本块内容：{extended_chunks}")

        print("\n=== 融合上下文 ===")
        merged_context = f"""
        【核心文本（向量检索）】：
        {chr(10).join(vector_chunks)}
        
        【扩展文本（图关联）】：
        {chr(10).join(extended_chunks) if extended_chunks else "无扩展文本"}
        """
        print("融合后上下文：", merged_context)
        return merged_context,vector_chunks,extended_chunks
