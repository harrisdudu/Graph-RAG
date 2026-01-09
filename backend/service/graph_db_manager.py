import sys
import os

from pymilvus import settings

# 将backend目录添加到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import Settings
from core.tools.init_graph_db import get_graph_db

# 导入Neo4j驱动（需提前安装对应库）
try:
    from neo4j import GraphDatabase
    NEO4J_AVAILABLE = True
except ImportError as e:
    print(f"警告：Neo4j驱动库导入失败：{e}")
    print("请安装所需库：pip install neo4j")
    NEO4J_AVAILABLE = False

class GraphDBManager:
    def __init__(self, settings: Settings, config=None):
        # 默认配置（从index_service.py中获取）
        self.default_config = {
            "uri": "bolt://192.168.0.197:7687",
            "username": "neo4j",
            "password": "kps@2025"
        }

        self.settings = settings
        
        # 合并配置
        self.config = self.default_config.copy()
        if config:
            self.config.update(config)
        
        self.graph_db = get_graph_db(self.settings)
    
    def __connect(self):
        """连接到Neo4j服务器"""
        if not NEO4J_AVAILABLE:
            raise Exception("Neo4j驱动库未安装或导入失败，请执行：pip install neo4j")
        
        self.driver = GraphDatabase.driver(
            self.config["uri"],
            auth=(self.config["username"], self.config["password"])
        )
    
    def __disconnect(self):
        """断开Neo4j服务器连接"""
        if hasattr(self, 'driver') and self.driver:
            self.driver.close()
    
    def get_all_nodes(self):
        """查询图数据库中所有节点"""
        try:
            self.__connect()
            
            with self.driver.session() as session:
                result = session.run("MATCH (n) RETURN n")
                nodes = []
                for record in result:
                    node = record["n"]
                    nodes.append({
                        "id": node.element_id,
                        "labels": list(node.labels),
                        "properties": dict(node)
                    })
            
            self.__disconnect()
            return nodes
        except Exception as e:
            self.__disconnect()
            raise e
    
    def get_all_relationships(self):
        """查询图数据库中所有关系"""
        try:
            self.__connect()
            
            with self.driver.session() as session:
                result = session.run("MATCH (a)-[r]->(b) RETURN a, r, b")
                relationships = []
                for record in result:
                    a = record["a"]
                    r = record["r"]
                    b = record["b"]
                    relationships.append({
                        "id": r.element_id,
                        "type": r.type,
                        "start_node_id": a.element_id,
                        "end_node_id": b.element_id,
                        "properties": dict(r)
                    })
            
            self.__disconnect()
            return relationships
        except Exception as e:
            self.__disconnect()
            raise e
    
    def get_graph_data(self):
        """获取完整的图数据（节点和关系）"""
        try:
            self.__connect()
            
            with self.driver.session() as session:
                # 查询所有节点
                nodes_result = session.run("MATCH (n) RETURN n")
                nodes = []
                for record in nodes_result:
                    node = record["n"]
                    nodes.append({
                        "id": node.element_id,
                        "labels": list(node.labels),
                        "properties": dict(node)
                    })
                
                # 查询所有关系
                relationships_result = session.run("MATCH (a)-[r]->(b) RETURN a, r, b")
                relationships = []
                for record in relationships_result:
                    a = record["a"]
                    r = record["r"]
                    b = record["b"]
                    relationships.append({
                        "id": r.element_id,
                        "type": r.type,
                        "start_node_id": a.element_id,
                        "end_node_id": b.element_id,
                        "properties": dict(r)
                    })
            
            self.__disconnect()
            return {
                "nodes": nodes,
                "relationships": relationships
            }
        except Exception as e:
            self.__disconnect()
            raise e
    
    def get_graph_stats(self):
        """获取图数据库统计信息"""
        try:
            self.__connect()
            
            with self.driver.session() as session:
                # 获取节点总数
                node_count = session.run("MATCH (n) RETURN count(n) as count").single()["count"]
                
                # 获取关系总数
                relationship_count = session.run("MATCH ()-[r]->() RETURN count(r) as count").single()["count"]
                
                # 获取节点标签分布
                labels_result = session.run("MATCH (n) RETURN labels(n) as label, count(n) as count")
                label_counts = []
                for record in labels_result:
                    label = record["label"][0] if record["label"] else "No Label"
                    label_counts.append({
                        "label": label,
                        "count": record["count"]
                    })
                
                # 获取关系类型分布
                relationship_types_result = session.run("MATCH ()-[r]->() RETURN type(r) as type, count(r) as count")
                relationship_types = []
                for record in relationship_types_result:
                    relationship_types.append({
                        "type": record["type"],
                        "count": record["count"]
                    })
            
            self.__disconnect()
            return {
                "node_count": node_count,
                "relationship_count": relationship_count,
                "label_counts": label_counts,
                "relationship_types": relationship_types
            }
        except Exception as e:
            self.__disconnect()
            raise e

    def get_graph_data_by_id(self, chunk_id: str):
        res = self.graph_db.query("""
        MATCH (c:Chunk {chunk_id: $chunk_id})-[:CONTAINS]->(e:Entity)
        RETURN e.name AS entity_name;
        """, params={"chunk_id": chunk_id})
        related_entities = []
        related_entities.extend([item["entity_name"] for item in res])
        related_entities = list(set(related_entities))
        return related_entities


# 使用示例
if __name__ == "__main__":
    # 创建图数据库管理器实例
    settings = Settings()
    graph_db_manager = GraphDBManager()
    
    try:
        # # 获取图统计信息
        # stats = graph_db_manager.get_graph_stats()
        # print(f"图数据库统计信息：")
        # print(f"节点总数：{stats['node_count']}")
        # print(f"关系总数：{stats['relationship_count']}")
        
        # print(f"\n节点标签分布：")
        # for label in stats['label_counts']:
        #     print(f"  - {label['label']}: {label['count']}")
        
        # print(f"\n关系类型分布：")
        # for rel_type in stats['relationship_types']:
        #     print(f"  - {rel_type['type']}: {rel_type['count']}")
        
        # # 获取前5个节点和关系
        # graph_data = graph_db_manager.get_graph_data()
        # print(f"\n前5个节点：")
        # for node in graph_data['nodes'][:5]:
        #     print(f"  - ID: {node['id']}, Labels: {node['labels']}, Properties: {node['properties']}")
        
        # print(f"\n前5个关系：")
        # for rel in graph_data['relationships'][:5]:
        #     print(f"  - ID: {rel['id']}, Type: {rel['type']}, From: {rel['start_node_id']}, To: {rel['end_node_id']}")
            
        # 获取指定节点的相关实体
        chunk_id = "7bedd6ab-c76e-4ae0-aef3-f7bd6e70c352"
        related_entities = graph_db_manager.get_graph_data_by_id(chunk_id)
        print(f"\n节点 {chunk_id} 的相关实体：{related_entities}")
            
    except Exception as e:
        print(f"操作失败：{e}")
