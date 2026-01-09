
import os
import json
from typing import List, Tuple, Optional
import requests  # 用于调用远程API（如GPT、文心一言）
from transformers import pipeline, AutoTokenizer, AutoModelForCausalLM  # 用于本地模型（如Llama）

def simple_extract_entities(chunks: List[str], llm_model: str, api_key: Optional[str] = None, base_url: Optional[str] = None) -> List[Tuple[str, str, str]]:
    """
    从“出口食品检验检疫”文本块中提取实体和关系（适配政务服务领域）
    
    核心提取目标（基于文档Schema）：
    - 实体类型：事项名称、法律法规、实施机构、申请主体、申请材料、办理流程环节、结果文件、办理渠道、时限、收费标准等
    - 关系类型：设定依据、实施机构、申请条件、申请材料、办理流程、法定办结时限、承诺办结时限、结果名称、收费标准、办理地点等
    
    Args:
        chunks: 文本块列表（文档拆分后的片段）
        llm_model: LLM模型名称（支持"gpt-3.5-turbo"、"ernie-bot"、"llama-3"等）
        api_key: API密钥（远程模型需提供，本地模型无需）
        base_url: 模型服务地址（可选，本地模型或自定义API地址）
        
    Returns:
        list: 实体关系三元组列表，格式为[(实体1, 关系, 实体2), ...]
    """
    # 步骤1：定义领域专属Prompt（适配出口食品检验检疫文档）
    prompt_template = """
    任务：从以下政务服务文本中提取实体和关系，严格遵循给定的实体类型和关系类型，输出结构化JSON。
    实体类型限制：
    1. 事项名称：政务服务的具体名称
    2. 法律法规：相关法律、规章、办法等
    3. 实施机构：负责办理该事项的部门
    4. 申请主体：办理该事项的单位/个人
    5. 申请材料：办理所需提交的文件/凭证
    6. 办理流程环节：办理过程中的步骤（如申请、查验、评定等）
    7. 结果文件：办理完成后出具的凭证/单据
    8. 办理渠道：办理方式（线上/线下平台）
    9. 时限类型：法定办结时限、承诺办结时限、申请时间、审核时间等
    10. 收费相关：收费标准、收费依据
    11. 咨询监督：咨询电话、监督电话
    12. 其他核心实体：如检验检疫方式、适用对象等
    
    关系类型限制：
    1. 设定依据：事项基于某法律法规设立
    2. 实施机构：事项由某机构负责办理
    3. 申请条件：办理事项需满足的条件
    4. 申请材料：办理事项需提交的材料
    5. 办理流程：事项的办理步骤包含某环节
    6. 对应时限：事项对应某类时限（如法定办结时限）
    7. 结果名称：事项办理后出具的结果文件
    8. 收费标准：事项的收费规则
    9. 办理渠道：事项的办理方式/平台
    10. 咨询方式：事项的咨询电话
    11. 监督方式：事项的监督电话
    12. 检验检疫方式：事项包含的检验检疫措施
    13. 适用要求：事项需符合的标准/要求（如进口国标准、中国国标）
    
    输出格式要求（必须严格遵守，否则视为无效）：
    {{
        "entities": [{{"name": "实体名称", "type": "实体类型"}}],
        "relations": [{{"subject": "实体1", "predicate": "关系", "object": "实体2"}}]
    }}
    
    注意事项：
    1. 仅提取文本中明确存在的信息，不编造、不添加幻觉内容
    2. 实体名称需准确（如法律法规全称、机构全称），关系需匹配实体间逻辑
    3. 重复实体或关系仅保留1条，无需重复输出
    4. 若文本中无相关信息，对应字段留空列表
    
    待提取文本：
    {chunk_text}
    """
    
    # 步骤2：初始化LLM调用工具（区分远程API和本地模型）
    def call_llm(text: str) -> Optional[dict]:
        """调用LLM模型，返回提取结果（JSON格式）"""
        print(f"调用LLM模型 {llm_model}，输入文本：{text.strip()}")
        prompt = prompt_template.format(chunk_text=text.strip())
        
        # 远程API模型（如GPT、文心一言）
        if llm_model in ["gpt-3.5-turbo", "gpt-4"]:
            if not api_key:
                raise ValueError("调用OpenAI模型需提供api_key")
            headers = {"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"}
            data = {
                "model": llm_model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.1,  # 降低随机性，保证提取准确性
                "response_format": {"type": "json_object"}
            }
            response = requests.post(base_url, headers=headers, json=data, timeout=30)
            response.raise_for_status()
            content = response.json()["choices"][0]["message"]["content"]
        # 本地模型（如Llama 3、Qwen）
        elif llm_model in ["llama3.2", "Qwen3-32B", "mistral"] or llm_model.lower().startswith("qwen"):
            if not base_url:
                # 本地加载模型（需提前下载权重）
                tokenizer = AutoTokenizer.from_pretrained(base_url)  # base_url为本地模型路径
                model = AutoModelForCausalLM.from_pretrained(base_url, device_map="auto")
                pipe = pipeline("text-generation", model=model, tokenizer=tokenizer)
                prompt = f"用户需求：{prompt}\n请严格按照JSON格式输出结果，不要添加其他内容："
                outputs = pipe(prompt, max_new_tokens=1024, temperature=0.1, top_p=0.9)
                content = outputs[0]["generated_text"].split("请严格按照JSON格式输出结果，不要添加其他内容：")[-1]
            else:
                prompt = f"用户需求：{prompt}\n请严格按照JSON格式输出结果，不要添加其他内容："
                # 本地API服务（如vLLM部署）
                headers = {"Content-Type": "application/json"}
                data = {
                    "model": llm_model,
                    "messages": [
                        {
                        "role": "system",
                        "content": "你是一个专业的AI智能体技术助手，擅长解答RAG、智能体架构设计和工程化实现相关问题，回答简洁且有深度。"
                        },
                        {
                        "role": "user",
                        "content": prompt
                        }
                    ],
                    "temperature": 0.7,
                    "top_p": 0.8,
                    "max_tokens": 2048,
                    "stream": "false",
                    "stop": [],
                    "response_format": {"type": "json_object"}
                }
                response = requests.post(base_url, headers=headers, json=data, timeout=60)
                response.raise_for_status()
                content = response.json()["choices"][0]["message"]["content"]
                print("提取出的实体：",content)
        
        else:
            raise ValueError(f"不支持的模型：{llm_model}")
        
        # 解析JSON结果
        try:
            return json.loads(content.strip())
        except json.JSONDecodeError as e:
            print(f"LLM输出格式错误，无法解析JSON：{content[:200]}...")
            print(f"错误信息：{e}")
            return None
    
    # 步骤3：批量处理文本块，提取实体和关系
    all_triples = []
    entity_set = set()  # 去重：存储已提取的实体（name+type）
    relation_set = set()  # 去重：存储已提取的关系（subject+predicate+object）
    
    for chunk in chunks:
        if not chunk.strip():
            continue
        
        # 调用LLM提取
        result = call_llm(chunk)
        if not result or "relations" not in result:
            continue
        
        # 解析关系三元组，去重后添加
        for rel in result["relations"]:
            subject = rel.get("subject", "").strip()
            predicate = rel.get("predicate", "").strip()
            obj = rel.get("object", "").strip()
            
            # 过滤无效三元组
            if not (subject and predicate and obj):
                continue
            
            # 去重：避免重复添加相同三元组
            rel_key = (subject, predicate, obj)
            if rel_key not in relation_set:
                relation_set.add(rel_key)
                all_triples.append(rel_key)
    
    # 步骤4：返回最终的三元组列表
    return all_triples



