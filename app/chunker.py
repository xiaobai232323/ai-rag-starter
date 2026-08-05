"""
递归文本分割器：按分隔符逐级切分，支持 chunk_size 和 chunk_overlap 配置。

不依赖 LangChain，独立实现相同逻辑。
"""

from typing import List


class RecursiveTextSplitter:
    """递归文本分割器

    依次尝试按分隔符列表切分文本，直到每个 chunk 小于 chunk_size。
    分隔符优先级从粗到细：段落 → 句子 → 空格 → 字符。
    """

    def __init__(
        self,
        chunk_size: int = 500,
        chunk_overlap: int = 50,
        separators: List[str] | None = None,
    ):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.separators = separators or [
            "\n\n",     # 段落
            "\n",       # 换行
            "。",       # 中文句号
            ". ",       # 英文句号+空格
            "；",       # 中文分号
            "; ",       # 英文分号
            "，",       # 中文逗号
            ", ",       # 英文逗号
            " ",        # 空格
            "",         # 逐字符
        ]

    def split(self, text: str) -> List[str]:
        """分割文本为 chunk 列表"""
        if not text.strip():
            return []
        return self._split_text(text, self.separators)

    def _split_text(self, text: str, separators: List[str]) -> List[str]:
        """递归切分"""
        final_chunks = []
        # 选当前最优分隔符
        separator = self._choose_separator(text, separators)
        if separator is None:
            return [text]

        splits = text.split(separator) if separator else list(text)

        good_splits = []
        for s in splits:
            if len(s) < self.chunk_size:
                good_splits.append(s)
            else:
                if good_splits:
                    merged = self._merge_splits(good_splits, separator)
                    final_chunks.extend(merged)
                    good_splits = []
                # 用下一级分隔符继续切分
                remaining_seps = separators[separators.index(separator) + 1:]
                if remaining_seps:
                    final_chunks.extend(self._split_text(s, remaining_seps))
                else:
                    final_chunks.append(s)

        if good_splits:
            merged = self._merge_splits(good_splits, separator)
            final_chunks.extend(merged)

        return final_chunks

    def _choose_separator(self, text: str, separators: List[str]) -> str | None:
        """选择 text 中存在的最高优先级分隔符"""
        for sep in separators:
            if sep in text:
                return sep
        return None

    def _merge_splits(self, splits: List[str], separator: str) -> List[str]:
        """合并短片段，保持 chunk_size + overlap"""
        merged = []
        current = ""
        for s in splits:
            if not current:
                current = s
            elif len(current) + len(separator) + len(s) <= self.chunk_size:
                current += separator + s
            else:
                merged.append(current)
                # overlap: 保留上一段的末尾作为下一段的开始
                if self.chunk_overlap > 0 and len(current) > self.chunk_overlap:
                    current = current[-self.chunk_overlap:] + separator + s
                else:
                    current = s

        if current:
            merged.append(current)

        return merged
