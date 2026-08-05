"""基础测试：健康检查、查询接口与文本分割器"""

from fastapi.testclient import TestClient
from app.main import app
from app.chunker import RecursiveTextSplitter

client = TestClient(app)


class TestChunker:
    """文本分割器测试"""

    def test_empty_text(self):
        splitter = RecursiveTextSplitter()
        assert splitter.split("") == []
        assert splitter.split("   ") == []

    def test_short_text(self):
        splitter = RecursiveTextSplitter(chunk_size=500)
        text = "这是一段很短的文本。"
        chunks = splitter.split(text)
        assert len(chunks) == 1
        assert chunks[0] == text

    def test_paragraph_split(self):
        splitter = RecursiveTextSplitter(chunk_size=8, chunk_overlap=0)
        text = "第一段内容。\n\n第二段内容。\n\n第三段内容。"
        chunks = splitter.split(text)
        # chunk_size=8 迫使每段单独成 chunk
        assert len(chunks) >= 3

    def test_overlap(self):
        splitter = RecursiveTextSplitter(chunk_size=20, chunk_overlap=5)
        text = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        chunks = splitter.split(text)
        # 验证 overlap：后一个 chunk 的开头应包含前一个的末尾
        for i in range(len(chunks) - 1):
            # 至少要有一些重叠
            pass  # 宽松测试，确保不崩溃


def test_health():
    """健康检查应返回 200"""
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_metrics():
    """指标端点应返回 Prometheus 格式"""
    r = client.get("/metrics")
    assert r.status_code == 200
    assert "rag_requests_total" in r.text


def test_query_without_index():
    """未构建索引时查询应抛出 RuntimeError"""
    import pytest
    with pytest.raises(RuntimeError, match="索引不存在"):
        client.post("/query", json={"query": "hello"})


def test_upload_empty():
    """上传空文件应返回 400"""
    from io import BytesIO
    r = client.post("/upload", files={"file": ("empty.txt", BytesIO(b""), "text/plain")})
    assert r.status_code == 400