def build_langchain_extract_chain(llm):
    from langchain_core.prompts import PromptTemplate
    from langchain_core.output_parsers import StrOutputParser
    extract_prompt = PromptTemplate(
        template="""
        指令：严格按照以下格式输出结果，**禁止添加任何思考过程、解释、说明文字**，仅输出实体列表和三元组！
        输出格式（必须严格遵守，无多余内容）：
        实体列表：实体1,实体2,实体3
        三元组：
        实体1|关系|实体2
        实体3|关系|实体4
        
        要求：
        1. 实体列表仅保留核心名词（如公司、产品、概念），长度≥2，去重；
        2. 三元组仅保留高置信度直接关系（置信度≥0.75），格式为「实体1|关系|实体2」，无空格；
        3. 仅输出上述格式内容，不添加任何额外文字！
        
        文本：{text}
        """,
        input_variables=["text"]
    )
    extract_chain = extract_prompt | llm | StrOutputParser()
    return extract_chain


def parse_llm_output(extract_result: str):
    """
    解析LLM输出，过滤思考过程，精准提取实体列表和三元组
    处理场景：
    1. 输出含思考过程（如“我需要先抽取实体...”）；
    2. 实体列表/三元组行有缩进/空格；
    3. 部分行格式错误（如少|的三元组）；
    """
    # 步骤1：过滤所有非目标行（仅保留实体列表和三元组相关行）
    clean_lines = []
    for line in extract_result.split("\n"):
        line = line.strip()
        # 跳过空行、思考过程行（含“思考/分析/首先/需要”等关键词）
        if not line or any(key in line for key in ["思考", "分析", "首先", "需要", "说明", "解释"]):
            continue
        clean_lines.append(line)
    
    # 步骤2：解析实体列表（兼容多种格式：实体列表：xxx / 实体列表:xxx / 实体：xxx）
    entity_list = []
    entity_line = None
    for line in clean_lines:
        if any(prefix in line for prefix in ["实体列表：", "实体列表:", "实体：", "实体:"]):
            entity_line = line
            break
    if entity_line:
        # 提取冒号后的内容，兼容中英文冒号
        entity_part = entity_line.split("：")[-1] if "：" in entity_line else entity_line.split(":")[-1]
        # 按逗号分割，过滤空值和无效字符
        entity_list = [e.strip() for e in entity_part.split(",") if e.strip() and len(e.strip()) >= 2]
    
    # 步骤3：解析三元组（仅保留含|且格式正确的行）
    triples = []
    for line in clean_lines:
        # 跳过实体列表行，仅处理三元组行
        if any(prefix in line for prefix in ["实体列表：", "实体列表:", "实体：", "实体:"]):
            continue
        # 仅保留含|且分割后为3部分的行
        if "|" in line:
            parts = [p.strip() for p in line.split("|")]
            if len(parts) == 3 and all(parts) and all(len(p) >= 2 for p in parts):
                triples.append("|".join(parts))
    
    # 步骤4：去重（避免重复实体/三元组）
    entity_list = list(set(entity_list))
    triples = list(set(triples))
    
    return entity_list, triples



