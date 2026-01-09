def preprocess_query(query, embed_model, extractor):
    """
    预处理用户查询，生成查询嵌入和提取查询实体
    
    Args:
        query: 用户查询文本
        embed_model: 嵌入模型实例
        extractor: 实体提取器实例
        
    Returns:
        tuple: (query_embedding, query_entities)
    """
    # 对用户查询生成embedding
    query_embedding = embed_model.embed(query)

    # 解析查询中的实体（可选，提升图检索精度）
    query_entities = extractor.extract_entities(query)  # 输出：["张三"]
    
    return query_embedding, query_entities