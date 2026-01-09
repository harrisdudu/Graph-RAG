import httpx

class OllamaEmbedding:
    def __init__(self, model="bge-m3", base_url="http://localhost:11434"):
        self.model = model
        self.base_url = base_url
    
    def embed(self, text):
        """
        使用Ollama的模型生成文本嵌入
        
        Args:
            text: 要生成嵌入的文本
            
        Returns:
            list: 嵌入向量
        """
        url = f"{self.base_url}/api/embeddings"
        payload = {
            "model": self.model,
            "prompt": text
        }
        
        try:
            response = httpx.post(url, json=payload)
            response.raise_for_status()  # 检查是否有HTTP错误
            return response.json()["embedding"]
        except Exception as e:
            raise Exception(f"Ollama嵌入生成失败: {str(e)}")

class LocalOpenAIEmbedding:
    def __init__(self, model="text-embedding-ada-002", base_url="http://localhost:8000/v1"):
        self.model = model
        self.base_url = base_url
    
    def embed(self, text):
        """
        使用本地OpenAI API的模型生成文本嵌入
        
        Args:
            text: 要生成嵌入的文本
            
        Returns:
            list: 嵌入向量
        """
        url = f"{self.base_url}/embeddings"
        payload = {
            "model": self.model,
            "input": text
        }
        
        try:
            response = httpx.post(url, json=payload)
            response.raise_for_status()  # 检查是否有HTTP错误
            return response.json()["data"][0]["embedding"]
        except Exception as e:
            raise Exception(f"本地OpenAI嵌入生成失败: {str(e)}")
