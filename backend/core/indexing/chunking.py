def simple_chunk_splitter(text, chunk_size=512, chunk_overlap=50):
    """
    将文本切分为语义块
    
    Args:
        text: 待切分的长文本
        chunk_size: 块大小
        chunk_overlap: 块重叠大小
        
    Returns:
        list: 切分后的文本块列表
    """
    # 使用简单的字符分块策略
    chunks = []
    start = 0
    text_length = len(text)
    
    while start < text_length:
        end = start + chunk_size
        # 如果不是最后一块，尝试在句子边界处分割
        if end < text_length:
            # 寻找最近的句号、问号或感叹号
            punctuation = text.rfind('.', start, end)
            if punctuation == -1:
                punctuation = text.rfind('?', start, end)
            if punctuation == -1:
                punctuation = text.rfind('!', start, end)
            if punctuation != -1:
                end = punctuation + 1
        # 添加块
        chunks.append(text[start:end].strip())
        # 更新起始位置，考虑重叠
        start = end - chunk_overlap
    
    return chunks


def kps_text_splitter(documents,chunk_size, chunk_overlap):
    from langchain_text_splitters  import RecursiveCharacterTextSplitter
    """
    将文本切分为语义块
    
    Args:
        documents: 待切分的长文本
        chunk_size: 块大小
        chunk_overlap: 块重叠大小
        
    Returns:
        list: 切分后的文本块列表
    """
    # 步骤1：文档分块（轻量配置，控制Token）
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", "。", "！", "？", "，", "、", " "]
    )
    chunks = text_splitter.split_text("\n".join(documents))
    print(f"文档分块完成，共{len(chunks)}块")
    return chunks