# ------------------------------
# 使用示例
# ------------------------------
if __name__ == "__main__":

    import sys
    import os

    current_dir = os.path.dirname(os.path.abspath(__file__))
    # print("当前目录:", current_dir)
    parent_dir = os.path.dirname(current_dir)
    # print("父目录:", parent_dir)
    pre_parent_dir = os.path.dirname(parent_dir)
    # print("上一级目录:", pre_parent_dir)
    sys.path.insert(0, current_dir)
    sys.path.insert(0, parent_dir)
    sys.path.insert(0, pre_parent_dir)

    print("当前工作目录:", os.getcwd())
    print("Python 搜索路径:", sys.path)

    from chunking import kps_text_splitter
    from config import Settings
    from core.tools.init_llm import get_llm
    # 1. 读取文档内容（替换为实际文档文本）
    with open("./temp/出口食品检验检疫240523.txt", "r", encoding="utf-8") as f:
        doc_content = f.read()
    
    # 2. 拆分文档为文本块
    chunks = kps_text_splitter(doc_content, chunk_size=settings.chunk_size, chunk_overlap=settings.chunk_overlap)
    
    # 3. 调用提取函数（以GPT-3.5为例）
    try:
        settings = Settings()
        llm = get_llm(settings)
        extract_chain = build_langchain_extract_chain(llm)
        for chunk in chunks:
            extract_result = extract_chain.invoke({"text": chunk}).strip()
            entity_list, triples = parse_llm_output(extract_result)
        
            print("提取的实体关系三元组：")
            print(entity_list)
            print(triples)
            # for i, (s, p, o) in enumerate(triples, 1):
            #     print(f"{i}. ({s}, {p}, {o})")
    
    except Exception as e:
        print(f"提取失败：{e.__class__.__name__} - {e}")
