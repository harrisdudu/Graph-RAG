# chunk_builder.py
from typing import List, Dict
from segments import Segment
from langchain_text_splitters import RecursiveCharacterTextSplitter

class ChunkBuilder:
    def __init__(self, max_len: int = 500):
        self.max_len = max_len

    def build_chunks(self, segments: List[Segment]) -> List[Dict]:
        """
        输入：线性 segments 列表
        输出：chunk 列表，每个元素是：
        {
            "chunk_id": int,
            "text": str,           # 实际 chunk 文本
            "header_chain": [...], # 该 chunk 的基础 header 链（首段的 header_chain）
        }
        """
        chunks: List[Dict] = []
        chunk_id = 0
        i = 0
        n = len(segments)

        while i < n:
            seg = segments[i]
            base_chain = seg.header_chain  # 这个 chunk 的基础 header 链（previous headers + 当前标题）

            # 先把基础 header 链写到文本顶部
            lines: List[str] = []
            lines.extend(base_chain)

            # 记录“当前 chunk 已经使用的长度”
            cur_len = sum(len(line) + 1 for line in lines)  # +1 代表换行
            last_chain = base_chain

            # 把当前这个 segment 放进 chunk
            if seg.text:
                available = self.max_len - cur_len - 1

                if len(seg.text) > available:
                    splitter = RecursiveCharacterTextSplitter(
                        chunk_size=self.max_len - sum(len(h) + 1 for h in base_chain) - 1,
                        chunk_overlap=0
                    )
                    parts = splitter.split_text(seg.text)

                    for p in parts:
                        chunk_lines = base_chain + [p]
                        chunk_text = "\n".join(chunk_lines).rstrip("\n")
                        chunks.append({
                            "chunk_id": chunk_id,
                            "text": chunk_text,
                            "header_chain": base_chain
                        })
                        chunk_id += 1

                    i += 1
                    continue

                # 否则可以正常塞入当前 chunk
                lines.append(seg.text)
                cur_len += len(seg.text) + 1
            i += 1
            # 尝试继续塞后面的 segments
            while i < n:
                next_seg = segments[i]
                # 计算 next_seg 写入时需要增加的 header 行 + 正文长度

                # 计算与 last_chain 的公共前缀长度
                common_prefix_len = 0
                max_common = min(len(last_chain), len(next_seg.header_chain))
                for k in range(max_common):
                    if last_chain[k] == next_seg.header_chain[k]:
                        common_prefix_len += 1
                    else:
                        break

                # 需要额外打印的标题 = next_seg.header_chain[common_prefix_len:]
                extra_headers = next_seg.header_chain[common_prefix_len:]

                extra_header_text_len = sum(len(h) + 1 for h in extra_headers)
                extra_body_len = len(next_seg.text) + 1 if next_seg.text else 0
                extra_total = extra_header_text_len + extra_body_len

                if cur_len + extra_total > self.max_len:
                    # 塞不下，当前 chunk 完成
                    break

                # 否则，把 extra headers + 正文写入当前 chunk
                for h in extra_headers:
                    lines.append(h)
                if next_seg.text:
                    lines.append(next_seg.text)

                cur_len += extra_total
                last_chain = next_seg.header_chain
                i += 1

            chunk_text = "\n".join(lines).rstrip("\n")
            chunks.append({
                "chunk_id": chunk_id,
                "text": chunk_text,
                "header_chain": base_chain
            })
            chunk_id += 1

        return chunks
