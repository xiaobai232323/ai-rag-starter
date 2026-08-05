# Release v0.1.0

Initial RAG Starter release — minimal Retrieval-Augmented Generation starter for demos and portfolio.

## Highlights

- FastAPI service with endpoints: /health, /metrics, /upload, /index, /query
- Local embeddings using sentence-transformers (all-MiniLM-L6-v2) + FAISS for vector retrieval
- Optional OpenAI Chat-based synthesis for answers when OPENAI_API_KEY is set (configurable model via OPENAI_CHAT_MODEL)
- Static demo UI at /static/demo.html (examples/demo.html)
- Dockerfile & docker-compose for local demo
- Lightweight CI (tests + lint) that avoids heavy deps in CI by default

## Files & changes

- app/rag.py — RAG engine: embeddings, FAISS index, retrieval, OpenAI chat synthesis with citation requirements
- app/main.py — FastAPI endpoints and static mount for demo
- examples/demo.html — simple static demo UI (upload / index / query)
- .github/workflows/ci.yml — lightweight CI workflow
- run_ops.sh, Dockerfile, docker-compose.yml — local dev & run helpers

## How to publish this release

Option A — using gh CLI (recommended):

1. Ensure gh is authenticated with workflow & repo permissions (PAT or gh auth). Then run:

   gh release create v0.1.0 --title "v0.1.0" --notes-file RELEASE_NOTES_v0.1.0.md --repo xiaobai232323/ai-rag-starter

   (To attach the ZIP artifact: `gh release create v0.1.0 ai-rag-starter-v0.1.0.zip --title "v0.1.0" --notes-file RELEASE_NOTES_v0.1.0.md`)

Option B — using GitHub web UI:

1. Go to: https://github.com/xiaobai232323/ai-rag-starter/releases
2. Click "Draft a new release"
3. Tag version: `v0.1.0` (create new tag), Release title: `v0.1.0`
4. Paste the contents of this file into the release notes textarea, upload optional assets (ZIP), and publish.

## Changelog (short)

- Initial commit: scaffold RAG starter with retrieval & optional OpenAI synthesis
- Added lightweight CI and static demo

---

If you want, I can also:
- Create the release for you if you grant me a token with repo & releases permissions (or perform via gh auth),
- Produce the ZIP artifact and attach it to the release,
- Draft a short tweet/LinkedIn blurb and a README banner for the release.
