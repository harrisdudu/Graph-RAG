import numpy as np
import networkx as nx
import requests
from typing import List, Tuple, Dict, Optional, Union
from dataclasses import dataclass
import torch
from sentence_transformers import SentenceTransformer
from abc import ABC, abstractmethod

# -------------------------- 模型配置常量（可扩展） --------------------------
# 内置支持的模型配置，key为model_name，value包含默认参数
BUILTIN_MODEL_CONFIGS = {
    "bge-m3": {
        "local_path": "BAAI/bge-m3",
        "remote_embedding_dim": 1024,
        "default_prompt": "为这个句子生成表示以用于检索相关文章：",
        "normalize": True
    },
    "bge-large-zh-v1.5": {
        "local_path": "BAAI/bge-large-zh-v1.5",
        "remote_embedding_dim": 1024,
        "default_prompt": "",
        "normalize": True
    },
    "all-MiniLM-L6-v2": {
        "local_path": "all-MiniLM-L6-v2",
        "remote_embedding_dim": 384,
        "default_prompt": "",
        "normalize": True
    },
    "text2vec-large-chinese": {
        "local_path": "shibing624/text2vec-large-chinese",
        "remote_embedding_dim": 1024,
        "default_prompt": "",
        "normalize": True
    }
}

# -------------------------- 嵌入模型抽象接口 --------------------------
class BaseEmbedModel(ABC):
    """所有嵌入模型的统一抽象接口"""
    def __init__(self, model_name: str):
        self.model_name = model_name
        self.builtin_config = BUILTIN_MODEL_CONFIGS.get(model_name, {})
        self.embedding_dim = self.builtin_config.get("remote_embedding_dim", 1024)

    @abstractmethod
    def encode(self, texts: List[str], **kwargs) -> np.ndarray:
        """生成文本嵌入向量（统一返回np.ndarray）"""
        pass

    @abstractmethod
    def get_embedding_dim(self) -> int:
        """获取嵌入维度"""
        pass

# -------------------------- 本地模型适配器 --------------------------
class LocalEmbedModel(BaseEmbedModel):
    """本地加载的嵌入模型适配器（支持bge-m3等所有SentenceTransformer兼容模型）"""
    def __init__(self, model_name: str, model_path: Optional[str] = None, device: str = "auto"):
        super().__init__(model_name)
        # 优先使用自定义路径，否则用内置默认路径
        self.model_path = model_path or self.builtin_config.get("local_path", model_name)
        self.device = device if device != "auto" else ("cuda" if torch.cuda.is_available() else "cpu")
        
        # 加载模型（兼容trust_remote_code）
        self.model = self._load_model()
        # 自动获取真实嵌入维度
        self.embedding_dim = self.model.get_sentence_embedding_dimension()

    def _load_model(self) -> SentenceTransformer:
        """加载本地模型（兼容不同模型的加载参数）"""
        try:
            # 基础加载参数
            load_kwargs = {"device": self.device}
            # 针对bge-m3等需要trust_remote_code的模型
            if "bge-m3" in self.model_name.lower():
                load_kwargs["trust_remote_code"] = True
            
            return SentenceTransformer(self.model_path, **load_kwargs)
        except Exception as e:
            raise RuntimeError(f"加载本地模型[{self.model_name}]失败：{str(e)}")

    def encode(self, texts: List[str], **kwargs) -> np.ndarray:
        """生成嵌入向量（自动适配模型特有参数）"""
        # 通用参数
        batch_size = kwargs.get("batch_size", 32)
        normalize = kwargs.get("normalize", self.builtin_config.get("normalize", True))
        show_progress_bar = kwargs.get("show_progress_bar", True)
        
        # 模型特有参数
        encode_kwargs = {
            "batch_size": batch_size,
            "normalize_embeddings": normalize,
            "show_progress_bar": show_progress_bar
        }
        
        # 为bge-m3添加专属参数
        if "bge-m3" in self.model_name.lower():
            encode_kwargs["prompt_name"] = kwargs.get("prompt_name", self.builtin_config.get("default_prompt", "s2p"))
        
        # 生成嵌入
        embeddings = self.model.encode(texts, **encode_kwargs)
        return embeddings

    def get_embedding_dim(self) -> int:
        return self.embedding_dim

