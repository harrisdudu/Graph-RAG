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

from markdown_parser import MarkdownParser
from chunk_builder import ChunkBuilder
import re

def read_markdown(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        text = f.read()
    return text

def remove_image(text: str) -> str:
    """删除 markdown 中的图片链接"""
    return re.sub(r'!\[.*?]\([^)]*\)', '', text)

def remove_toc_lines_basic(markdown_text):
    """
    删除包含多个点的目录行（基础版本）
    """
    # 匹配以点或空格开头，包含多个点，以数字结尾的行
    pattern = r'^[\s.]*\.{3,}[\s\d]*\d+\s*$'
    
    lines = markdown_text.split('\n')
    filtered_lines = []
    
    for line in lines:
        if not re.match(pattern, line.strip()):
            if "......" not in line:
                filtered_lines.append(line)
    
    return '\n'.join(filtered_lines)

def remove_special_page_tags_with_info(content: str):
    """
    去除内容中的所有 special_page_num_tag 并将其替换为换行符，
    同时返回所有被移除的页码
    
    参数:
    content: 包含特殊标签的文本内容
    
    返回:
    (处理后的文本内容, 页码列表)
    """
    # 定义正则表达式模式
    pattern = r'<special_page_num_tag>(\d+)</special_page_num_tag>'
    
    # 替换所有标签为换行符
    result = re.sub(pattern, '\n', content)
    
    return result

def content_split_run(text: str, chunk_size: int = 500, chunk_overlap: int = 100):
    text = remove_image(remove_special_page_tags_with_info(remove_toc_lines_basic(text)))

    parser = MarkdownParser()
    segments = parser.parse_to_segments(text)

    builder = ChunkBuilder(max_len=chunk_size)
    chunks = builder.build_chunks(segments)

    # 转为数组结构
    # chunks_array =  [text for id,text,headerchain in chunks]
    chunks_array = [item["text"] for item in chunks]

    return chunks_array

def test_run(md_path, output_path):
    text = read_markdown(md_path)
    text = remove_image(remove_special_page_tags_with_info(remove_toc_lines_basic(text)))

    parser = MarkdownParser()
    segments = parser.parse_to_segments(text)

    builder = ChunkBuilder(max_len=500)
    chunks = builder.build_chunks(segments)

    txt = ""
    c_texts = [c["text"] for c in chunks]
    txt = "\n ================================================================= \n".join(c_texts)
    with open(output_path, "w", encoding="utf-8") as fw:
        fw.write(txt)



if __name__ == "__main__":
    from glob import glob
    from tqdm import tqdm
    import os
    output_dir = f"D:/bbb"
    input_dir = f"C:/Users/hando/Desktop/aaa"
    input_files = glob(f"{input_dir}/**/*.md", recursive=True)
    input_files = [input_files[0]]
    for file in tqdm(input_files):
        output_path = os.path.join(output_dir, os.path.basename(file).replace(".md", "_chunked.txt"))
        print(output_path)
        test_run(file, output_path)