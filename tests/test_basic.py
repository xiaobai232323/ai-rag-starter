"""基础测试：健康检查与查询接口"""

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


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
    """未构建索引时查询应返回 500"""
    r = client.post("/query", json={"query": "hello"})
    assert r.status_code == 500


def test_upload_empty():
    """上传空文件应返回 400"""
    from io import BytesIO
    r = client.post("/upload", files={"file": ("empty.txt", BytesIO(b""), "text/plain")})
    assert r.status_code == 400
