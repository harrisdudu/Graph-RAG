import sys
import os

current_dir = os.path.dirname(os.path.abspath(__file__))
# print("当前目录:", current_dir)
parent_dir = os.path.dirname(current_dir)
# print("父目录:", parent_dir)
pre_parent_dir = os.path.dirname(parent_dir)
# print("上一级目录:", pre_parent_dir)
sys.path.insert(0, current_dir)
sys.path.insert(0, parent_dir)
sys.path.insert(0, pre_parent_dir)

from typing import List
import uuid
from chunking import kps_text_splitter
from config import Settings
from langchain_milvus import Milvus
from langchain_community.graphs import Neo4jGraph
from core.tools.init_llm import get_llm
from core.tools.init_embed import get_embedding
from core.tools.init_vector_db import get_vector_db
from core.tools.init_graph_db import get_graph_db
from core.indexing.build_entity_extract_chain import build_langchain_extract_chain, parse_llm_output

def build_vector(chunk: str, chunk_id: str, vector_db: Milvus,file_params:dict) -> None:
    """
    从文本块中提取实体关系并构建知识图谱向量
    Args:
        chunks: 文本块列表
        vector_db: 向量数据库实例
    Returns:
        None
    """
    metadata = {
        "file_tag1": file_params.get("file_tag1", ""), 
        "file_tag2": file_params.get("file_tag2", "")
    }
    metadatas = [metadata]
    vector_db.add_texts(texts=[chunk], ids=[chunk_id], metadatas=metadatas)

def build_graph(settings: Settings,graph: Neo4jGraph, chunk: str, chunk_id: str,extract_chain) -> None:
    """
    从文本块中提取实体关系并构建知识图谱向量
    Args:
        chunks: 文本块列表
        vector_db: 向量数据库实例
    Returns:
        None
    """
    extract_result = extract_chain.invoke({"text": chunk}).strip()

    # # 解析实体列表
    # entity_list_line = [line for line in extract_result.split("\n") if "实体列表：" in line][0]
    # entity_list = [e.strip() for e in entity_list_line.replace("实体列表：", "").split(",") if e.strip()]
    # # 解析三元组
    # triples = [
    #     line.strip() for line in extract_result.split("\n") 
    #     if "|" in line and not line.startswith("实体列表：")
    # ]

    entity_list, triples = parse_llm_output(extract_result)
    # 知识库标签，区分不同知识库
    biz_label = settings.graph_store.biz_label
    # 3.3 图数据库入库 - 创建Chunk节点（文本块→实体）
    graph.query(f"""
    MERGE (c:Chunk {{chunk_id: $chunk_id}})
    SET c.content = $content, c.entities = $entities
    SET c:{biz_label};
    """, params={
        "chunk_id": chunk_id,
        "content": chunk[:20] + "...",
        "entities": entity_list
    })

    # 图数据库入库 - 创建Entity节点 (实体->文本块)
    for entity_name in entity_list:
        # 实体→文本块：更新Entity的chunk_ids（去重）
        # graph.query("""
        # MERGE (e:Entity {name: $entity_name})
        # SET e.chunk_ids = apoc.coll.addUnique(coalesce(e.chunk_ids, []), $chunk_id);
        # """, params={"entity_name": entity_name, "chunk_id": chunk_id})
        # add_unique_chunk_id(graph, entity_name, chunk_id)
        query = f"""
        MERGE (e:Entity {{name: $entity_name}})
        SET e:{biz_label}
        SET e.chunk_ids = CASE 
            WHEN e.chunk_ids IS NULL THEN [$chunk_id]
            WHEN NOT $chunk_id IN e.chunk_ids THEN e.chunk_ids + $chunk_id
            ELSE e.chunk_ids
        END
        RETURN e
        """
        graph.query(query, params={"entity_name": entity_name, "chunk_id": chunk_id})

    # 图数据库入库 - 文本块→实体：创建CONTAINS关系
    for entity_name in entity_list: 
        graph.query("""
        MATCH (c:Chunk {chunk_id: $chunk_id}), (e:Entity {name: $entity_name})
        MERGE (c)-[:CONTAINS]->(e);
        """, params={"chunk_id": chunk_id, "entity_name": entity_name})
        print(f"创建[文本块→实体]CONTAINS关系：{chunk_id} -> {entity_name}")

    # 图数据库入库 - 实体->实体: 实体间关系（RELATION）
    for triple in triples:
        if len(triple.split("|")) != 3:
            continue
        e1, rel, e2 = triple.split("|")
        e1, rel, e2 = e1.strip(), rel.strip(), e2.strip()
        if not e1 or not rel or not e2:
            continue
        # 入库实体关系
        graph.query("""
        MATCH (a:Entity {name: $e1}), (b:Entity {name: $e2})
        MERGE (a)-[r:RELATION {name: $rel}]->(b);
        """, params={"e1": e1, "rel": rel, "e2": e2})
        print(f"创建[实体→实体]RELATION关系：{e1} -> {rel} -> {e2}")


# def add_unique_chunk_id(graph, entity_name, chunk_id):
#     query = """
#         MERGE (e:Entity {name: $entity_name})
#         SET e.chunk_ids = CASE 
#             WHEN e.chunk_ids IS NULL THEN [$chunk_id]
#             WHEN NOT $chunk_id IN e.chunk_ids THEN e.chunk_ids + $chunk_id
#             ELSE e.chunk_ids
#         END
#         RETURN e
#     """
#     return graph.query(query, params={"entity_name": entity_name, "chunk_id": chunk_id})




def build_graph2vector(settings: Settings,chunks: List[str], vector_db, graph_db, extract_chain,file_params:dict)-> None:
    for chunk in chunks:
        # 生成唯一Chunk ID（跨库关联键）
        chunk_id = str(uuid.uuid4())
        print(f"处理文本块ID: {chunk_id}")
        print(f"处理文本块标签: ",file_params)
        # 向量库入库
        build_vector(chunk=chunk, chunk_id=chunk_id, vector_db=vector_db, file_params=file_params) 
        # 图数据库入库
        build_graph(settings=settings,graph=graph_db, chunk=chunk, chunk_id=chunk_id,extract_chain=extract_chain)


# ------------------------------
# 测试示例
# ------------------------------
if __name__ == "__main__":
    settings = Settings()
    embeddings = get_embedding(settings)
    vector_db = get_vector_db(settings,embeddings)
    graph_db = get_graph_db(settings)

    llm = get_llm(settings)
    extract_chain = build_langchain_extract_chain(llm)

    # 1. 读取文档内容（替换为实际文档文本）
    with open("./temp/出口食品检验检疫240523.txt", "r", encoding="utf-8") as f:
        doc_content = f.read()
    
    # 2. 拆分文档为文本块
    chunks = kps_text_splitter(doc_content, chunk_size=settings.chunk_size, chunk_overlap=settings.chunk_overlap)
    build_graph2vector(settings=settings,chunks=chunks, vector_db=vector_db, graph_db=graph_db, extract_chain=extract_chain)
