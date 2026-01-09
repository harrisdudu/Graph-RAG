from fastapi import FastAPI, UploadFile, File, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import asyncio
import os
from pathlib import Path
from config import Settings

# 导入知识库管理服务
from service.knowledge_base_manager import KnowledgeBaseManager
# 导入索引服务
from service.index_service import IndexService
# 导入向量数据库管理服务
from service.vector_db_manager import VectorDBManager
# 导入图数据库管理服务
from service.graph_db_manager import GraphDBManager
# 导入检索服务
from service.retrieval_service import RetrievalService

# 初始化知识库管理器
kb_manager = KnowledgeBaseManager()

# 全局索引服务实例
# index_service = None

# 全局向量数据库管理服务实例
# vector_db_manager = VectorDBManager(settings=Settings())

# 全局图数据库管理服务实例
# graph_db_manager = GraphDBManager(settings=Settings())

# 全局检索服务实例
# retrieval_service = None

# 初始化FastAPI
app = FastAPI(title="文本分割与索引服务")

# 跨域配置（允许前端访问）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境请替换为具体前端域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 知识库请求模型
class KnowledgeBaseCreateRequest(BaseModel):
    name: str
    description: str = ""

class KnowledgeBaseUpdateRequest(BaseModel):
    name: str = None
    description: str = None

class KnowledgeBaseSearchRequest(BaseModel):
    query: str
    library_name: str
    search_method: str = "keyword"
    top_k: int = 3

# 初始化索引服务
@app.on_event("startup")
async def startup_event():
    global index_service
    # 创建数据存储目录
    # Path("./data/faiss").mkdir(parents=True, exist_ok=True)
    # Path("./data/graph").mkdir(parents=True, exist_ok=True)
    
    # 初始化索引服务，传递配置参数
    # index_service = IndexService(config={
    #     "llm_model": "Qwen3-32B",
    #     "llm_model_base_url": "http://172.16.0.211:23001/v1/chat/completions",
    #     "api_key": "fake_key",
    #     "embed_model": "bge-m3",
    #     "embed_model_base_url": "http://172.16.0.211:10000/v1/embeddings",
    #     "embed_model_config": {
    #         "embedding_dim": 1024
    #     }
    # })
    print("IndexService初始化完成")
    
    # 初始化检索服务
    # global retrieval_service
    # retrieval_service = RetrievalService()
    # print("RetrievalService初始化完成")

# 1. 文件上传接口（支持txt/pdf/docx）
@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    # if not index_service:
    #     return {"code": 500, "msg": "IndexService未初始化", "data": None}
    
    # 创建临时文件目录（如果不存在）
    temp_dir = "./temp"
    Path(temp_dir).mkdir(parents=True, exist_ok=True)
    print(f"临时目录已创建：{temp_dir}")
    # 使用安全的方式生成临时文件名
    temp_file_path = Path(temp_dir) / f"temp_{os.urandom(8).hex()}_{file.filename}"
    print(f"临时文件路径：{temp_file_path}")
    
    try:
        # 保存临时文件
        with open(temp_file_path, "wb") as f:
            f.write(await file.read())
        
        # 读取文件内容
        with open(temp_file_path, "r", encoding="utf-8") as f:
            file_content = f.read()
        
        # 使用索引服务处理文件内容（异步调用）
        index_service = IndexService(settings=Settings())
        process_result = await asyncio.to_thread(index_service.process_text, file_content)
        
        # 删除临时文件
        Path(temp_file_path).unlink()
        
        return {
            "code": 200, 
            "msg": f"文件 {file.filename} 上传并处理完成", 
            "data": {
                "chunks_count": len(process_result['chunks']),
                "node_count": process_result['graph_info']['node_count']
            }
        }
    except Exception as e:
        # 确保临时文件被删除
        if Path(temp_file_path).exists():
            Path(temp_file_path).unlink()
        return {"code": 500, "msg": f"文件处理失败：{str(e)}", "data": None}

# 2. 文本导入接口
@app.post("/add-text")
async def add_text(text: str = Query(...)):
    # if not index_service:
    #     return {"code": 500, "msg": "IndexService未初始化", "data": None}
    try:
        # 使用索引服务处理文本内容（异步调用）
        index_service = IndexService(settings=Settings())
        process_result = await asyncio.to_thread(index_service.process_text, text)
        
        return {
            "code": 200, 
            "msg": "文本导入并处理完成", 
            "data": {
                "chunks_count": len(process_result['chunks']),
                # "triples_count": len(process_result['graph_triples']),
                "node_count": process_result['graph_info']['node_count']
            }
        }
    except Exception as e:
        return {"code": 500, "msg": f"文本导入失败：{str(e)}", "data": None}



