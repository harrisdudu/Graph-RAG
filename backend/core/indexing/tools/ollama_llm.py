import httpx

class OllamaLLM:
    """
    Ollama LLM模型包装类，用于与本地Ollama服务交互
    """
    def __init__(self, model="llama3.2", base_url="http://localhost:11434"):
        self.model = model
        self.base_url = base_url
        
    def generate(self, prompt, **kwargs):
        """
        生成文本响应
        
        Args:
            prompt: 输入提示文本
            **kwargs: 其他参数，如temperature、max_tokens等
            
        Returns:
            str: 生成的响应文本
        """
        url = f"{self.base_url}/api/generate"
        
        # 构建请求体
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False
        }
        
        # 添加额外参数
        if kwargs:
            payload.update(kwargs)
        
        # 发送请求
        response = httpx.post(url, json=payload)
        response.raise_for_status()
        
        # 解析响应
        return response.json()["response"]

    def chat(self, messages, **kwargs):
        """
        聊天模式生成响应
        
        Args:
            messages: 消息列表，格式为[{"role": "user", "content": "..."}, ...]
            **kwargs: 其他参数，如temperature、max_tokens等
            
        Returns:
            str: 生成的响应文本
        """
        url = f"{self.base_url}/api/chat"
        
        # 构建请求体
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False
        }
        
        # 添加额外参数
        if kwargs:
            payload.update(kwargs)
        
        # 发送请求
        response = httpx.post(url, json=payload)
        response.raise_for_status()
        
        # 解析响应
        return response.json()["message"]["content"]
