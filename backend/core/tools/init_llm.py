import sys
import os

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
pre_parent_dir = os.path.dirname(parent_dir)
sys.path.insert(0, current_dir)
sys.path.insert(0, parent_dir)
sys.path.insert(0, pre_parent_dir)

from typing import List, Tuple, Dict, Optional
from langchain_openai import ChatOpenAI
from langchain_core.language_models.llms import BaseLLM
from config import Settings


def init_qwen3_32b_llm(llm_model: str, api_key: Optional[str] = None, base_url: Optional[str] = None) -> BaseLLM:
    """
    初始化LLM模型（支持本地模型和远程API）
    
    Args:
        llm_model: 模型名称（如"meta-llama/Llama-2-7b-chat-hf"）
        api_key: 远程API密钥（如OpenAI API Key）
        base_url: 远程API基础URL（如OpenAI API Base URL）
        
    Returns:
        BaseLLM: 初始化后的LLM模型实例
    """
    return ChatOpenAI(
        model=llm_model,
        temperature=0,
        api_key=api_key,
        base_url=base_url
    )


def get_llm(settings: Settings) -> BaseLLM:
    """
    根据配置初始化LLM模型
    
    Args:
        settings: 配置对象
        
    Returns:
        BaseLLM: 初始化后的LLM模型实例
    """
    return init_qwen3_32b_llm(
        llm_model=settings.llm.model,
        api_key=settings.llm.api_key,
        base_url=settings.llm.base_url
    )

if __name__ == "__main__":
    settings = Settings()
    llm = get_llm(settings)
    print(llm.invoke("你好"))