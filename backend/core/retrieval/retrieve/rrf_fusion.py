
def rrf_fusion(vector_results, extended_chunks_results, k=60, weights=[0.6, 0.4]):
    """
    RRF（倒数排名融合）核心实现
    :param vector_results: 向量检索结果，格式：[(doc_id1, score1), (doc_id2, score2), ...]
    :param extended_chunks_results: 图扩展文本块结果，格式：[(doc_id1, score1), (doc_id2, score2), ...]
    :param k: 平滑常数（默认60）
    :param weights: 各源权重，如[0.6, 0.4]对应向量检索和图扩展
    :return: 按RRF得分降序的文档列表，包含doc_id、rrf_score、original_score、source_type字段
    """
    doc_scores = {}
    doc_info = {}
    
    for rank, (doc_id, original_score) in enumerate(vector_results, start=1):
        rrf_score = weights[0] / (k + rank)
        if doc_id not in doc_scores:
            doc_scores[doc_id] = 0.0
            doc_info[doc_id] = {
                'doc_id': doc_id,
                'original_score': original_score,
                'source_type': 'main_chunk'
            }
        doc_scores[doc_id] += rrf_score
    
    for rank, (doc_id, original_score) in enumerate(extended_chunks_results, start=1):
        rrf_score = weights[1] / (k + rank)
        if doc_id not in doc_scores:
            doc_scores[doc_id] = 0.0
            doc_info[doc_id] = {
                'doc_id': doc_id,
                'original_score': original_score,
                'source_type': 'extend_chunk'
            }
        else:
            doc_info[doc_id]['source_type'] = 'both'
        doc_scores[doc_id] += rrf_score
    
    sorted_results = sorted(doc_scores.items(), key=lambda x: x[1], reverse=True)
    
    result = []
    for doc_id, rrf_score in sorted_results:
        result.append({
            'doc_id': doc_id,
            'rrf_score': rrf_score,
            'original_score': doc_info[doc_id]['original_score'],
            'source_type': doc_info[doc_id]['source_type']
        })
    
    return result