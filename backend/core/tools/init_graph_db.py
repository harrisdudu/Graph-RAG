import sys
import os

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
pre_parent_dir = os.path.dirname(parent_dir)
sys.path.insert(0, current_dir)
sys.path.insert(0, parent_dir)
sys.path.insert(0, pre_parent_dir)

from langchain_community.graphs import Neo4jGraph
from config import Settings

def init_neo4j_graph(url: str, user: str, password: str,database: str) -> Neo4jGraph:
    return Neo4jGraph(
        url=url,
        username=user,
        password=password,
        database=database
    )

def get_graph_db(settings: Settings) -> Neo4jGraph:
    url = settings.graph_store.uri
    user = settings.graph_store.user
    password = settings.graph_store.password
    database = settings.graph_store.database
    return init_neo4j_graph(url, user, password,database)

def check_neo4j_details(graph_db):
    """适配多种 Neo4jGraph 实现的检查函数"""
    try:
        # 获取数据库版本
        version_query = "CALL dbms.components() YIELD name, versions RETURN name, versions[0] AS version"
        
        # 获取节点数量
        count_query = "MATCH (n) RETURN count(n) AS node_count"
        
        # 方法1: 尝试 LlamaIndex Neo4jGraph 的 query 方法
        if hasattr(graph_db, 'query'):
            try:
                result = graph_db.query(version_query)
                if result and len(result) > 0:
                    info = result[0]
                    print(f"数据库: {info.get('name', 'Unknown')} v{info.get('version', 'Unknown')}")
                
                result = graph_db.query(count_query)
                if result and len(result) > 0:
                    count = result[0]
                    print(f"图中节点总数: {count.get('node_count', 0)}")
                return
            except:
                pass  # 如果 query 方法失败，尝试下一种方法
        
        # 方法2: 尝试获取底层驱动
        if hasattr(graph_db, '_driver'):
            driver = graph_db._driver
        elif hasattr(graph_db, 'driver'):
            driver = graph_db.driver
        else:
            driver = None
        
        if driver and hasattr(driver, 'session'):
            with driver.session() as session:
                # 获取版本
                result = session.run(version_query)
                info = result.single()
                print(f"数据库: {info['name']} v{info['version']}")
                
                # 获取节点数
                result = session.run(count_query)
                count = result.single()
                print(f"图中节点总数: {count['node_count']}")
            return
        
        # 方法3: 尝试 refresh_schema 或其他方法 (LangChain 风格)
        if hasattr(graph_db, 'refresh_schema'):
            graph_db.refresh_schema()
            print(f"✅ 数据库架构刷新成功")
            print(f"节点类型: {len(graph_db.node_types)}")
            print(f"关系类型: {len(graph_db.relationship_types)}")
            return
        
        # 如果以上方法都失败
        print(f"⚠️  无法识别的 Neo4jGraph 类型: {type(graph_db)}")
        print(f"可用方法: {[m for m in dir(graph_db) if not m.startswith('_')][:15]}")
        
    except Exception as e:
        print(f"获取数据库信息失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    settings = Settings()
    settings.graph_store.uri = "bolt://192.168.0.197:27687"
    graph_db = get_graph_db(settings)
    if graph_db:
        print("驱动对象:", graph_db)
        # 可以进一步检查数据库信息
        check_neo4j_details(graph_db)
    else:
        print("无法建立 Neo4j 连接")