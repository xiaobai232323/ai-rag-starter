# 使用指南

## 环境准备

```bash
cp .env.example .env
# 可选：编辑 .env 设置 OPENAI_API_KEY 启用生成式回答
```

## 启动服务

```bash
./run_ops.sh up
```

## 上传文档

```bash
curl -F "file=@examples/sample.txt" http://localhost:8080/upload
```

## 构建索引

```bash
./run_ops.sh index
```

## 查询

```bash
curl -X POST http://localhost:8080/query \
  -H "Content-Type: application/json" \
  -d '{"query":"什么是RAG?"}'
```

## 健康检查

```bash
curl http://localhost:8080/health
```

## 停止服务

```bash
./run_ops.sh down
```
