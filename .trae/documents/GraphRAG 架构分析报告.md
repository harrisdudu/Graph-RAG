我已完成对 `Graph-RAG` 项目核心架构与执行流程的深度分析。

**1. 核心设计模式**
该项目采用 **双流架构 (Dual-Pipeline)**：
- **Indexing Pipeline (写入流)**: 负责将非结构化文档转化为结构化的向量索引和图谱数据。
- **Retrieval Pipeline (查询流)**: 负责实时的混合检索、重排序与生成。

**2. 详细执行流程**

**阶段一：Indexing (索引构建)**
1.  **Ingestion**: 接收 `.md/.txt` 文档，进行清洗。
2.  **Chunking**: 使用 `MarkdownParser` 和 `ChunkBuilder` 将长文档切分为 500字符左右的语义块。
3.  **Vectorization**: 计算 Chunk 向量并存入 **Milvus**。
4.  **Graph Construction**:
    - 利用 LLM 抽取实体 (Entities) 和关系 (Triples)。
    - 将数据写入 **Neo4j**，建立 `(Chunk)-[:CONTAINS]->(Entity)` 的连接，实现图文关联。

**阶段二：Retrieval (检索增强)**
1.  **Vector Search**: 首先通过向量相似度召回 Top-K 相关文档块。
2.  **Graph Expansion**: 以召回的 Chunk 为起点，在图谱中向外扩展 1 跳，获取关联的实体和隐藏上下文。
3.  **Rerank**: 使用 Cross-Encoder 模型对混合检索结果进行精细打分。
4.  **Generation**: 将 Top 结果填入 Prompt，由 LLM 生成带引用的回答。

**下一步计划**
我将为您生成一份详细的分析报告，包含关键代码路径引用和架构图解，帮助您快速掌握系统全貌。