# 知识库管理API
# 1. 创建知识库
@app.post("/knowledge-base")
async def create_knowledge_base(request: KnowledgeBaseCreateRequest):
    try:
        knowledge_base = kb_manager.create_knowledge_base(
            name=request.name,
            description=request.description
        )
        return {
            "code": 200,
            "msg": "知识库创建成功",
            "data": {
                "id": knowledge_base.id,
                "name": knowledge_base.name,
                "description": knowledge_base.description,
                "created_at": knowledge_base.created_at,
                "updated_at": knowledge_base.updated_at,
                "is_active": knowledge_base.is_active
            }
        }
    except Exception as e:
        return {"code": 500, "msg": f"知识库创建失败：{str(e)}", "data": None}

# 2. 获取所有知识库
@app.get("/knowledge-base")
async def get_all_knowledge_bases():
    try:
        knowledge_bases = kb_manager.get_all_knowledge_bases()
        data = [
            {
                "id": kb.id,
                "name": kb.name,
                "description": kb.description,
                "created_at": kb.created_at,
                "updated_at": kb.updated_at,
                "is_active": kb.is_active
            } for kb in knowledge_bases
        ]
        return {
            "code": 200,
            "msg": "获取知识库列表成功",
            "data": data
        }
    except Exception as e:
        return {"code": 500, "msg": f"获取知识库列表失败：{str(e)}", "data": None}

# 3. 获取单个知识库
@app.get("/knowledge-base/{kb_id}")
async def get_knowledge_base(kb_id: str):
    try:
        knowledge_base = kb_manager.get_knowledge_base(kb_id)
        if not knowledge_base:
            return {"code": 404, "msg": "知识库不存在", "data": None}
        
        return {
            "code": 200,
            "msg": "获取知识库成功",
            "data": {
                "id": knowledge_base.id,
                "name": knowledge_base.name,
                "description": knowledge_base.description,
                "created_at": knowledge_base.created_at,
                "updated_at": knowledge_base.updated_at,
                "is_active": knowledge_base.is_active
            }
        }
    except Exception as e:
        return {"code": 500, "msg": f"获取知识库失败：{str(e)}", "data": None}

# 4. 更新知识库
@app.put("/knowledge-base/{kb_id}")
async def update_knowledge_base(kb_id: str, request: KnowledgeBaseUpdateRequest):
    try:
        knowledge_base = kb_manager.update_knowledge_base(
            kb_id=kb_id,
            name=request.name,
            description=request.description
        )
        if not knowledge_base:
            return {"code": 404, "msg": "知识库不存在", "data": None}
        
        return {
            "code": 200,
            "msg": "更新知识库成功",
            "data": {
                "id": knowledge_base.id,
                "name": knowledge_base.name,
                "description": knowledge_base.description,
                "created_at": knowledge_base.created_at,
                "updated_at": knowledge_base.updated_at,
                "is_active": knowledge_base.is_active
            }
        }
    except Exception as e:
        return {"code": 500, "msg": f"更新知识库失败：{str(e)}", "data": None}

# 5. 删除知识库
@app.delete("/knowledge-base/{kb_id}")
async def delete_knowledge_base(kb_id: str):
    try:
        knowledge_base = kb_manager.delete_knowledge_base(kb_id)
        if not knowledge_base:
            return {"code": 404, "msg": "知识库不存在", "data": None}
        
        return {
            "code": 200,
            "msg": "删除知识库成功",
            "data": {
                "id": knowledge_base.id,
                "name": knowledge_base.name,
                "is_active": knowledge_base.is_active
            }
        }
    except Exception as e:
        return {"code": 500, "msg": f"删除知识库失败：{str(e)}", "data": None}

# 获取向量库中的所有数据
@app.get("/vector-db/all")
async def get_all_vectors():
    try:
        vector_db_manager = VectorDBManager(settings=Settings())
        vectors = await asyncio.to_thread(vector_db_manager.get_all_vectors)
        return {
            "code": 200,
            "msg": "获取所有向量数据成功",
            "data": vectors
        }
    except Exception as e:
        return {"code": 500, "msg": f"获取向量数据失败：{str(e)}", "data": None}

# 获取向量库中最近的向量数据
@app.get("/vector-db/latest")
async def get_latest_vectors(limit: int = Query(20, ge=1, le=100)):
    try:
        vector_db_manager = VectorDBManager(settings=Settings())
        vectors = await asyncio.to_thread(vector_db_manager.get_latest_vectors, limit=limit)
        return {
            "code": 200,
            "msg": "获取最近向量数据成功",
            "data": vectors
        }
    except Exception as e:
        return {"code": 500, "msg": f"获取向量数据失败：{str(e)}", "data": None}

