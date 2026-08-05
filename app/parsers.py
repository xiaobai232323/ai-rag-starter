"""
文档解析器：支持 TXT / PDF / DOCX 格式。

PDF 和 DOCX 依赖为可选，仅在调用对应解析函数时才导入。
"""

from pathlib import Path
from typing import Optional


def parse_file(file_path: Path) -> str:
    """根据文件扩展名自动选择解析器，返回纯文本内容"""
    ext = file_path.suffix.lower()

    if ext == ".pdf":
        return parse_pdf(file_path)
    elif ext in (".docx", ".doc"):
        return parse_docx(file_path)
    elif ext in (".txt", ".md", ".csv", ".json", ".xml", ".html", ".py", ".java", ".c", ".cpp", ".h"):
        return parse_text(file_path)
    else:
        # 未知格式，尝试当纯文本读
        return parse_text(file_path)


def parse_text(file_path: Path) -> str:
    """读取纯文本文件"""
    return file_path.read_text(encoding="utf-8", errors="ignore")


def parse_pdf(file_path: Path) -> str:
    """解析 PDF 文件，提取文本内容（需要 PyPDF2）"""
    try:
        from PyPDF2 import PdfReader
    except ImportError:
        raise ImportError(
            "PDF 解析需要 PyPDF2，请执行: pip install PyPDF2"
        )

    reader = PdfReader(str(file_path))
    pages: list[str] = []
    for page in reader.pages:
        text = page.extract_text()
        if text:
            pages.append(text)
    return "\n\n".join(pages)


def parse_docx(file_path: Path) -> str:
    """解析 DOCX 文件，提取文本内容（需要 python-docx）"""
    try:
        from docx import Document
    except ImportError:
        raise ImportError(
            "DOCX 解析需要 python-docx，请执行: pip install python-docx"
        )

    doc = Document(str(file_path))
    paragraphs: list[str] = []
    for para in doc.paragraphs:
        if para.text.strip():
            paragraphs.append(para.text)
    return "\n".join(paragraphs)
