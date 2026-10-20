# Data Process Agent

Upload guide (PDF/gambar) + data mentah (Excel/CSV) → tabel sesuai guide.
LLM lokal (Ollama) bikin rencana, pandas yang ngitung.

## Jalanin
1. `ollama pull qwen3-vl:8b`
2. backend: `cp .env.example .env && uv sync`
3. 3 terminal:
   - `cd backend && uv run uvicorn data_agent.main:app --reload --port 8000`
   - `cd backend && npx --allow-scripts=inngest-cli inngest-cli@latest dev -u http://127.0.0.1:8000/api/inngest --no-discovery`
   - `cd frontend && npm ci && npm run dev`
4. buka http://localhost:5173

## Cek kualitas
- `cd backend && uv run pytest`
- `cd backend && uv run data-agent-eval`

Detail lengkap: GUIDE.md