# -------------------------- 远程模型适配器 --------------------------
class RemoteEmbedModel(BaseEmbedModel):
    """远程API调用的嵌入模型适配器（支持动态适配不同模型）"""
    def __init__(self, model_name: str, api_url: str, api_key: Optional[str] = None, embedding_dim: Optional[int] = None):
        super().__init__(model_name)
        self.api_url = api_url
        self.api_key = api_key
        # 优先使用自定义维度，否则用内置默认维度
        self.embedding_dim = embedding_dim or self.builtin_config.get("remote_embedding_dim", 1024)

    def encode(self, texts: List[str], **kwargs) -> np.ndarray:
        """调用远程API生成嵌入（统一适配不同模型的API参数）"""
        # 构造通用请求头
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        
        # 构造请求体（兼容主流嵌入API格式）
        data = {
            "model": self.model_name,  # 指定模型名
            "input": texts,
            # "parameters": {
            "batch_size": kwargs.get("batch_size", 32),
            "normalize": kwargs.get("normalize", self.builtin_config.get("normalize", True)),
            # 模型特有参数
            "prompt_name": kwargs.get("prompt_name", self.builtin_config.get("default_prompt", ""))
            # }

            # "messages": [
            #     {
            #     "role": "user",
            #     "content": "生成文本嵌入向量"
            #     }
            # ],
            # "prompt": kwargs.get("prompt_name", self.builtin_config.get("default_prompt", "")),
            # "normalized": true 
        }

        try:
            # 发送请求
            response = requests.post(
                self.api_url,
                json=data,
                headers=headers,
                timeout=kwargs.get("timeout", 60)
            )
            response.raise_for_status()
            result = response.json()
            
            # 兼容不同的响应格式
            embeddings_data = result.get("embeddings")
            
            # 处理OpenAI格式：{"data": [{"embedding": [...]}]}
            if embeddings_data is None and "data" in result:
                data_list = result.get("data")
                if isinstance(data_list, list) and len(data_list) > 0 and "embedding" in data_list[0]:
                    embeddings_data = [item["embedding"] for item in data_list]
            
            # 如果仍未找到有效嵌入数据，直接使用result（作为备选）
            if embeddings_data is None:
                embeddings_data = result
            
            # 确保返回二维数组
            embeddings = np.array(embeddings_data)
            if len(embeddings.shape) == 1:
                # 如果是一维数组，转换为二维数组（单样本情况）
                embeddings = embeddings.reshape(1, -1)
            elif len(embeddings.shape) != 2:
                # 如果不是二维数组，抛出异常
                raise ValueError(f"API返回的嵌入数据格式错误，当前维度：{len(embeddings.shape)}")
            
            return embeddings
        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"调用远程模型[{self.model_name}]失败：{str(e)}")

    def get_embedding_dim(self) -> int:
        return self.embedding_dim

# -------------------------- 模型工厂（核心：动态适配） --------------------------
class EmbedModelFactory:
    """模型工厂：根据model_name和配置动态创建对应模型实例"""
    @staticmethod
    def create_model(
        model_name: str,
        deploy_type: str = "local",
        **kwargs
    ) -> BaseEmbedModel:
        """
        创建嵌入模型实例
        :param model_name: 模型名称（如bge-m3、bge-large-zh-v1.5）
        :param deploy_type: 部署类型（local/remote）
        :param kwargs: 其他参数
            - local模式：model_path（可选）、device（可选）
            - remote模式：api_url（必填）、api_key（可选）、embedding_dim（可选）
        :return: 统一的嵌入模型实例
        """
        # 校验模型名
        if model_name not in BUILTIN_MODEL_CONFIGS and deploy_type == "local":
            print(f"警告：模型[{model_name}]不在内置配置中，将使用默认参数加载")
        
        # 创建对应模型
        if deploy_type == "local":
            return LocalEmbedModel(
                model_name=model_name,
                model_path=kwargs.get("model_path"),
                device=kwargs.get("device", "auto")
            )
        elif deploy_type == "remote":
            if not kwargs.get("api_url"):
                raise ValueError("远程模式必须指定api_url参数")
            return RemoteEmbedModel(
                model_name=model_name,
                # api_url=kwargs["api_url"],
                api_url=kwargs.get("api_url"),
                api_key=kwargs.get("api_key"),
                embedding_dim=kwargs.get("embedding_dim")
            )
        else:
            raise ValueError(f"不支持的部署类型：{deploy_type}，仅支持local/remote")

