# 项目结构
text_splitter/
├── backend/                 # 后端代码
│   ├── core/               # 基础代码目录
│   │   ├── indexing/       # 索引相关核心逻辑
│   │   │   ├── build_entity_extract_chain.py # 实体提取链构建
│   │   │   ├── chunking.py         # 文本分块
│   │   │   ├── data_persistence.py # 数据持久化
│   │   │   ├── graph_build.py      # 图构建
│   │   │   ├── graph_vector_construction.py # 图向量构建
│   │   │   ├── tools/              # 索引工具
│   │   │   │   ├── ollama_embedding.py # Ollama 嵌入模型
│   │   │   │   └── ollama_llm.py       # Ollama LLM 模型
│   │   │   └── extract_entity.py   # 实体提取
│   │   ├── retrieval/      # 检索相关核心逻辑
│   │   │   ├── generate.py    # 结果生成
│   │   │   ├── pre_query.py   # 查询预处理
│   │   │   ├── rerank.py      # 结果重排
│   │   │   └── searching.py   # 检索实现
│   │   └── tools/           # 核心工具
│   │       ├── init_embed.py      # 嵌入模型初始化
│   │       ├── init_graph_db.py   # 图数据库初始化
│   │       ├── init_llm.py        # LLM 初始化
│   │       └── init_vector_db.py  # 向量数据库初始化
│   ├── service/            # 业务服务层
│   │   ├── graph_db_manager.py       # 图数据库管理
│   │   ├── index_service.py          # 索引服务
│   │   ├── knowledge_base_manager.py # 知识库管理
│   │   ├── retrieval_service.py      # 检索服务
│   │   └── vector_db_manager.py      # 向量数据库管理
│   ├── config.py           # 配置文件
│   ├── main.py             # 主入口文件
│   ├── readme.md           # 后端说明文档
│   ├── data/               # 后端数据目录
│   └── temp/               # 临时文件目录
├── frontend/               # Web UI 前端代码
│   ├── index.html          # 前端入口页面
│   ├── script.js           # JavaScript 代码
│   └── style.css           # CSS 样式
├── temp/                   # 全局临时文件目录
├── requirements.txt        # Python 依赖
└── readme.md               # 项目说明文档



