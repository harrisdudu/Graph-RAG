import sys
import os
from docx import Document  # 需要先安装 python-docx 库


# 将backend目录添加到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.indexing.chunking import kps_text_splitter
from core.indexing.build_entity_extract_chain import build_langchain_extract_chain
from core.indexing.graph_vector_construction import build_graph2vector
from config import Settings
from core.tools.init_llm import get_llm
from core.tools.init_embed import get_embedding
from core.tools.init_vector_db import get_vector_db
from core.tools.init_graph_db import get_graph_db, check_neo4j_details
from core.indexing.chunk.content_split import content_split_run

class IndexService:
    def __init__(self, settings: Settings, config=None):
        self.llm = get_llm(settings)
        self.embeddings = get_embedding(settings)
        self.vector_db = get_vector_db(settings, self.embeddings)
        self.graph_db = get_graph_db(settings)
        self.index_settings = settings
    
    def process_md(self, doc_content, file_params:dict):
        """
        处理文本的完整流程：分块 -> 提取实体关系 -> 构建图
        
        Args:
            text: 待处理的长文本
            
        Returns:
            dict: 处理结果，包含chunks、graph_triples、graph_info等信息
        """
        # 1. 文本分块
        chunks = content_split_run(doc_content, chunk_size=self.index_settings.split.chunk_size, chunk_overlap=self.index_settings.split.chunk_overlap)
        print(f"文本分块完成，共得到 {len(chunks)} 个块")
        
        # 2. 构建提取实体和关系模版 
        extract_chain = build_langchain_extract_chain(self.llm)
        print(f"提取实体和关系模版构建完成")

        # 3. 构建图结构 
        build_graph2vector(settings=self.index_settings, chunks=chunks, vector_db=self.vector_db, graph_db=self.graph_db, extract_chain=extract_chain,file_params=file_params)
        print(f"图构建完成")
        # print(f"图构建完成，包含 {check_neo4j_details(self.graph_db)} 个节点")
        
        # 返回处理结果
        return {
            "chunks": chunks,
            "graph_info": {
                "node_count": check_neo4j_details(self.graph_db)
            },
            "status": "success"
        }
        # return {
        #     "chunks": chunks,
        #     "graph_triples": graph_triples,
        #     "graph_info": {
        #         "node_count": len(graph.node_ids),
        #         "node_embeddings_shape": graph.node_embeddings.shape if graph.node_embeddings is not None else None
        #     },
        #     "persist_success": success
        # }

    def process_text(self, doc_content, file_params:dict):
        """
        处理文本的完整流程：分块 -> 提取实体关系 -> 构建图
        
        Args:
            text: 待处理的长文本
            
        Returns:
            dict: 处理结果，包含chunks、graph_triples、graph_info等信息
        """
        # 1. 文本分块
        chunks = kps_text_splitter(doc_content, chunk_size=self.index_settings.split.chunk_size, chunk_overlap=self.index_settings.split.chunk_overlap)
        print(f"文本分块完成，共得到 {len(chunks)} 个块")
        
        # 2. 构建提取实体和关系模版 
        extract_chain = build_langchain_extract_chain(self.llm)
        print(f"提取实体和关系模版构建完成")

        # 3. 构建图结构 
        build_graph2vector(settings=self.index_settings, chunks=chunks, vector_db=self.vector_db, graph_db=self.graph_db, extract_chain=extract_chain,file_params=file_params)
        print(f"图构建完成")
        # print(f"图构建完成，包含 {check_neo4j_details(self.graph_db)} 个节点")
        
        # 返回处理结果
        return {
            "chunks": chunks,
            "graph_info": {
                "node_count": check_neo4j_details(self.graph_db)
            },
            "status": "success"
        }


# 使用示例
if __name__ == "__main__":
    # 创建索引服务实例
    settings = Settings()
    settings.graph_store.uri = "bolt://192.168.0.197:27687"
    settings.vector_store.port = "29530"
    
    settings.graph_store.biz_label = "kb_flfg"
    settings.vector_store.collection_name = "kb_flfg"
    
    # settings.graph_store.biz_label = "Knowledge2"
    # settings.vector_store.collection_name = "graph_entities2"
    index_service = IndexService(settings)
    
    # 待处理的长文本 - 从本地文件出口食品检验检疫240523.txt读取
    try:
        # 读取本地文件内容
        # file_path="./temp/出口食品检验检疫240523.txt"
        # file_path="./temp/安徽省地方金融条例_法律法规_地方法规.md"
        file_path="./temp/青岛市金融发展促进条例_地方法规_政策法规.md"
        file_ext = os.path.splitext(file_path)[1].lower()
        file_tag_1 = None
        file_tag_2 = None
        file_params = {
            "file_tag1": file_tag_1 if file_tag_1 else None,
            "file_tag2": file_tag_2 if file_tag_2 else None
        }
        if file_ext == '.txt':
            # 读取txt文件
            with open(file_path, "r", encoding="utf-8") as f:
                text = f.read()
            # 处理文本
            result = index_service.process_text(text, file_params)
        elif file_ext == '.md':
            full_file_name = os.path.splitext(file_path)[0].lower()
            file_tag_1 = full_file_name.split('_')[1]
            file_tag_2 = full_file_name.split('_')[2]
            # 读取md文件
            file_params = {
                "file_tag1": file_tag_1 if file_tag_1 else None,
                "file_tag2": file_tag_2 if file_tag_2 else None
            }
            with open(file_path, "r", encoding="utf-8") as f:
                text = f.read()
            # 处理文本
            result = index_service.process_md(text, file_params)
        elif file_ext == '.docx':
            # 读取docx文件
            doc = Document(file_path)
            # 拼接docx中所有段落的文本
            text = '\n'.join([para.text for para in doc.paragraphs])
            # 处理文本
            result = index_service.process_text(text, file_params)
        else:
            raise ValueError(f"不支持的文件格式：{file_ext}，仅支持 .txt/.md 和 .docx")
        print(f"成功读取文件：{file_path}")
        
        # 处理文本
        # result = index_service.process_text(text)
        
        # 打印结果
        print("\n处理结果：")
        print(f"分块数：{len(result['chunks'])}")
        # print(f"三元组数：{len(result['graph_triples'])}")
        # print(f"节点数：{result['graph_info']['node_count']}")
        
    except FileNotFoundError:
        print("错误：文件【北京市地方金融监督管理条例.docx】未找到")
        sys.exit(1)
    except Exception as e:
        print(f"读取文件时发生错误：{e}")
        sys.exit(1)
    