# 获取图数据库中的所有节点
@app.get("/graph-db/nodes")
async def get_all_graph_nodes():
    try:
        graph_db_manager = GraphDBManager(settings=Settings())
        nodes = await asyncio.to_thread(graph_db_manager.get_all_nodes)
        return {
            "code": 200,
            "msg": "获取所有节点数据成功",
            "data": nodes
        }
    except Exception as e:
        return {"code": 500, "msg": f"获取节点数据失败：{str(e)}", "data": None}

# 获取图数据库中的所有关系
@app.get("/graph-db/relationships")
async def get_all_graph_relationships():
    try:
        graph_db_manager = GraphDBManager(settings=Settings())
        relationships = await asyncio.to_thread(graph_db_manager.get_all_relationships)
        return {
            "code": 200,
            "msg": "获取所有关系数据成功",
            "data": relationships
        }
    except Exception as e:
        return {"code": 500, "msg": f"获取关系数据失败：{str(e)}", "data": None}

# 获取完整的图数据（节点和关系）
@app.get("/graph-db/all")
async def get_all_graph_data():
    try:
        graph_db_manager = GraphDBManager(settings=Settings())
        graph_data = await asyncio.to_thread(graph_db_manager.get_graph_data)
        return {
            "code": 200,
            "msg": "获取完整图数据成功",
            "data": graph_data
        }
    except Exception as e:
        return {"code": 500, "msg": f"获取图数据失败：{str(e)}", "data": None}

# 获取图数据库统计信息
@app.get("/graph-db/stats")
async def get_graph_stats():
    try:
        graph_db_manager = GraphDBManager(settings=Settings())
        stats = await asyncio.to_thread(graph_db_manager.get_graph_stats)
        return {
            "code": 200,
            "msg": "获取图统计信息成功",
            "data": stats
        }
    except Exception as e:
        return {"code": 500, "msg": f"获取图统计信息失败：{str(e)}", "data": None}

# 根据chunkid获取图数据库中实体
@app.get("/graph-db/nodesById")
async def get_graph_nodes_by_id(chunk_id: str = Query(...)):
    try:
        graph_db_manager = GraphDBManager(settings=Settings())
        nodes = await asyncio.to_thread(graph_db_manager.get_graph_data_by_id, chunk_id)
        return {
            "code": 200,
            "msg": "根据chunk_id获取实体成功",
            "data": nodes
        }
    except Exception as e:
        return {"code": 500, "msg": f"获取节点数据失败：{str(e)}", "data": None}

# 检索接口
@app.get("/retrieval")
async def retrieval(query: str = Query(...)):
    # if not retrieval_service:
    #     return {"code": 500, "msg": "RetrievalService未初始化", "data": None}
    
    try:
        # 处理查询
        retrieval_service = RetrievalService(settings=Settings())
        results,vector_chunks,extended_chunks = await asyncio.to_thread(retrieval_service.process_query, query)
        return {
            "code": 200,
            "msg": "检索成功",
            "data": results,
            "vector_chunks": vector_chunks,
            "extended_chunks": extended_chunks
        }
    except Exception as e:
        return {"code": 500, "msg": f"检索失败：{str(e)}", "data": None}

# 处理socket.io请求（避免404错误）
@app.get("/socket.io/")
@app.post("/socket.io/")
async def handle_socketio():
    return {"code": 400, "msg": "Socket.io服务未启用"}


@app.post("/kb/search")
async def kb_search(request: KnowledgeBaseSearchRequest):
    try:
        # if not retrieval_service:
        #     return {"code": 500, "msg": "RetrievalService未初始化", "data": None}
        
        
        settings = Settings()
        settings.graph_store.uri = "bolt://192.168.0.197:27687"
        settings.vector_store.port = "29530"
        settings.graph_store.biz_label = request.library_name
        settings.vector_store.collection_name = request.library_name
        
        kb_retrieval_service = RetrievalService(settings)
        results, vector_chunks, extended_chunks = kb_retrieval_service.process_query(request.query, request.search_method)
        
        context = []
        for chunk in vector_chunks:
            context.append({
                "content": chunk.page_content,
                "metadata": {
                    "confidence_score": 0.98,
                    "source_type": request.library_name,
                    "library": request.library_name,
                    "filename": chunk.metadata["filename"],
                    "page": 1,
                    "keywords": [chunk.metadata["file_tag1"],chunk.metadata["file_tag2"]]
                }
            })
        
        return {
            "code": 200,
            "msg": "检索成功",
            "data": {
                # "query": request.query,
                # "answer": results,
                "context": context
            }
        }
    except Exception as e:
        return {"code": 500, "msg": f"检索失败：{str(e)}", "data": None}


if __name__ == "__main__":
    import uvicorn
    # 安装依赖：pip install uvicorn python-multipart
    uvicorn.run(app, host="0.0.0.0", port=8000)