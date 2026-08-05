# AI RAG Starter

用于检索增强生成（RAG）的最小可用启动项目，面向作品展示和面试。

- 上传文档 → 构建 FAISS 向量索引 → 查询检索 → LLM 合成回答
- 本地嵌入：sentence-transformers `all-MiniLM-L6-v2`（轻量 CPU 可用）
- 可选 LLM：OpenAI（设置 `OPENAI_API_KEY` 后自动启用生成式回答）

## API 端点

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/health` | 健康检查 |
| GET | `/metrics` | Prometheus 指标 |
| POST | `/upload` | 上传文档（multipart file） |
| POST | `/index` | 构建/持久化 FAISS 索引 |
| POST | `/query` | 查询 `{"query": "..."}` |

## 快速开始

```bash
cp .env.example .env
./run_ops.sh up            # 启动服务
curl -F "file=@examples/sample.txt" http://localhost:8080/upload
./run_ops.sh index         # 构建索引
curl -X POST http://localhost:8080/query \
  -H "Content-Type: application/json" \
  -d '{"query":"什么是RAG?"}'
```

## 技术栈

Python 3.11 · FastAPI · sentence-transformers · FAISS-cpu · Prometheus · Docker · GitHub Actions
