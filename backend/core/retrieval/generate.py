from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser


def generate_answer(query: str, merged_context: str, llm):
    generate_prompt = PromptTemplate(
        template=f"""
        请基于以下上下文回答问题，要求：
        1. 答案准确、简洁，优先使用核心文本，扩展文本作为补充；
        2. 若上下文无相关信息，直接回复“无相关答案”；
        3. 最后补充答案来源说明。
        
        注意：不需要返回思考过程。

        上下文：{merged_context}
        问题：{query}

        返回格式：
        大模型生成的答案；
        来源：展示具体来源和内容摘要
        """,
        input_variables=["context", "query"]
    )
    generate_chain = generate_prompt | llm | StrOutputParser()
    answer = generate_chain.invoke({"context": merged_context, "query": query})
    print(f"生成回答：{answer}")
    return answer