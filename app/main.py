"""
AI RAG Starter — FastAPI 主入口

提供文档上传、索引构建、查询检索、健康检查和 Prometheus 指标。
"""

import os
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST, Counter

from .rag import RAGEngine

app = FastAPI(title="AI RAG Starter")

# Prometheus 指标：RAG 请求计数
rag_requests_total = Counter("rag_requests_total", "RAG 查询总次数")

# RAG 引擎延迟初始化（避免 import 时加载 heavy deps，CI 友好）
_engine = None


def get_engine() -> RAGEngine:
    global _engine
    if _engine is None:
        _engine = RAGEngine()
    return _engine


class QueryRequest(BaseModel):
    query: str


@app.get("/health")
def health():
    """健康检查端点"""
    return {"status": "ok"}


@app.get("/metrics")
def metrics():
    """Prometheus 指标端点"""
    data = generate_latest()
    return Response(content=data, media_type=CONTENT_TYPE_LATEST)


@app.post("/upload")
async def upload(file: UploadFile = File(...)):
    """上传文档，保存到 DOCS_DIR"""
    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="文件为空")
    saved_path = get_engine().save_document(file.filename, content)
    return {"saved": saved_path}


@app.post("/index")
def build_index():
    """构建 FAISS 向量索引并持久化"""
    eng = get_engine()
    eng.build_index()
    return {"status": "indexed", "index_path": eng.index_path}


@app.post("/query")
def query(req: QueryRequest):
    """查询接口：检索 + 可选 LLM 合成回答"""
    rag_requests_total.inc()
    top_k = int(os.getenv("TOP_K", "3"))
    result = get_engine().query(req.query, top_k=top_k)
    return result
