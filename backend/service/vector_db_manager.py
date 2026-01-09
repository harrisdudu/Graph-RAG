import sys
import os

# 将backend目录添加到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import Settings

# 导入Milvus客户端（需提前安装对应库）
try:
    from pymilvus import connections, Collection
    MILVUS_AVAILABLE = True
except ImportError as e:
    print(f"警告：Milvus客户端库导入失败：{e}")
    print("请安装所需库：pip install pymilvus")
    MILVUS_AVAILABLE = False

class VectorDBManager:
    def __init__(self, settings: Settings, config=None):

        self.settings = settings
        # 默认配置
        self.default_config = {
            # "host": "192.168.0.197",
            # "port": "19530",
            # "collection_name": "graph_entities"

            "host": self.settings.milvus_host,
            "port": self.settings.milvus_port,
            "collection_name": self.settings.milvus_collection_name
        }
        
        # 合并配置
        self.config = self.default_config.copy()
        if config:
            self.config.update(config)
    
    def __connect(self):
        """连接到Milvus服务器"""
        if not MILVUS_AVAILABLE:
            raise Exception("Milvus客户端库未安装或导入失败，请执行：pip install pymilvus")
        
        connections.connect(
            alias="default",
            host=self.config["host"],
            port=self.config["port"]
        )
    
    def __disconnect(self):
        """断开Milvus服务器连接"""
        connections.disconnect("default")
    
    def get_all_vectors(self):
        """查询向量库中所有数据"""
        try:
            self.__connect()
            
            # 获取集合
            collection = Collection(name=self.config["collection_name"])
            collection.load()
            
            # 查询所有数据
            results = collection.query(
                expr="",  # 空表达式表示查询所有数据
                output_fields=["pk", "text", "vector"],
                limit=10000  # 设置一个较大的限制，可根据实际情况调整
            )
            
            self.__disconnect()
            return results
        except Exception as e:
            self.__disconnect()
            raise e
    
    def get_latest_vectors(self, limit=10):
        """查询向量库中最近的向量数据
        
        Args:
            limit: 返回的最大数量，默认100
            
        Returns:
            list: 包含id、node_name和embedding的向量数据列表
        """
        try:
            self.__connect()
            
            # 获取集合
            collection = Collection(name=self.config["collection_name"])
            collection.load()
            
            # 查询最近的数据（按id降序排序，取最近的limit条）
            results = collection.query(
                expr="",  # 空表达式表示查询所有数据
                output_fields=["pk", "text", "vector"],
                limit=limit,
                offset=0,
                order_by="id DESC"  # 按id降序排序，假设id是递增的
            )
            processed_results = []
            for item in results:
                # 跳过空值，避免报错
                if not item.get("text"):
                    processed_results.append(item)
                    continue
                
                # 方式1：精准替换所有换行符（推荐，只处理换行）
                clean_text = item["text"].replace("\r\n", "").replace("\n", "").replace("\r", "")
                
                # 方式2：替换所有空白字符（换行/制表符/空格等）为单个空格（更通用）
                # clean_text = re.sub(r'\s+', ' ', item["text"]).strip()  # strip去除首尾空格
                
                # 方式3：仅删除换行符，保留其他空白（如空格）
                # clean_text = re.sub(r'[\r\n]+', '', item["text"])
                
                # 更新处理后的文本
                item["text"] = clean_text
                processed_results.append(item)
            
            self.__disconnect()
            return processed_results
        except Exception as e:
            self.__disconnect()
            raise e
    
    def get_vectors_by_limit_offset(self, limit=100, offset=0):
        """分页查询向量数据
        
        Args:
            limit: 每页数量
            offset: 偏移量
            
        Returns:
            list: 包含id、node_name和embedding的向量数据列表
        """
        try:
            self.__connect()
            
            # 获取集合
            collection = Collection(name=self.config["collection_name"])
            collection.load()
            
            # 分页查询
            results = collection.query(
                expr="",  # 空表达式表示查询所有数据
                output_fields=["pk", "text", "vector"],
                limit=limit,
                offset=offset,
                order_by="id ASC"  # 按id升序排序
            )
            
            self.__disconnect()
            return results
        except Exception as e:
            self.__disconnect()
            raise e
    
    def get_vector_count(self):
        """获取向量库中的向量总数
        
        Returns:
            int: 向量总数
        """
        try:
            self.__connect()
            
            # 获取集合
            collection = Collection(name=self.config["collection_name"])
            collection.load()
            
            # 获取集合统计信息
            stats = collection.num_entities
            
            self.__disconnect()
            return stats
        except Exception as e:
            self.__disconnect()
            raise e

# 使用示例
if __name__ == "__main__":
    settings = Settings()
    # 创建向量数据库管理器实例
    vector_db_manager = VectorDBManager(settings=settings)
    
    try:
        # 获取向量总数
        count = vector_db_manager.get_vector_count()
        print(f"向量库中共有 {count} 个向量")
        
        # 查询最近100条数据
        latest_vectors = vector_db_manager.get_latest_vectors(limit=10)
        print(f"\n最近10条向量数据：")
        for i, vector in enumerate(latest_vectors):
            print(f"{i+1}. ID: {vector['pk']}, Node Name: {vector['text']}, Embedding: {vector['vector'][:3]}...")
        
        # 查询所有数据
        # all_vectors = vector_db_manager.get_all_vectors()
        # print(f"\n所有向量数据数量：{len(all_vectors)}")
        
    except Exception as e:
        print(f"操作失败：{e}")
