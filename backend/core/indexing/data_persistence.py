from typing import Dict, Optional
import numpy as np
import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..')))

# 尝试相对导入，如果失败则使用绝对导入
try:
    from .graph_build import Graph  # 导入图类
except ImportError:
    from backend.core.indexing.graph_build import Graph  # 导入图类

# 导入数据库客户端（需提前安装对应库）
try:
    from neo4j import GraphDatabase  # 图数据库
    from pymilvus import connections, Collection, FieldSchema, CollectionSchema, DataType  # 向量数据库
    NEO4J_AVAILABLE = True
    MILVUS_AVAILABLE = True
except ImportError as e:
    print(f"警告：数据库客户端库导入失败：{e}")
    print("请安装所需库：pip install neo4j pymilvus")
    NEO4J_AVAILABLE = False
    MILVUS_AVAILABLE = False


def persist_data(
    graph: Graph,
    graph_store_config: Optional[Dict] = None,
    vector_store_config: Optional[Dict] = None
) -> bool:
    """
    持久化图数据到图数据库和向量数据库
    
    Args:
        graph: 图对象（来自graph_build.py的Graph类）
        graph_store_config: 图存储配置，示例：
            {
                "type": "neo4j",
                "uri": "bolt://localhost:7687",
                "user": "neo4j",
                "password": "password",
                "database": "neo4j"  # 可选
            }
        vector_store_config: 向量存储配置，示例：
            {
                "type": "milvus",
                "host": "localhost",
                "port": "19530",
                "collection_name": "graph_embeddings",
                "dim": 1024  # 向量维度（需与实际嵌入匹配）
            }
    
    Returns:
        bool: 持久化是否成功
    """
    try:
        # 1. 持久化到图数据库
        if graph_store_config and graph_store_config.get("type") == "neo4j":
            if not NEO4J_AVAILABLE:
                raise Exception("Neo4j客户端库未安装或导入失败，请执行：pip install neo4j")
            if not persist_to_neo4j(graph, graph_store_config):
                raise Exception("图数据库持久化失败")
        
        # 2. 持久化到向量数据库
        if vector_store_config and vector_store_config.get("type") == "milvus":
            if not MILVUS_AVAILABLE:
                raise Exception("Milvus客户端库未安装或导入失败，请执行：pip install pymilvus")
            if graph.node_embeddings is None:
                raise ValueError("图对象中未包含节点嵌入向量，无法持久化到向量数据库")
            if not persist_to_milvus(graph, vector_store_config):
                raise Exception("向量数据库持久化失败")
        
        print("数据持久化成功")
        return True
    except Exception as e:
        print(f"数据持久化失败：{str(e)}")
        return False


def persist_to_neo4j(graph: Graph, config: Dict) -> bool:
    """将图数据持久化到Neo4j"""
    # 连接数据库
    driver = GraphDatabase.driver(
        config["uri"],
        auth=(config["user"], config["password"]),
        database=config.get("database", "neo4j")
    )
    
    try:
        with driver.session() as session:
            # 清除已有数据（可选操作）
            session.run("MATCH (n) DETACH DELETE n")
            
            # 批量创建节点（带名称属性）
            node_names = [graph.graph.nodes[node_id]["name"] for node_id in graph.node_ids]
            create_nodes_query = """
                UNWIND $nodes AS node
                MERGE (n:Entity {name: node.name})
                SET n.id = node.id
            """
            session.run(create_nodes_query, nodes=[
                {"id": node_id, "name": graph.graph.nodes[node_id]["name"]}
                for node_id in graph.node_ids
            ])
            
            # 批量创建关系
            triples = graph.get_triples()
            create_rels_query = """
                UNWIND $rels AS rel
                MATCH (h:Entity {name: rel.head})
                MATCH (t:Entity {name: rel.tail})
                MERGE (h)-[r:RELATION {type: rel.relation}]->(t)
            """
            session.run(create_rels_query, rels=[
                {"head": h, "relation": r, "tail": t} for h, r, t in triples
            ])
        
        print(f"成功将 {len(node_names)} 个节点和 {len(triples)} 条关系写入Neo4j")
        return True
    finally:
        driver.close()


def persist_to_milvus(graph: Graph, config: Dict) -> bool:
    """将节点嵌入向量持久化到Milvus"""
    # 连接Milvus
    connections.connect(
        alias="default",
        host=config["host"],
        port=config["port"]
    )
    
    collection_name = config["collection_name"]
    dim = config.get("dim", graph.embedding_dim)
    
    try:
        # 定义集合结构
        fields = [
            FieldSchema(name="id", dtype=DataType.VARCHAR, max_length=64, is_primary=True),
            FieldSchema(name="node_name", dtype=DataType.VARCHAR, max_length=256),
            FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=dim)
        ]
        schema = CollectionSchema(fields, description="Graph node embeddings")
        
        # 创建集合（如果不存在）
        collection = Collection(name=collection_name, schema=schema)
        
        # 准备数据
        data = [
            [node_id for node_id in graph.node_ids],  # id
            [graph.graph.nodes[node_id]["name"] for node_id in graph.node_ids],  # node_name
            graph.node_embeddings.tolist()  # embedding向量
        ]
        
        # 插入数据
        collection.insert(data)
        # 创建索引（加速查询）
        index_params = {
            "index_type": "IVF_FLAT",
            "metric_type": "L2",
            "params": {"nlist": 128}
        }
        collection.create_index(field_name="embedding", index_params=index_params)
        collection.load()
        
        print(f"成功将 {len(graph.node_ids)} 个节点嵌入写入Milvus（集合：{collection_name}）")
        return True
    finally:
        connections.disconnect("default")


# -------------------------- 测试示例 --------------------------
if __name__ == "__main__":
    # 测试代码中的导入
    try:
        from .graph_build import build_graph
    except ImportError:
        from backend.core.indexing.graph_build import build_graph

        # 测试三元组
    test_triples = [
        ("张三", "创始人", "字节跳动"),
        ("字节跳动", "总部位于", "北京"),
        ("北京", "属于", "中国"),
        ("字节跳动", "产品", "抖音")
    ]

    remote_config = {
        "type": "remote",
        "api_url": "http://172.16.0.211:10000/v1/embeddings",  # 替换为真实API地址
        "api_key": None,  # 可选
        "batch_size": 4
    }
    try:
        graph2 = build_graph(test_triples, model_name="bge-m3", deploy_config=remote_config)
        print(f"远程bge-m3嵌入维度：{graph2.embedding_dim}")
        print(f"远程bge-m3嵌入维度：{graph2.node_embeddings}")
    except Exception as e:
        print(f"远程调用失败（示例）：{e}")


    # 2. 配置数据库连接
    graph_db_config = {
        "type": "neo4j",
        "uri": "bolt://192.168.0.197:7687",
        "user": "neo4j",
        "password": "kps@2025",  # 替换为实际密码
        "database": "neo4j"
    }

    vector_db_config = {
        "type": "milvus",
        "host": "192.168.0.197",
        "port": "19530",
        "collection_name": "graph_nodes",
        "dim": 1024  
    }

    # 3. 执行持久化
    success = persist_data(
        graph=graph2,
        graph_store_config=graph_db_config,
        vector_store_config=vector_db_config
    )
    print("持久化结果：", "成功" if success else "失败")