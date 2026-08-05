"""
RAG 引擎核心：文档存储、嵌入、FAISS 索引、检索、LLM 合成回答。

改动说明：
- _llm_synthesize 使用 OpenAI Chat Completions（可配置模型 via OPENAI_CHAT_MODEL，默认 gpt-3.5-turbo）
- 返回的生成回答会要求模型在回答中引用来源编号（[来源1] 等），并且在失败时回退到拼接的检索片段
- 嵌入与索引逻辑保持不变
"""

import os
import json
import hashlib
from pathlib import Path
from typing import List, Dict, Any

# 重量级依赖延迟导入，以加速 CI 和冷启动
# numpy / faiss / SentenceTransformer 仅在首次调用嵌入或索引时加载


class RAGEngine:
    """RAG 引擎：嵌入 + FAISS 索引 + 检索 + 可选 OpenAI 合成回答"""

    def __init__(self):
        self.docs_dir = Path(os.getenv("DOCS_DIR", "data/docs"))
        self.index_dir = Path(os.getenv("INDEX_DIR", "data/index"))
        self.docs_dir.mkdir(parents=True, exist_ok=True)
        self.index_dir.mkdir(parents=True, exist_ok=True)

        self.embedding_model_name = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
        self.openai_key = os.getenv("OPENAI_API_KEY", "")
        # OpenAI chat model name (configurable)
        self.openai_chat_model = os.getenv("OPENAI_CHAT_MODEL", "gpt-3.5-turbo")

        self._embedder = None
        self._index = None
        self._metas: List[Dict[str, str]] = []

        self.index_path = str(self.index_dir / "faiss.index")
        self.meta_path = str(self.index_dir / "metas.json")

    # ── 嵌入模型懒加载 ──────────────────────────────────────

    def _load_embedder(self):
        if self._embedder is None:
            from sentence_transformers import SentenceTransformer
            print(f"[RAG] 加载嵌入模型: {self.embedding_model_name}")
            self._embedder = SentenceTransformer(self.embedding_model_name)
        return self._embedder

    # ── 文档管理 ────────────────────────────────────────────

    def save_document(self, filename: str, content: bytes) -> str:
        """保存文档到 docs_dir，按段落分割用于后续索引"""
        h = hashlib.sha1(content).hexdigest()[:10]
        out_name = f"{h}_{filename}"
        out_path = self.docs_dir / out_name
        out_path.write_bytes(content)
        return str(out_path)

    def _load_docs(self) -> List[Dict[str, Any]]:
        """加载所有文档并按段落切分"""
        docs = []
        for p in sorted(self.docs_dir.glob("*")):
            if p.is_dir():
                continue
            text = p.read_text(errors="ignore")
            # 简单按空行切段落
            parts = [s.strip() for s in text.split("\n\n") if s.strip()]
            for i, part in enumerate(parts):
                docs.append({"id": f"{p.name}_{i}", "text": part, "source": str(p)})
        return docs

    # ── 索引构建 ────────────────────────────────────────────

    def build_index(self):
        """构建 FAISS 向量索引并持久化到磁盘"""
        import faiss
        import numpy as np
        docs = self._load_docs()
        if not docs:
            print("[RAG] 没有需要索引的文档。")
            return

        texts = [d["text"] for d in docs]
        embedder = self._load_embedder()
        embs = embedder.encode(texts, show_progress_bar=True, convert_to_numpy=True)
        dim = embs.shape[1]

        index = faiss.IndexFlatL2(dim)
        index.add(embs.astype("float32"))
        faiss.write_index(index, self.index_path)

        metas = [
            {"id": d["id"], "text": d["text"], "source": d["source"]} for d in docs
        ]
        with open(self.meta_path, "w", encoding="utf-8") as f:
            json.dump(metas, f, ensure_ascii=False, indent=2)

        self._index = index
        self._metas = metas
        print(f"[RAG] 索引完成，共 {len(docs)} 个文本块。")

    # ── 索引加载 ────────────────────────────────────────────

    def _ensure_index(self):
        """确保索引已加载到内存"""
        import faiss
        if self._index is None:
            if Path(self.index_path).exists() and Path(self.meta_path).exists():
                self._index = faiss.read_index(self.index_path)
                with open(self.meta_path, "r", encoding="utf-8") as f:
                    self._metas = json.load(f)
            else:
                raise RuntimeError("索引不存在，请先调用 /index 构建索引。")

    # ── 查询嵌入 ────────────────────────────────────────────

    def _embed_query(self, q: str):
        """对查询文本做嵌入，可选 OpenAI embedding（通过 FORCE_OPENAI_EMBEDDING 控制）"""
        import numpy as np
        if self.openai_key and os.getenv("FORCE_OPENAI_EMBEDDING", ""):
            import requests
            url = "https://api.openai.com/v1/embeddings"
            headers = {"Authorization": f"Bearer {self.openai_key}"}
            body = {"input": q, "model": "text-embedding-3-small"}
            r = requests.post(url, headers=headers, json=body, timeout=15)
            r.raise_for_status()
            return np.array(r.json()["data"][0]["embedding"], dtype="float32")

        embedder = self._load_embedder()
        return embedder.encode([q], convert_to_numpy=True)[0].astype("float32")

    # ── 查询检索 ────────────────────────────────────────────

    def query(self, q: str, top_k: int = 3) -> Dict[str, Any]:
        """检索 top_k 个最相关文档片段，可选 OpenAI 合成回答"""
        import numpy as np
        self._ensure_index()
        q_emb = self._embed_query(q)

        distances, indices = self._index.search(
            np.array([q_emb], dtype="float32"), k=top_k
        )

        results = []
        for dist, idx in zip(distances[0], indices[0]):
            if idx < 0 or idx >= len(self._metas):
                continue
            meta = self._metas[idx]
            results.append({
                "score": float(dist),
                "id": meta["id"],
                "source": meta["source"],
                "text": meta["text"],
            })

        # 拼接检索到的片段作为基础回答
        concat_answer = "\n\n".join([r["text"] for r in results])

        # 若有 OpenAI key，尝试生成式合成回答；否则返回拼接片段
        if self.openai_key:
            synth = self._llm_synthesize(q, results)
            return {"query": q, "results": results, "answer": synth}

        return {"query": q, "results": results, "answer": concat_answer}

    # ── LLM 合成回答（OpenAI Chat Completions） ──────────────────────────────

    def _llm_synthesize(self, query: str, results: List[Dict]) -> str:
        """调用 OpenAI Chat API 基于检索结果生成带引用的回答

        要求模型：
        - 仅基于提供的上下文回答
        - 如无法从上下文回答则返回“信息不足”
        - 在回答中引用来源编号，例如 [来源1]
        """
        if not results:
            return "信息不足：没有检索到相关内容。"

        context = "\n\n".join([f"[来源{i+1}] {r['text']}" for i, r in enumerate(results)])

        system_prompt = (
            "你是一个基于文档回答问题的助手。"
            "请严格只使用下面提供的上下文回答问题。"
            "如果上下文不足以回答，请如实说 '信息不足'。"
            "回答时请在相关句子后使用来源编号，例如 [来源1]。"
        )

        user_message = f"上下文:\n{context}\n\n问题: {query}"

        payload = {
            "model": self.openai_chat_model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
            "temperature": 0.2,
            "max_tokens": 500,
        }

        try:
            import requests
            r = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.openai_key}",
                    "Content-Type": "application/json",
                },
                json=payload,
                timeout=30,
            )
            r.raise_for_status()
            j = r.json()
            # defensive access
            choice = j.get("choices", [{}])[0]
            msg = choice.get("message", {}).get("content") if isinstance(choice, dict) else None
            if not msg:
                return concat_answer
            return msg
        except Exception as e:
            print(f"[RAG] LLM 合成失败，回退到拼接回答: {e}")
            return concat_answer
