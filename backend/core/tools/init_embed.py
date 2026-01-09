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

from langchain.embeddings.base import Embeddings
import requests
from typing import List, Optional
from config import Settings

class init_Embedding(Embeddings):
    """
    通过URL访问公司内部bge-m3模型服务
    """
    
    def __init__(
        self, 
        api_url: str,
        model_name: str,
        api_key: Optional[str] = None,
        timeout: int = 30,
        batch_size: int = 32
    ):
        """
        Args:
            api_url: 模型服务API地址，如 "http://embedding-service.internal:8000/v1"
            model_name: 模型名称，用于指定具体模型版本
            api_key: API认证密钥（如果需要）
            timeout: API请求超时时间（秒）
            batch_size: 批处理大小，根据API限制调整
        """
        self.api_url = api_url.rstrip("/")
        self.model_name = model_name
        self.api_key = api_key
        self.timeout = timeout
        self.batch_size = batch_size
        
        # 验证API可用性
        self._validate_connection()
    
    def _get_headers(self) -> dict:
        """获取API请求头"""
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers
    
    # def _validate_connection(self):
    #     """验证模型服务连通性"""
    #     try:
    #         response = requests.get(
    #             f"{self.api_url}/health",
    #             headers=self._get_headers(),
    #             timeout=5
    #         )
    #         response.raise_for_status()
    #     except requests.exceptions.RequestException as e:
    #         raise ConnectionError(f"无法连接到bge-m3模型服务 {self.api_url}: {e}")


    def _validate_connection(self):
        """验证 OpenAI 兼容的 embeddings 服务"""
        # 暂时注释掉连接验证，方便本地开发测试
        print("跳过embedding服务连接验证")
        return
        # try:
        #     # 直接测试 embeddings 端点，使用空文本或最短文本
        #     response = requests.post(
        #         f"{self.api_url}",
        #         headers={
        #             **self._get_headers(),
        #             "Content-Type": "application/json"
        #         },
        #         json={
        #             "model": "bge-m3",  # 或您的模型名称
        #             "input": ["test"]   # 最短测试文本
        #         },
        #         timeout=5
        #     )
        #     response.raise_for_status()
        #     
        #     # 验证返回的 embedding 格式
        #     result = response.json()
        #     if "data" not in result or not result["data"]:
        #         raise ConnectionError("服务返回了无效的 embedding 格式")
        #         
        # except requests.exceptions.HTTPError as e:
        #     if e.response.status_code == 404:
        #         raise ConnectionError(
        #             f"embeddings 端点不存在，请确认 API URL 是否正确。 "
        #             f"当前尝试的 URL: {self.api_url}"
        #         )
        #     else:
        #         raise ConnectionError(f"HTTP 错误: {e}")
        # except requests.exceptions.RequestException as e:
        #     raise ConnectionError(f"无法连接到服务: {e}")


    def _call_api(self, texts: List[str]) -> List[List[float]]:
        """调用embedding API"""
        try:
            payload = {
                "model": self.model_name,
                "input": texts,
                "normalize": True  # 确保向量归一化，对Milvus COSINE相似度很重要
            }
            
            response = requests.post(
                f"{self.api_url}",
                json=payload,
                headers=self._get_headers(),
                timeout=self.timeout
            )
            response.raise_for_status()
            
            # 解析响应（兼容OpenAI格式）
            result = response.json()
            
            if "data" in result:
                # OpenAI格式: {"data": [{"embedding": [...]}, ...]}
                embeddings = [item["embedding"] for item in sorted(result["data"], key=lambda x: x["index"])]
            elif "embeddings" in result:
                # 自定义格式: {"embeddings": [[...], ...]}
                embeddings = result["embeddings"]
            else:
                raise ValueError(f"API响应格式不支持: {result}")
            
            return embeddings
            
        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"API调用失败: {e}")
        except (KeyError, TypeError) as e:
            raise ValueError(f"API响应解析错误: {e}")
    
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """
        批量文档embedding
        """
        all_embeddings = []
        
        # 分批处理，避免请求过大
        for i in range(0, len(texts), self.batch_size):
            batch = texts[i:i + self.batch_size]
            batch_embeddings = self._call_api(batch)
            all_embeddings.extend(batch_embeddings)
        
        return all_embeddings
    
    def embed_query(self, text: str) -> List[float]:
        """
        单个查询embedding
        """
        return self.embed_documents([text])[0]


def get_embedding(settings: Settings) -> Embeddings:
    """
    初始化通过URL访问的bge-m3模型
    
    Args:
        settings: 配置对象，需包含:
                 - bge_api_url: 模型服务API地址
                 - bge_model_name: 模型名称（可选，默认"bge-m3"）
                 - bge_api_key: API密钥（可选）
                 
    Returns:
        Embeddings: 初始化后的embedding模型实例
    """
    return init_Embedding(
        api_url=settings.embed.base_url,
        model_name=settings.embed.model,
        api_key="None"
    )

if __name__ == "__main__":
    settings = Settings()
    embeddings = get_embedding(settings)
    print(embeddings.embed_query("你好"))