# -------------------------- 图结构核心类 --------------------------
class Graph:
    """完整的图结构类（保留核心功能）"""
    def __init__(self):
        self.graph = nx.MultiDiGraph()
        self.node_ids: List[str] = []
        self.node_embeddings: Optional[np.ndarray] = None
        self.node_name2id: Dict[str, str] = {}
        self.embedding_dim: Optional[int] = None

    def add_triple(self, head: str, relation: str, tail: str, **kwargs):
        """添加三元组到图中"""
        for node_name in [head, tail]:
            if node_name not in self.node_name2id:
                node_id = f"node_{len(self.node_name2id)}"
                self.node_name2id[node_name] = node_id
                self.node_ids.append(node_id)
                self.graph.add_node(node_id, name=node_name)
        
        head_id = self.node_name2id[head]
        tail_id = self.node_name2id[tail]
        self.graph.add_edge(head_id, tail_id, relation=relation,** kwargs)

    def set_node_embeddings(self, embeddings: np.ndarray):
        """设置节点嵌入向量"""
        if len(embeddings) != len(self.node_ids):
            raise ValueError(f"嵌入数量({len(embeddings)})与节点数量({len(self.node_ids)})不匹配")
        
        # 确保embeddings是二维数组
        if len(embeddings.shape) != 2:
            raise ValueError(f"嵌入必须是二维数组，当前维度：{len(embeddings.shape)}")
            
        self.node_embeddings = embeddings
        self.embedding_dim = embeddings.shape[1]
        for node_id, embedding in zip(self.node_ids, embeddings):
            self.graph.nodes[node_id]["embedding"] = embedding

    def get_node_embedding(self, node_name: str) -> Optional[np.ndarray]:
        """获取指定节点的嵌入向量"""
        return self.graph.nodes[self.node_name2id.get(node_name)].get("embedding") if node_name in self.node_name2id else None

    def get_triples(self) -> List[Tuple[str, str, str]]:
        """返回所有三元组"""
        id2name = {v: k for k, v in self.node_name2id.items()}
        return [(id2name[h], d["relation"], id2name[t]) for h, t, d in self.graph.edges(data=True)]

# -------------------------- 核心图构建函数 --------------------------
def build_graph(
    graph_triples: List[Tuple[str, str, str]],
    model_name: str,
    deploy_config: Dict
) -> Graph:
    """
    动态适配模型的图构建函数
    :param graph_triples: 实体关系三元组列表 [(头, 关系, 尾), ...]
    :param model_name: 嵌入模型名称（如bge-m3、bge-large-zh-v1.5）
    :param deploy_config: 部署配置
        - type: local/remote
        - 其他参数：根据部署类型不同，见EmbedModelFactory
    :return: 构建好的图对象
    """
    # 1. 初始化图并添加三元组
    graph = Graph()
    for idx, triple in enumerate(graph_triples):
        if len(triple) != 3:
            raise ValueError(f"三元组{idx}格式错误：{triple}")
        graph.add_triple(*triple, confidence=1.0)

    if not graph.node_ids:
        print("警告：无有效节点，跳过嵌入生成")
        return graph

    # 2. 动态创建嵌入模型
    deploy_type=deploy_config['type']
    print(f"初始化模型：{model_name}（部署类型：{deploy_type}）")
    embed_model = EmbedModelFactory.create_model(
        model_name=model_name,
        deploy_type=deploy_type,
        **deploy_config
    )

    # 3. 生成节点嵌入
    node_names = [graph.graph.nodes[node_id]["name"] for node_id in graph.node_ids]
    print(f"为{len(node_names)}个节点生成嵌入（维度：{embed_model.get_embedding_dim()}）")
    embeddings = embed_model.encode(
        node_names,
        batch_size=deploy_config.get("batch_size", 32),
        normalize=deploy_config.get("normalize", True)
    )

    # 4. 设置嵌入并返回
    graph.set_node_embeddings(embeddings)
    print(f"图构建完成：节点数={len(graph.node_ids)}, 边数={graph.graph.number_of_edges()}, 嵌入维度={graph.embedding_dim}")
    return graph

# -------------------------- 测试示例 --------------------------
if __name__ == "__main__":
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

