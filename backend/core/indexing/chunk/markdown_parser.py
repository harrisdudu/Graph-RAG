# markdown_parser.py
import re
from typing import List
from segments import Segment

HEADER_PATTERN = re.compile(r'^(#{1,6})\s+(.*)$')

class MarkdownParser:
    """
    将 Markdown 文本解析为线性 Segment 列表：
    每个 Segment = (header_chain, text)
    """

    def parse_to_segments(self, text: str) -> List[Segment]:
        lines = text.splitlines()

        header_chain: List[str] = []  # 当前 header 栈
        current_text_lines: List[str] = []
        segments: List[Segment] = []

        def flush_segment():
            """把当前 header_chain + text_lines 推成一个 Segment"""
            nonlocal current_text_lines
            if header_chain:
                body = "\n".join(current_text_lines).rstrip("\n")
                segments.append(Segment(header_chain=header_chain.copy(), text=body))
            current_text_lines = []

        for line in lines:
            m = HEADER_PATTERN.match(line)
            if m:
                # 这是一个标题行
                level = len(m.group(1))
                title_text = m.group(2).strip()
                header = f"{'#' * level} {title_text}"

                # 在遇到新标题前，先把之前的正文段刷新为一个 segment
                flush_segment()

                # 调整 header 栈长度到 level-1，然后压入新 header
                # 例：遇到 ### 时，header_chain 应为 [#, ##]，再 append ###。
                while len(header_chain) >= level:
                    header_chain.pop()
                header_chain.append(header)

            else:
                # 普通正文行
                current_text_lines.append(line)

        # 处理最后残留的正文
        flush_segment()

        # 注意：如果文首有不带标题的内容，会被丢弃（因为没有 header_chain）。
        # 你目前的文件是从 # 开始的，不会有问题。
        return segments
