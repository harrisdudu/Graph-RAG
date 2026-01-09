from sentence_transformers import CrossEncoder
import torch

def rerank_candidates(query: str, candidates: list, model_path: str = "./backend/model/local_models/BAAI/bge-reranker-base",top_k:int=3) -> list:
    """
    使用重排模型对候选文本列表进行重新排序
    
    Args:
        query: 查询语句（如用户问题）
        candidates: 待重排的候选文本列表
        model_name: 重排模型名称，默认使用BGE-reranker-large（效果好），也可选择轻量版BAAI/bge-reranker-base
    
    Returns:
        排序后的候选列表（按相关性从高到低），每个元素为 (文本, 得分)
    """
    # 1. 加载重排模型，自动适配GPU/CPU
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model = CrossEncoder(model_path, device=device)
    
    # 2. 构造模型输入：(查询, 候选文本) 对
    pairs = [(query, candidate) for chunkid, candidate, score in candidates]
    
    # 3. 计算相关性得分（得分越高，相关性越强）
    scores = model.predict(pairs)
    
    # 4. 结合文本和得分，按得分降序排序
    ranked_results = list(zip(candidates, scores))
    ranked_results.sort(key=lambda x: x[1], reverse=True)

    # 取相关性最强的top_k个
    top_k_results = ranked_results[:top_k]
    return top_k_results