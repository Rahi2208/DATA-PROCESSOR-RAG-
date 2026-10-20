# 📘 Data Process Agent: Panduan Lengkap

> Satu file berisi **konsep, prompt, dependencies, workflow, dan semua kode** sampai app jadi dan bisa di-maintain.
> Semua kode di sini udah dites: **36 test lolos** dan frontend **berhasil di-build**. Bagian yang manggil model Ollama asli dites pakai "LLM palsu", jadi perilaku model asli tetap dicek di Langkah 5 dan 12.
>
> 🔄 **Update 2026-10-18** (waktu dibangun beneran): disesuaiin sama npm 12, shadcn 4, dan inngest-cli 1.46.
> Ada perbaikan di `jobs.py` (+ `tests/test_jobs.py`) dan perintah Inngest/shadcn. Detailnya ditandai 🔄 di tiap langkah.

---

## 🧭 Cara pakai panduan ini

- Kerjain **berurutan**, satu langkah sampai bagian ✅ Cek-nya lolos, baru lanjut
- Tiap langkah isinya: 🎯 tujuan → 💡 konsep → 🧩 perintah/kode → ✅ cek
- Semua perintah ditulis buat **Arch Linux + fish**
- Kode ditulis **lengkap**. Tugas lu: ketik/copy, jalanin, dan **baca komentarnya** biar paham
- Kalau macet, lompat ke [🆘 Troubleshooting](#-troubleshooting)

### Daftar isi

- [A. Konsep](#a-konsep)
- [B. Prompt buat Claude](#b-prompt-buat-claude)
- [C. Dependencies](#c-dependencies)
- [D. Struktur folder akhir](#d-struktur-folder-akhir)
- [E. Part 1: Backend (AI Agent)](#e-part-1-backend-ai-agent)
- [F. Part 2: Frontend (React)](#f-part-2-frontend-react)
- [G. Maintenance](#g-maintenance)
- [🆘 Troubleshooting](#-troubleshooting)
- [H. Pengembangan berikutnya](#h-pengembangan-berikutnya)

---

# A. Konsep

## A1. App ini ngapain?

```
INPUT                                   OUTPUT
┌──────────────────────┐                ┌──────────────────────────┐
│ guide.pdf / foto     │                │ Tabel 1: Hasil Perhitungan│
│ "hitung T = t/10,    │   drag & drop  │ Tabel 2: Ringkasan        │
│  g = 4π²L/T², ..."   │ ─────────────→ │ (+ rumus yang dipakai)    │
│                      │   pencet Enter │ (+ cek tiap instruksi)    │
│ data.xlsx            │                │ (+ download Excel)        │
│ (data mentah)        │                └──────────────────────────┘
└──────────────────────┘
```

- **Guide**: PDF atau gambar yang isinya cara ngolah data (rumus, pembulatan, format tabel)
- **Data**: 1 file Excel/CSV berisi data mentah (misal hasil eksperimen)
- **Hasil**: tabel sebanyak yang diminta guide, dengan kolom sesuai template di guide

## A2. Ide utama: LLM yang ngerti, pandas yang ngitung

LLM itu jago **ngerti bahasa**, tapi gak bisa diandalkan buat **ngitung ribuan angka**. Jadi tugasnya dibagi:

```
guide.pdf ──→ LLM ──→ RENCANA (JSON)          ← LLM cuma nerjemahin guide
                         ↑
data.xlsx ──→ pandas ──→ nama kolom + 5 baris contoh   ← LLM gak lihat semua data

RENCANA + data.xlsx ──→ pandas ──→ tabel hasil   ← angkanya pasti bener
```

Contoh rencana yang dibikin LLM:

```json
{"tables": [{
  "id": "hasil", "title": "Hasil Perhitungan", "source": "data",
  "steps": [
    {"op": "compute", "new_column": "t_periode", "expr": "waktu_10_ayunan_s / 10"},
    {"op": "compute", "new_column": "g", "expr": "4 * pi ** 2 * panjang_tali_m / t_periode ** 2"},
    {"op": "round", "columns": ["t_periode", "g"], "decimals": 3}
  ]
}]}
```

Tiap `op` itu fungsi pandas kecil yang **kita tulis sendiri** dan ada test-nya. LLM cuma bisa milih op dari daftar, gak bisa ngejalanin kode bebas.

## A3. Alur proses: 5 step Inngest

```
1. load_inputs           baca guide (teks + gambar) & ringkasan Excel        [tanpa LLM]
2. extract_instructions  LLM bikin checklist instruksi dari guide            [LLM]
3. make_plan             LLM bikin rencana JSON, langsung diuji di data asli [LLM]
                         kalau error → pesan error dikirim balik ke LLM (maks 3x)
4. run_plan              pandas jalanin rencana                              [tanpa LLM]
5. review                LLM ngecek: tiap instruksi udah dipenuhi?           [LLM]
```

Kenapa pakai **Inngest**:
- Tiap step **dicatat**: input, output, dan error-nya kelihatan di dashboard
- Step yang gagal **dicoba ulang** tanpa ngulang step yang udah sukses
- Proses jalan di **background**, jadi user gak nunggu satu request yang lama

## A4. Kenapa React gak langsung ngobrol sama Inngest?

React jalan di **browser user**, jadi gak boleh pegang akses ke sistem internal. Semua lewat FastAPI:

```
Browser (React)
   │  POST /api/jobs (upload file)      GET /api/jobs/{id} (cek status, tiap 1,5 detik)
   ▼
FastAPI ──kirim event──→ Inngest ──jalanin──→ fungsi process_job (5 step)
   │                        │
   └──── nanya status ──────┘
```

## A5. Keputusan teknis & alasannya

| Keputusan | Alasan |
|---|---|
| Ollama, nama model di `.env` | Lokal = gratis & data gak keluar dari laptop. Pindah ke cloud cukup ganti `.env`. 🔄 Laptop sekarang cuma CPU, jadi pakai `qwen3-vl:2b-instruct` dulu, nanti pindah ke `glm-5.3-flash:cloud` |
| **Rencana JSON + pandas** | Angka pasti benar, aman (gak ngejalanin kode buatan AI), gampang dites |
| Satu model `Step` untuk semua op | Schema JSON-nya simpel, lebih gampang diikutin model lokal yang kecil |
| Nama kolom dirapihin (`Panjang Tali (m)` → `panjang_tali_m`) | Biar aman dipakai di rumus |
| Tiap step "uji coba" di data asli | Rencana yang salah ketahuan sebelum hasilnya dikasih ke user |
| Step `review` + rumus ditampilin di UI | LLM bisa salah baca rumus (misal `T²` jadi `T*2`), jadi user harus bisa ngecek |
| Qdrant **ditunda** | Guide biasanya pendek dan muat di konteks model. RAG malah berisiko bikin instruksi kelewat |
| Satu pintu per urusan (`config.py`, `llm.py`, `prompts.py`) | Mau ganti setting / model / prompt? Cukup buka 1 file |

---

# B. Prompt buat Claude

Pakai prompt ini kalau mau lanjut belajar bareng Claude (di chat atau Claude Code). Udah disesuaiin sama semua keputusan di atas.

````markdown
# Project: Data Process Agent App

## 🎯 Konsep
User drag & drop file GUIDE (PDF/gambar berisi cara olah data: rumus, pembulatan,
format tabel) + 1 file DATA mentah (.xlsx/.csv, misal hasil eksperimen), pencet Enter,
app balikin tabel sesuai guide: jumlah tabel & kolom ngikutin guide.

Folder project: DATA-PROCESSOR/ (backend/ + frontend/).
Panduan lengkap + semua kode ada di file GUIDE.md di root project. Baca dulu.

## 👤 Tentang gua
- Pemula fullstack, belajar paling enak lewat project langsung
- Arch Linux, shell fish, pakai uv buat Python
- Laptop cuma CPU (Intel, RAM 11,5 GB): model lokal ≥ 8B kehabisan RAM
- Mau paham dan bisa maintain app ini. Jangan vibe coding.

## 🧠 Arsitektur (udah diputusin)
- LLM: Ollama, nama model di .env. Sekarang LOKAL `qwen3-vl:2b-instruct`
  (LLM_NUM_CTX=8192, LLM_THINK=false), nanti pindah ke `glm-5.3-flash:cloud`.
  LLM cuma bikin RENCANA JSON, yang ngitung pandas lewat daftar op di operations.py
  (compute, filter, select, rename, sort, round, group_agg, aggregate, linear_fit).
  Rumus divalidasi pakai ast.
- Backend: uv, Python 3.12, src/data_agent/, FastAPI + Inngest (5 step:
  load_inputs → extract_instructions → make_plan → run_plan → review),
  Pydantic di custom_types.py, semua panggilan LLM lewat llm.py, prompt di prompts.py
- Frontend: Vite + React + TypeScript, Tailwind, shadcn/ui, TanStack Query (polling),
  TanStack Table v9, react-dropzone. React cuma ngobrol sama FastAPI, gak ke Inngest.
- Qdrant ditunda sampai alur dasar jalan.

## 🧭 Aturan kerja (WAJIB)
1. Satu langkah per balasan. Kodenya LU yang tulis lengkap, tapi bertahap.
2. Tiap langkah: 💡 konsep singkat → 🧩 kode lengkap + komentar → ✅ cara ngecek.
3. Berhenti dan tunggu sampai gua bilang "lanjut" atau kirim hasil/error.
   Kalau gua kirim error, review dulu sebelum lanjut.
4. Penjelasan simpel, satu ide per bagian, jangan paragraf panjang.
5. Mau ubah keputusan arsitektur di atas? Kasih alasan + alternatif, tanya gua dulu.

## 🔧 Maintenance (jaga terus)
- uv.lock & package-lock.json di-commit, .env gak di-commit
- tiap fitur baru ada test-nya (uv run pytest)
- tiap ubah prompt/model: jalanin uv run data-agent-eval
- types.ts di frontend harus sama dengan custom_types.py

## ▶️ Sekarang
[tulis lagi di langkah berapa / mau ngapain]
````

---

# C. Dependencies

## C1. Tools di komputer

| Tool | Buat apa | Install (Arch) |
|---|---|---|
| `uv` | ngatur project & package Python | `sudo pacman -S uv` |
| `nodejs` + `npm` | frontend React + Inngest dev server | `sudo pacman -S nodejs npm` |
| `ollama` | server model AI lokal | `sudo pacman -S ollama-cuda` (NVIDIA) / `ollama-rocm` (AMD) / `ollama` (CPU) |
| `git` | version control | `sudo pacman -S git` |

## C2. Backend (Python)

| Package | Buat apa |
|---|---|
| `ollama` | client Python buat manggil model |
| `python-dotenv` | baca file `.env` |
| `pydantic` | bentuk data + validasi (otomatis ikut FastAPI) |
| `pymupdf` | ambil teks PDF + render halaman scan jadi gambar |
| `pandas` | ngolah tabel / ngitung rumus |
| `numpy` | regresi linear (`linear_fit`) |
| `openpyxl` | biar pandas bisa baca & tulis `.xlsx` |
| `fastapi` | server API |
| `uvicorn` | yang ngejalanin server FastAPI |
| `python-multipart` | wajib ada biar FastAPI bisa nerima upload file |
| `inngest` | step-step proses di background + dashboard |
| `httpx` | nanya status job ke Inngest |
| `pytest` *(dev)* | testing |

## C3. Frontend (npm)

| Package | Buat apa |
|---|---|
| `react`, `vite`, `typescript` | kerangka app (dari template Vite) |
| `tailwindcss`, `@tailwindcss/vite` | styling |
| shadcn/ui (`button`, `card`, `table`, `badge`, `alert`) | komponen siap pakai, kodenya masuk ke project lu |
| `@tanstack/react-query` | kirim job + polling status |
| `@tanstack/react-table` (v9) | tabel hasil yang bisa di-sort |
| `react-dropzone` | drag & drop file |
| `lucide-react` | ikon (ikut ke-install waktu `shadcn init`) |
| `@types/node` *(dev)* | biar `vite.config.ts` kenal modul `node:path` |

---

# D. Struktur folder akhir

```
DATA-PROCESSOR/
├─ GUIDE.md                    ← file ini
├─ README.md
├─ backend/
│  ├─ .env / .env.example
│  ├─ .gitignore
│  ├─ pyproject.toml / uv.lock / .python-version
│  ├─ playground/              ← tempat nyoba-nyoba, bukan bagian app
│  │  ├─ try_ask.py
│  │  └─ try_structured.py
│  ├─ samples/
│  │  ├─ make_bandul.py        ← bikin sample bandul
│  │  └─ bandul/  guide.pdf  data.xlsx  expected.json
│  ├─ src/data_agent/
│  │  ├─ __init__.py
│  │  ├─ config.py             ← baca .env
│  │  ├─ custom_types.py       ← bentuk data (Pydantic)
│  │  ├─ llm.py                ← satu-satunya yang manggil model
│  │  ├─ doc_loader.py         ← baca guide & Excel
│  │  ├─ operations.py         ← daftar op pandas + validasi rumus
│  │  ├─ executor.py           ← jalanin rencana
│  │  ├─ prompts.py            ← semua prompt
│  │  ├─ pipeline.py           ← 5 tahap proses (fungsi biasa)
│  │  ├─ cli.py                ← jalanin dari terminal
│  │  ├─ evaluate.py           ← cek semua sample
│  │  ├─ jobs.py               ← status job + export Excel
│  │  └─ main.py               ← FastAPI + Inngest
│  └─ tests/
│     ├─ conftest.py
│     ├─ test_doc_loader.py  test_operations.py  test_executor.py
│     ├─ test_pipeline.py  test_api.py  test_jobs.py  test_inngest_function.py
└─ frontend/
   ├─ .env / .env.example
   ├─ components.json          ← dibikin shadcn
   ├─ vite.config.ts / tsconfig*.json / package.json / package-lock.json
   └─ src/
      ├─ main.tsx / App.tsx / index.css
      ├─ api/       types.ts  client.ts  files.ts
      ├─ hooks/     useJob.ts
      ├─ lib/       utils.ts   ← dibikin shadcn
      └─ components/
         ├─ FileDropzone.tsx  ResultTable.tsx  ReviewList.tsx
         └─ ui/     ← dibikin shadcn (button, card, table, badge, alert)
```

---
# E. Part 1: Backend (AI Agent)

## Langkah 0: Setup tools

🎯 **Tujuan:** semua tools ke-install, model ke-download, server Ollama nyala.

💡 **Konsep:** Ollama jalan sebagai **server di background**. Terminal & kode Python cuma "ngobrol" sama server itu:

```
kode Python → Ollama server (localhost:11434) → model qwen3-vl di GPU/CPU lu
```

🧩 **Perintah:**

```fish
# 1. cek GPU: buat milih ukuran model
lspci | grep -iE 'vga|3d'
nvidia-smi          # kalau NVIDIA: lihat kolom Memory (VRAM)
free -h             # kalau cuma CPU: lihat RAM yang "available"

# 2. install tools (pilih SATU package ollama sesuai GPU)
sudo pacman -S uv nodejs npm git
sudo pacman -S ollama-cuda      # NVIDIA
# sudo pacman -S ollama-rocm    # AMD
# sudo pacman -S ollama         # CPU aja

# 3. nyalain server ollama (otomatis nyala tiap boot)
sudo systemctl enable --now ollama

# 4. download model + tes (ganti nama model sesuai tabel di bawah)
ollama pull qwen3-vl:8b
ollama run qwen3-vl:8b "halo, jawab dalam satu kalimat"
```

Pilih ukuran model:

| VRAM | Model |
|---|---|
| ≥ 8 GB | `qwen3-vl:8b` ⭐ |
| 4–6 GB | `qwen3-vl:4b` |
| < 4 GB / CPU | `qwen3-vl:2b-instruct` (lambat) |

> 🔄 **Kalau cuma CPU:** pakai versi `-instruct` (bukan `-thinking`): model "mikir" nulis ratusan token dulu sebelum jawab, dan di CPU tiap token mahal.
> Tambahin juga `LLM_NUM_CTX=8192` dan `LLM_THINK=false` di `.env` (Langkah 1).
> Contoh nyata: laptop Intel tanpa GPU, RAM 11,5 GB → `qwen3-vl:8b` dengan konteks 16384 **dibunuh kernel (OOM)**, model 1B cuma ~2,7 token/detik.

✅ **Cek:**

```fish
uv --version; node --version; npm --version; ollama --version
curl http://localhost:11434      # → Ollama is running
ollama list                      # → ada model yang lu pull
ollama ps                        # (waktu model kebuka) kolom PROCESSOR: 100% GPU = mantap
```

---

## Langkah 1: Init project backend

🎯 **Tujuan:** kerangka project Python pakai `uv`.

💡 **Konsep:** isi project uv:

```
pyproject.toml   → daftar dependency yang lu minta
uv.lock          → versi PASTI semua package (dikunci, di-commit)
.venv/           → tempat package di-install (gak di-commit)
src/data_agent/  → kode lu
```

`uv run ...` otomatis pakai `.venv`, jadi **gak perlu activate**.

🧩 **Perintah:**

```fish
cd ~/Projects/"AI APPS"          # sesuaiin sama lokasi lu
mkdir -p DATA-PROCESSOR/backend
cd DATA-PROCESSOR/backend

uv init --package --name data-agent --python 3.12 --vcs none
uv add ollama python-dotenv pymupdf pandas numpy openpyxl fastapi uvicorn python-multipart inngest httpx
uv add --dev pytest
```

| Flag | Artinya |
|---|---|
| `--package` | layout `src/`, sama kayak RAG-PDF |
| `--name data-agent` | folder kodenya jadi `src/data_agent/` |
| `--python 3.12` | kalau belum ada, uv download sendiri |
| `--vcs none` | jangan bikin git di sini (git-nya satu aja di `DATA-PROCESSOR/`) |

> ⚠️ Karena `--vcs none`, uv **gak** bikin `.gitignore`. Kita bikin manual di bawah.

Bikin `backend/.gitignore`:

```gitignore
# file sampah python
__pycache__/
*.py[oc]
.pytest_cache/

# tempat package di-install, bisa dibikin ulang pakai `uv sync`
.venv/

# rahasia & setting lokal
.env

# file yang di-upload user (bisa berisi data pribadi)
uploads/
```

Bikin `backend/.env` (setting asli, **gak** di-commit). Nama model sesuaiin sama pilihan di Langkah 0:

```fish
printf 'OLLAMA_HOST=http://localhost:11434\nLLM_MODEL=qwen3-vl:8b\n' > .env
```

> Fish gak punya `<<EOF` kayak bash, jadi `printf` dipakai buat nulis beberapa baris (`\n` = ganti baris).

🔄 Versi buat laptop yang cuma CPU (yang dipakai sekarang):

```fish
printf 'OLLAMA_HOST=http://localhost:11434\nLLM_MODEL=qwen3-vl:2b-instruct\nLLM_NUM_CTX=8192\nLLM_THINK=false\n' > .env
```

Bikin `backend/.env.example` (contoh lengkap semua setting, **di-commit**):

```bash
# --- LLM ---
OLLAMA_HOST=http://localhost:11434
LLM_MODEL=qwen3-vl:8b
# panjang konteks; turunin (misal 8192) kalau GPU kehabisan memori
LLM_NUM_CTX=16384
# isi "false" kalau model kelamaan "mikir"
LLM_THINK=

# --- dokumen ---
MAX_GUIDE_PAGES=20
MAX_UPLOAD_MB=20
UPLOAD_DIR=uploads

# --- server ---
INNGEST_API_BASE=http://127.0.0.1:8288/v1
FRONTEND_ORIGIN=http://localhost:5173
```

Edit `pyproject.toml`, jadiin persis kayak gini. Yang berubah: `description`, bagian `[project.scripts]` (2 perintah), dan `[tool.pytest.ini_options]`. Angka versi (di `dependencies` dan `build-system`) boleh beda, ikutin punya lu:

```toml
[project]
name = "data-agent"
version = "0.1.0"
description = "Agent yang ngubah data mentah jadi tabel sesuai guide"
readme = "README.md"
requires-python = ">=3.12"
dependencies = [
    "fastapi>=0.143.3",
    "httpx>=0.28.1",
    "inngest>=0.5.19",
    "numpy>=2.5.4",
    "ollama>=0.6.3",
    "openpyxl>=3.1.5",
    "pandas>=3.0.6",
    "pymupdf>=1.28.2",
    "python-dotenv>=1.2.4",
    "python-multipart>=0.0.32",
    "uvicorn>=0.54.0",
]

[project.scripts]
data-agent = "data_agent.cli:main"
data-agent-eval = "data_agent.evaluate:main"

[build-system]
requires = ["uv_build>=0.12.23,<0.13.0"]
build-backend = "uv_build"

[dependency-groups]
dev = [
    "pytest>=9.1.1",
]

[tool.pytest.ini_options]
testpaths = ["tests"]
```

Ganti isi `src/data_agent/__init__.py` jadi satu baris komentar aja:

```python
# data_agent: agent yang ngubah data mentah jadi tabel sesuai guide
```

> Kenapa dikosongin? `uv init` naruh fungsi `main()` di sini. Fungsi itu kita pindah ke `cli.py` (Langkah 12), biar namanya gak bentrok sama file `main.py` (server).

✅ **Cek:**

```fish
ls -a                 # ada .env .env.example .gitignore pyproject.toml uv.lock .venv src
uv run python -c "import ollama, pandas, fastapi, inngest, pymupdf; print('semua package oke')"
```

---

## Langkah 2: `config.py`: satu pintu buat `.env`

🎯 **Tujuan:** semua setting dibaca di satu tempat.

💡 **Konsep:**

```python
os.getenv('OLLAMA_HOST', 'http://localhost:11434')  # gak ada? pakai default
os.environ['LLM_MODEL']                              # gak ada? langsung CRASH
```

Crash itu **bagus** buat setting wajib: mending error jelas di awal daripada app diam-diam pakai model yang salah.

🧩 Bikin `src/data_agent/config.py`:

```python
# config.py: satu-satunya file yang baca .env
# file lain cukup: from data_agent import config
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()  # cari file .env, masukin isinya ke environment variable


def _optional_bool(name: str) -> bool | None:
    # "true"/"false" -> True/False, kosong -> None (biarin ollama pakai default model)
    value = os.getenv(name, '').strip().lower()
    if value in ('true', '1', 'yes'):
        return True
    if value in ('false', '0', 'no'):
        return False
    return None


# --- LLM ---
OLLAMA_HOST = os.getenv('OLLAMA_HOST', 'http://localhost:11434')
LLM_MODEL = os.environ['LLM_MODEL']  # wajib: kalau gak ada, crash dari awal
LLM_NUM_CTX = int(os.getenv('LLM_NUM_CTX', '16384'))  # panjang konteks (token)
LLM_THINK = _optional_bool('LLM_THINK')  # matiin "mode mikir" kalau kelamaan: LLM_THINK=false

# --- dokumen ---
MAX_GUIDE_PAGES = int(os.getenv('MAX_GUIDE_PAGES', '20'))
MAX_UPLOAD_MB = int(os.getenv('MAX_UPLOAD_MB', '20'))
UPLOAD_DIR = Path(os.getenv('UPLOAD_DIR', 'uploads')).resolve()

# --- server ---
INNGEST_API_BASE = os.getenv('INNGEST_API_BASE', 'http://127.0.0.1:8288/v1')
FRONTEND_ORIGIN = os.getenv('FRONTEND_ORIGIN', 'http://localhost:5173')
```

✅ **Cek:**

```fish
uv run python -c "from data_agent import config; print(config.LLM_MODEL, config.UPLOAD_DIR)"
```

Harus muncul nama model lu + `/.../backend/uploads`. Coba hapus baris `LLM_MODEL` dari `.env` → harus `KeyError: 'LLM_MODEL'`. Habis itu balikin lagi.

---

## Langkah 3: `llm.py`: satu-satunya pintu ke model

🎯 **Tujuan:** bisa manggil model dari Python, sambil nyatat token & kecepatan.

💡 **Konsep 1:** semua file lain manggil model **lewat `llm.py`**. Mau ganti model / provider / nambah retry? Cukup ubah file ini.

💡 **Konsep 2:** respons Ollama isinya lebih dari jawaban:

```python
res.message.content     # teks jawaban
res.prompt_eval_count   # token INPUT
res.eval_count          # token OUTPUT
res.total_duration      # waktu dalam NANOdetik (÷ 1e9 = detik)
```

💡 **Konsep 3:** `logging` > `print`: tiap baris otomatis ada waktu, level, dan nama file asalnya.

💡 **Konsep 4:** `structured()` maksa model jawab sesuai **schema Pydantic** (`format=`), terus hasilnya divalidasi. Kalau JSON-nya salah, kesalahannya dikasih tau ke model dan diminta ulang.

🧩 Bikin `src/data_agent/llm.py`:

```python
# llm.py: satu-satunya file yang ngobrol sama model
# mau ganti model/provider? cukup ubah file ini
import logging
from typing import TypeVar

from ollama import Client
from pydantic import BaseModel, ValidationError

from data_agent import config

logger = logging.getLogger(__name__)
client = Client(host=config.OLLAMA_HOST)  # sambungan ke server ollama

T = TypeVar('T', bound=BaseModel)
MAX_FORMAT_RETRIES = 2  # kalau JSON dari model gak sesuai schema, coba ulang segini kali


def _chat(messages: list[dict], schema: dict | None, label: str) -> str:
    res = client.chat(
        model=config.LLM_MODEL,
        messages=messages,
        format=schema,                    # paksa jawaban sesuai JSON schema
        think=config.LLM_THINK,           # None = default model
        options={
            'temperature': 0,             # 0 = jawaban paling konsisten
            'num_ctx': config.LLM_NUM_CTX,
        },
    )
    # ollama ngitung waktu dalam NANOdetik -> dibagi 1e9 jadi detik
    seconds = (res.total_duration or 0) / 1e9
    tps = (res.eval_count or 0) / ((res.eval_duration or 1) / 1e9)
    logger.info(
        '[%s] model=%s input=%s output=%s waktu=%.1fs speed=%.1f tok/s',
        label, config.LLM_MODEL, res.prompt_eval_count, res.eval_count, seconds, tps,
    )
    return res.message.content


def ask(prompt: str) -> str:
    # jawaban teks biasa
    return _chat([{'role': 'user', 'content': prompt}], schema=None, label='ask')


def structured(prompt: str, schema: type[T], images: list[str] | None = None,
               label: str = 'llm') -> T:
    # jawaban berbentuk Pydantic model (schema)
    message: dict = {'role': 'user', 'content': prompt}
    if images:
        message['images'] = images  # path gambar, ollama yang baca filenya
    messages = [message]

    for attempt in range(1, MAX_FORMAT_RETRIES + 2):
        content = _chat(messages, schema.model_json_schema(), f'{label}#{attempt}')
        try:
            return schema.model_validate_json(content)
        except ValidationError as e:
            logger.warning('[%s] output gak sesuai schema (percobaan %s): %s', label, attempt, e)
            # kasih tau model kesalahannya, terus minta ulang
            messages = [
                message,
                {'role': 'assistant', 'content': content},
                {'role': 'user', 'content': f'Your JSON was invalid:\n{e}\nReturn corrected JSON only.'},
            ]
    raise ValueError(f'[{label}] model gagal ngasih JSON yang valid')
```

Bikin folder buat nyoba-nyoba (`mkdir playground`), terus bikin `playground/try_ask.py`:

```python
# try_ask.py: tes pertama ngobrol sama model (bukan bagian app, cuma buat nyoba)
# jalanin: uv run python playground/try_ask.py
import logging

from data_agent import config, llm

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(name)s: %(message)s')
logging.getLogger('httpx').setLevel(logging.WARNING)

print('host :', config.OLLAMA_HOST)
print('model:', config.LLM_MODEL)
print(llm.ask('Sebutkan rumus periode bandul sederhana dalam satu baris'))
```

✅ **Cek:**

```fish
uv run python playground/try_ask.py
uv run python playground/try_ask.py     # jalanin 2x
```

Hasil yang diharapkan, kurang lebih:

```
host : http://localhost:11434
model: qwen3-vl:8b
2026-10-18 05:00:12 INFO data_agent.llm: [ask] model=qwen3-vl:8b input=24 output=31 waktu=2.3s speed=35.2 tok/s
T = 2π √(L/g)
```

| `speed` | Artinya |
|---|---|
| ≥ 20 tok/s | jalan di GPU 👍 |
| 5–20 | sebagian tumpah ke CPU |
| < 5 | full CPU → pertimbangin model yang lebih kecil, atau Ollama cloud |

Run pertama lebih lama karena model harus dimuat ke GPU/RAM dulu.

---

## Langkah 4: `custom_types.py`: bentuk data antar step

🎯 **Tujuan:** semua data yang lewat antar step punya bentuk yang jelas.

💡 **Konsep:** Pydantic = "satpam" data. Kalau LLM ngasih JSON yang bentuknya salah, langsung ketahuan di sini, bukan nanti di tengah perhitungan.

Urutan model-nya ngikutin alur proses:

```
InputBundle → Instructions → Plan (TablePlan → Step) → ResultTable → Review → JobResult
```

💡 Kenapa `Step` cuma **satu model** dengan banyak field opsional (bukan satu model per op)? Schema JSON-nya jadi simpel, lebih gampang diikutin model lokal yang kecil. Parameter wajib per op dicek di `operations.py`.

🧩 Bikin `src/data_agent/custom_types.py`:

```python
# custom_types.py: "bentuk" data yang lewat antar step
# Pydantic ngecek bentuknya otomatis, jadi data yang salah langsung ketahuan
from typing import Any, Literal

from pydantic import BaseModel


# ---------- 1. input yang udah dibaca ----------
class SheetSummary(BaseModel):
    name: str                      # nama sheet di Excel
    columns: list[str]             # nama kolom (udah dirapihin, lihat doc_loader)
    dtypes: dict[str, str]         # tipe data tiap kolom
    n_rows: int
    sample_rows: list[dict[str, Any]]  # beberapa baris contoh buat LLM


class InputBundle(BaseModel):
    guide_text: str                # teks dari guide (PDF)
    guide_images: list[str]        # path gambar (foto guide / halaman PDF scan)
    data_path: str                 # path file Excel/CSV
    sheets: list[SheetSummary]


# ---------- 2. hasil LLM: daftar instruksi ----------
class Instructions(BaseModel):
    items: list[str]               # tiap instruksi di guide, satu per item
    expected_tables: list[str]     # tabel apa aja yang diminta guide


# ---------- 3. hasil LLM: rencana proses ----------
OpName = Literal[
    'compute', 'filter', 'select', 'rename', 'sort',
    'round', 'group_agg', 'aggregate', 'linear_fit',
]
AggFunc = Literal['mean', 'sum', 'min', 'max', 'count', 'std', 'median']


class Aggregation(BaseModel):
    column: str                    # kolom yang dihitung
    func: AggFunc                  # fungsi: mean, sum, ...
    output: str                    # nama kolom hasilnya


class RenamePair(BaseModel):
    old: str
    new: str


class Step(BaseModel):
    # satu model buat semua op (bukan satu model per op),
    # biar schema-nya simpel dan gampang diikutin model lokal yang kecil.
    # parameter yang wajib per op dicek di operations.py
    op: OpName
    new_column: str | None = None          # compute
    expr: str | None = None                # compute (rumus) / filter (kondisi)
    columns: list[str] | None = None       # select / round
    renames: list[RenamePair] | None = None  # rename
    by: list[str] | None = None            # sort / group_agg
    descending: bool | None = None         # sort
    decimals: int | None = None            # round
    aggregations: list[Aggregation] | None = None  # group_agg / aggregate
    x: str | None = None                   # linear_fit
    y: str | None = None                   # linear_fit


class TablePlan(BaseModel):
    id: str                        # id unik, contoh: "hasil_g"
    title: str                     # judul yang ditampilin
    source: str                    # nama sheet ATAU id tabel sebelumnya
    steps: list[Step]


class Plan(BaseModel):
    tables: list[TablePlan]


# ---------- 4. hasil akhir ----------
class ResultTable(BaseModel):
    id: str
    title: str
    columns: list[str]
    rows: list[list[Any]]
    formulas: list[str]            # langkah/rumus yang dipakai, buat ditampilin di UI


class TableSet(BaseModel):
    tables: list[ResultTable]


class CheckItem(BaseModel):
    instruction: str
    done: bool
    note: str


class Review(BaseModel):
    items: list[CheckItem]


class JobResult(BaseModel):
    instructions: Instructions
    plan: Plan
    tables: list[ResultTable]
    review: Review
```

✅ **Cek:**

```fish
uv run python -c "from data_agent.custom_types import Plan; import json; print(json.dumps(Plan.model_json_schema())[:300])"
```

Muncul potongan JSON schema = ini yang nanti dikirim ke model lewat `format=`.

---

## Langkah 5: Tes structured output (penting!)

🎯 **Tujuan:** mastiin model lokal lu **nurut schema JSON**. Ini fondasi seluruh app.

🧩 Bikin `playground/try_structured.py`:

```python
# try_structured.py: tes model jawab dalam bentuk JSON sesuai schema Pydantic
# jalanin: uv run python playground/try_structured.py
import logging

from pydantic import BaseModel

from data_agent import llm

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(name)s: %(message)s')
logging.getLogger('httpx').setLevel(logging.WARNING)


class Rumus(BaseModel):
    nama: str
    rumus: str
    variabel: list[str]


hasil = llm.structured('Jelaskan rumus periode bandul sederhana.', Rumus, label='coba')
print(type(hasil))    # <class '__main__.Rumus'>  -> udah jadi objek Python, bukan teks
print(hasil.rumus)
print(hasil.variabel)
```

✅ **Cek:**

```fish
uv run python playground/try_structured.py
```

Yang diharapkan: `<class '__main__.Rumus'>` + rumus + daftar variabel.

Kalau gagal:
- muncul warning "output gak sesuai schema" berkali-kali → model terlalu kecil, coba model yang lebih gede atau Ollama cloud
- lama banget → isi `LLM_THINK=false` di `.env` (matiin mode mikir)
- `out of memory` / Ollama mati sendiri → turunin `LLM_NUM_CTX=8192` di `.env`, atau pakai model yang lebih kecil

---

## Langkah 6: `doc_loader.py` + sample pertama

🎯 **Tujuan:** baca guide (PDF/gambar) & data (Excel/CSV), plus bikin sample buat tes.

💡 **Konsep 1:** halaman PDF yang teksnya dikit (hasil scan) atau ada gambarnya (misal rumus berupa gambar) **dirender jadi PNG**, biar bisa "dilihat" model vision.

💡 **Konsep 2:** nama kolom dirapihin:

```
"Panjang Tali (m)"    → "panjang_tali_m"
"Waktu 10 Ayunan (s)" → "waktu_10_ayunan_s"
"10 cm"               → "c_10_cm"   (gak boleh diawali angka)
```

💡 **Konsep 3:** LLM cuma dikasih **5 baris contoh** + nama & tipe kolom, bukan semua data.

🧩 Bikin `src/data_agent/doc_loader.py`:

```python
# doc_loader.py: baca file input
#   guide (PDF/gambar) -> teks + gambar buat LLM
#   data (Excel/CSV)   -> DataFrame pandas + ringkasan kolom buat LLM
import json
import logging
import re
import shutil
from pathlib import Path
from typing import Literal

import pandas as pd
import pymupdf

from data_agent import config
from data_agent.custom_types import InputBundle, SheetSummary

logger = logging.getLogger(__name__)

GUIDE_EXTENSIONS = {'.pdf', '.png', '.jpg', '.jpeg', '.webp'}
DATA_EXTENSIONS = {'.xlsx', '.csv'}
SAMPLE_ROWS = 5          # baris contoh yang dikasih ke LLM (bukan semua data!)
MIN_TEXT_CHARS = 50      # halaman dengan teks lebih sedikit dari ini dianggap hasil scan
RENDER_DPI = 110         # resolusi render halaman PDF jadi gambar


def classify(filename: str) -> Literal['guide', 'data'] | None:
    # tebak jenis file dari ekstensinya
    ext = Path(filename).suffix.lower()
    if ext in GUIDE_EXTENSIONS:
        return 'guide'
    if ext in DATA_EXTENSIONS:
        return 'data'
    return None


def normalize_column(name: object) -> str:
    # "Panjang Tali (m)" -> "panjang_tali_m"
    # biar nama kolom aman dipakai di rumus (gak ada spasi / simbol)
    text = str(name).strip().lower()
    text = re.sub(r'[^0-9a-z]+', '_', text).strip('_')
    if not text:
        text = 'kolom'
    if text[0].isdigit():
        text = f'c_{text}'
    return text


def _normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    seen: dict[str, int] = {}
    new_names = []
    for col in df.columns:
        name = normalize_column(col)
        if name in seen:  # nama kembar -> kasih nomor: nilai, nilai_2
            seen[name] += 1
            name = f'{name}_{seen[name]}'
        else:
            seen[name] = 1
        new_names.append(name)
    df = df.copy()
    df.columns = new_names
    return df


def read_data(path: str) -> dict[str, pd.DataFrame]:
    # balikin {nama_sheet: DataFrame}; CSV dianggap satu sheet bernama "data"
    p = Path(path)
    if p.suffix.lower() == '.csv':
        sheets = {'data': pd.read_csv(p)}
    else:
        sheets = pd.read_excel(p, sheet_name=None)  # None = baca semua sheet
    return {
        normalize_column(name): _normalize_columns(df.dropna(how='all'))
        for name, df in sheets.items()
    }


def summarize_sheets(sheets: dict[str, pd.DataFrame]) -> list[SheetSummary]:
    summaries = []
    for name, df in sheets.items():
        # to_json -> json.loads: cara gampang ubah tipe numpy/NaN jadi tipe JSON biasa
        sample = json.loads(df.head(SAMPLE_ROWS).to_json(orient='records'))
        summaries.append(SheetSummary(
            name=name,
            columns=list(df.columns),
            dtypes={col: str(dtype) for col, dtype in df.dtypes.items()},
            n_rows=len(df),
            sample_rows=sample,
        ))
    return summaries


def load_guide(path: str, out_dir: Path) -> tuple[str, list[str]]:
    # PDF -> ambil teksnya; halaman scan / bergambar ikut dirender jadi PNG
    # gambar (foto) -> langsung dipakai
    p = Path(path)
    if p.suffix.lower() != '.pdf':
        return '', [str(p)]

    texts: list[str] = []
    images: list[str] = []
    with pymupdf.open(p) as doc:
        for i, page in enumerate(doc):
            if i >= config.MAX_GUIDE_PAGES:
                logger.warning('guide %s dipotong di %s halaman', p.name, config.MAX_GUIDE_PAGES)
                break
            text = page.get_text().strip()
            if text:
                texts.append(f'--- {p.name} halaman {i + 1} ---\n{text}')
            if len(text) < MIN_TEXT_CHARS or page.get_images():
                img_path = out_dir / f'{p.stem}_page{i + 1}.png'
                page.get_pixmap(dpi=RENDER_DPI).save(img_path)
                images.append(str(img_path))
    return '\n\n'.join(texts), images


def load_inputs(guide_paths: list[str], data_path: str, work_dir: str) -> InputBundle:
    out_dir = Path(work_dir) / 'rendered'
    shutil.rmtree(out_dir, ignore_errors=True)  # bersihin sisa run sebelumnya (kalau di-retry)
    out_dir.mkdir(parents=True)

    all_text: list[str] = []
    all_images: list[str] = []
    for gp in guide_paths:
        text, images = load_guide(gp, out_dir)
        if text:
            all_text.append(text)
        all_images.extend(images)

    sheets = read_data(data_path)
    logger.info('input: %s guide, %s gambar, sheet=%s',
                len(guide_paths), len(all_images), list(sheets))
    return InputBundle(
        guide_text='\n\n'.join(all_text),
        guide_images=all_images,
        data_path=data_path,
        sheets=summarize_sheets(sheets),
    )
```

🧩 Bikin folder `samples/` dan `tests/` dulu:

```fish
mkdir -p samples tests
```

🧩 Bikin `samples/make_bandul.py`. Script ini bikin guide PDF, data Excel, dan **jawaban yang benar** (dihitung manual, bukan pakai app):

```python
# make_bandul.py: bikin sample pertama (praktikum bandul) buat tes & evaluasi
# jalanin dari folder backend: uv run python samples/make_bandul.py
import json
import math
from pathlib import Path

import pandas as pd
import pymupdf

OUT = Path(__file__).parent / 'bandul'
OUT.mkdir(exist_ok=True)

# ---------- 1. data mentah (Excel) ----------
data = pd.DataFrame({
    'Percobaan': [1, 2, 3, 4, 5],
    'Panjang Tali (m)': [0.3, 0.5, 0.7, 0.9, 1.1],
    'Waktu 10 Ayunan (s)': [11.02, 14.15, 16.83, 19.01, 21.10],
})
data.to_excel(OUT / 'data.xlsx', sheet_name='Data', index=False)

# ---------- 2. guide (PDF) ----------
GUIDE = """PANDUAN PENGOLAHAN DATA - PRAKTIKUM BANDUL SEDERHANA

Data mentah ada di file Excel (sheet Data).

Langkah pengolahan:
1. Hitung periode satu ayunan: T = t / 10, dengan t = waktu 10 ayunan.
2. Hitung percepatan gravitasi: g = 4 x pi^2 x L / T^2, dengan L = panjang tali.
3. Bulatkan T dan g ke 3 angka di belakang koma.

Tabel 1 - Hasil Perhitungan, dengan kolom berurutan:
| Percobaan | L (m) | T (s) | g (m/s2) |

Tabel 2 - Ringkasan, berisi:
- g rata-rata (dibulatkan 3 desimal)
- persen error terhadap g literatur 9.8 m/s2:
  error = |g rata-rata - 9.8| / 9.8 x 100 (dibulatkan 2 desimal)
"""
doc = pymupdf.open()
page = doc.new_page()
page.insert_textbox(pymupdf.Rect(50, 50, 550, 800), GUIDE, fontsize=11)
doc.save(OUT / 'guide.pdf')

# ---------- 3. jawaban yang benar (dihitung manual, BUKAN pakai app) ----------
rows = []
for p, L, t in data.itertuples(index=False):
    T = round(t / 10, 3)
    g = round(4 * math.pi ** 2 * L / (t / 10) ** 2, 3)
    rows.append([p, L, T, g])
g_mean = round(sum(r[3] for r in rows) / len(rows), 3)
error = round(abs(g_mean - 9.8) / 9.8 * 100, 2)

expected = {'tables': [
    {'title': 'Hasil Perhitungan', 'columns': ['Percobaan', 'L (m)', 'T (s)', 'g (m/s2)'], 'rows': rows},
    {'title': 'Ringkasan', 'columns': ['g rata-rata', 'error (%)'], 'rows': [[g_mean, error]]},
]}
(OUT / 'expected.json').write_text(json.dumps(expected, indent=2))
print('sample dibuat di', OUT)
```

```fish
uv run python samples/make_bandul.py
```

🧩 Bikin `tests/conftest.py`. File ini disiapin pytest sebelum semua test jalan, dan berisi **rencana yang benar** buat sample bandul:

```python
# conftest.py: disiapin pytest sebelum semua test jalan
import os
import subprocess
import sys
from pathlib import Path

import pytest

# test gak butuh .env asli; config.py cuma butuh LLM_MODEL ada isinya
os.environ.setdefault('LLM_MODEL', 'test-model')

from data_agent.custom_types import Aggregation, Plan, RenamePair, Step, TablePlan  # noqa: E402

BACKEND = Path(__file__).parent.parent
SAMPLE = BACKEND / 'samples' / 'bandul'


@pytest.fixture(scope='session')
def bandul_dir() -> Path:
    # bikin file sample kalau belum ada
    if not (SAMPLE / 'expected.json').exists():
        subprocess.run([sys.executable, str(SAMPLE.parent / 'make_bandul.py')], check=True)
    return SAMPLE


@pytest.fixture
def bandul_plan() -> Plan:
    # rencana yang BENAR untuk sample bandul (contoh jawaban ideal dari LLM)
    return Plan(tables=[
        TablePlan(id='hasil', title='Hasil Perhitungan', source='data', steps=[
            Step(op='compute', new_column='t_periode', expr='waktu_10_ayunan_s / 10'),
            Step(op='compute', new_column='g', expr='4 * pi ** 2 * panjang_tali_m / t_periode ** 2'),
            Step(op='round', columns=['t_periode', 'g'], decimals=3),
            Step(op='rename', renames=[
                RenamePair(old='percobaan', new='Percobaan'),
                RenamePair(old='panjang_tali_m', new='L (m)'),
                RenamePair(old='t_periode', new='T (s)'),
                RenamePair(old='g', new='g (m/s2)'),
            ]),
            Step(op='select', columns=['Percobaan', 'L (m)', 'T (s)', 'g (m/s2)']),
        ]),
        TablePlan(id='ringkasan', title='Ringkasan', source='hasil', steps=[
            Step(op='aggregate', aggregations=[
                Aggregation(column='g (m/s2)', func='mean', output='g_rata_rata'),
            ]),
            Step(op='round', columns=['g_rata_rata'], decimals=3),
            Step(op='compute', new_column='error', expr='abs(g_rata_rata - 9.8) / 9.8 * 100'),
            Step(op='round', columns=['error'], decimals=2),
            Step(op='rename', renames=[
                RenamePair(old='g_rata_rata', new='g rata-rata'),
                RenamePair(old='error', new='error (%)'),
            ]),
        ]),
    ])
```

🧩 Bikin `tests/test_doc_loader.py`:

```python
import pandas as pd
import pymupdf
import pytest

from data_agent.doc_loader import classify, load_inputs, normalize_column, read_data


@pytest.mark.parametrize('raw, clean', [
    ('Panjang Tali (m)', 'panjang_tali_m'),
    ('  Waktu 10 Ayunan (s) ', 'waktu_10_ayunan_s'),
    ('10 cm', 'c_10_cm'),
    ('%%%', 'kolom'),
])
def test_normalize_column(raw, clean):
    assert normalize_column(raw) == clean


def test_classify():
    assert classify('panduan.PDF') == 'guide'
    assert classify('foto.jpg') == 'guide'
    assert classify('data.xlsx') == 'data'
    assert classify('virus.exe') is None


def test_read_data_nama_kolom_kembar(tmp_path):
    path = tmp_path / 'd.csv'
    pd.DataFrame([[1, 2]], columns=['Nilai', 'nilai ']).to_csv(path, index=False)
    sheets = read_data(str(path))
    assert list(sheets['data'].columns) == ['nilai', 'nilai_2']


def test_load_inputs_pdf_scan_dirender(tmp_path):
    # halaman 1 ada teks, halaman 2 kosong (kayak hasil scan) -> halaman 2 jadi gambar
    pdf = tmp_path / 'guide.pdf'
    doc = pymupdf.open()
    doc.new_page().insert_text((50, 72), 'Hitung rata-rata kolom nilai. ' * 5)
    doc.new_page()
    doc.save(pdf)
    data = tmp_path / 'data.csv'
    pd.DataFrame({'Nilai': [1, 2, 3]}).to_csv(data, index=False)

    bundle = load_inputs([str(pdf)], str(data), str(tmp_path / 'job'))

    assert 'rata-rata' in bundle.guide_text
    assert len(bundle.guide_images) == 1 and bundle.guide_images[0].endswith('page2.png')
    assert bundle.sheets[0].columns == ['nilai'] and bundle.sheets[0].n_rows == 3
```

✅ **Cek:**

```fish
uv run pytest tests/test_doc_loader.py -v
```

Semua `PASSED`. Lihat juga folder `samples/bandul/`: buka `guide.pdf` dan `data.xlsx`.

---

## Langkah 7: `operations.py`: daftar op + validasi rumus

🎯 **Tujuan:** fungsi-fungsi pandas yang boleh dipakai rencana, plus satpam rumus.

💡 **Konsep 1: validasi rumus pakai `ast`.** Rumus dipecah jadi "pohon", terus tiap potongannya dicek:

```
"4 * pi ** 2 * panjang_tali_m"   ✅ angka, konstanta, kolom
"__import__('os').system('ls')"  ❌ fungsi gak diizinkan
"a.__class__"                    ❌ akses atribut
"T ^ 2"                          ❌ ^ di Python bukan pangkat → pesan: pakai **
```

💡 **Konsep 2: `PlanError`.** Semua kesalahan rencana jadi `PlanError` dengan pesan yang jelas. Pesan ini nanti **dikirim balik ke LLM** biar dia bisa benerin rencananya sendiri.

💡 **Konsep 3: registry `OPERATIONS`.** Kamus `nama op → fungsi`. Nambah op baru = bikin fungsi + daftarin di kamus (lihat [G4](#g4-cara-nambah-op-baru)).

🧩 Bikin `src/data_agent/operations.py`:

```python
# operations.py: "kamus" operasi pandas yang boleh dipakai rencana
# LLM cuma milih op + parameter; yang ngitung tetap kode kita (hasilnya pasti)
import ast
import math

import numpy as np
import pandas as pd

from data_agent.custom_types import Step


class PlanError(Exception):
    # error karena rencana salah (kolom gak ada, rumus aneh, dll)
    # pesannya dikirim balik ke LLM biar dia bisa benerin
    pass


CONSTANTS = {'pi': math.pi, 'e': math.e}
ALLOWED_FUNCS = {'sqrt', 'abs', 'log', 'log10', 'exp', 'sin', 'cos', 'tan'}

# jenis "potongan" rumus yang diizinkan. Selain ini (akses atribut, import, lambda, dll) ditolak
_ALLOWED_NODES = (
    ast.Expression, ast.BinOp, ast.UnaryOp, ast.BoolOp, ast.Compare,
    ast.Name, ast.Load, ast.Constant, ast.Call,
    ast.Add, ast.Sub, ast.Mult, ast.Div, ast.Pow, ast.Mod, ast.FloorDiv,
    ast.USub, ast.UAdd, ast.Not, ast.And, ast.Or, ast.BitAnd, ast.BitOr,
    ast.Eq, ast.NotEq, ast.Lt, ast.LtE, ast.Gt, ast.GtE,
)


def validate_expr(expr: str, columns: list[str]) -> None:
    # cek rumus SEBELUM dijalanin: cuma boleh angka, nama kolom, konstanta, fungsi matematika
    if '^' in expr:
        raise PlanError(f"rumus '{expr}' pakai '^'. Untuk pangkat pakai '**'")
    try:
        tree = ast.parse(expr, mode='eval')
    except SyntaxError as e:
        raise PlanError(f"rumus '{expr}' gak valid: {e.msg}") from e

    for node in ast.walk(tree):
        if not isinstance(node, _ALLOWED_NODES):
            raise PlanError(f"rumus '{expr}' pakai sintaks yang gak diizinkan: {type(node).__name__}")
        if isinstance(node, ast.Call):
            if not isinstance(node.func, ast.Name) or node.func.id not in ALLOWED_FUNCS:
                raise PlanError(f"rumus '{expr}': fungsi yang boleh cuma {sorted(ALLOWED_FUNCS)}")
            if node.keywords:
                raise PlanError(f"rumus '{expr}': fungsi gak boleh pakai argumen bernama")
        if isinstance(node, ast.Name):
            allowed = set(columns) | set(CONSTANTS) | ALLOWED_FUNCS
            if node.id not in allowed:
                raise PlanError(f"rumus '{expr}': '{node.id}' bukan kolom. Kolom yang ada: {columns}")


def _need(step: Step, *names: str) -> None:
    # pastiin parameter wajib buat op ini diisi
    for name in names:
        if getattr(step, name) in (None, [], ''):
            raise PlanError(f"op '{step.op}' butuh parameter '{name}'")


def _check_columns(df: pd.DataFrame, cols: list[str]) -> None:
    missing = [c for c in cols if c not in df.columns]
    if missing:
        raise PlanError(f'kolom {missing} gak ada. Kolom yang ada: {list(df.columns)}')


# ---------- satu fungsi per op ----------

def op_compute(df: pd.DataFrame, step: Step) -> pd.DataFrame:
    # bikin kolom baru dari rumus, contoh: T = waktu_10_ayunan / 10
    _need(step, 'new_column', 'expr')
    validate_expr(step.expr, list(df.columns))
    df = df.copy()
    df[step.new_column] = df.eval(step.expr, resolvers=[CONSTANTS])
    return df


def op_filter(df: pd.DataFrame, step: Step) -> pd.DataFrame:
    # saring baris, contoh: percobaan > 1 and panjang_tali <= 1
    _need(step, 'expr')
    validate_expr(step.expr, list(df.columns))
    return df.query(step.expr, resolvers=[CONSTANTS])


def op_select(df: pd.DataFrame, step: Step) -> pd.DataFrame:
    # pilih + urutin kolom (dipakai buat nyamain format template)
    _need(step, 'columns')
    _check_columns(df, step.columns)
    return df[step.columns]


def op_rename(df: pd.DataFrame, step: Step) -> pd.DataFrame:
    _need(step, 'renames')
    mapping = {r.old: r.new for r in step.renames}
    _check_columns(df, list(mapping))
    return df.rename(columns=mapping)


def op_sort(df: pd.DataFrame, step: Step) -> pd.DataFrame:
    _need(step, 'by')
    _check_columns(df, step.by)
    return df.sort_values(step.by, ascending=not step.descending)


def op_round(df: pd.DataFrame, step: Step) -> pd.DataFrame:
    # kalau columns kosong: bulatin semua kolom angka
    _need(step, 'decimals')
    cols = step.columns or list(df.select_dtypes('number').columns)
    _check_columns(df, cols)
    df = df.copy()
    df[cols] = df[cols].round(step.decimals)
    return df


def op_group_agg(df: pd.DataFrame, step: Step) -> pd.DataFrame:
    # rata-rata/jumlah per kelompok, contoh: rata-rata g per panjang_tali
    _need(step, 'by', 'aggregations')
    _check_columns(df, step.by + [a.column for a in step.aggregations])
    named = {a.output: (a.column, a.func) for a in step.aggregations}
    return df.groupby(step.by, as_index=False).agg(**named)


def op_aggregate(df: pd.DataFrame, step: Step) -> pd.DataFrame:
    # ringkasan satu baris untuk seluruh data, contoh: rata-rata g
    _need(step, 'aggregations')
    _check_columns(df, [a.column for a in step.aggregations])
    row = {a.output: df[a.column].agg(a.func) for a in step.aggregations}
    return pd.DataFrame([row])


def op_linear_fit(df: pd.DataFrame, step: Step) -> pd.DataFrame:
    # regresi linear y = slope * x + intercept, plus R²
    _need(step, 'x', 'y')
    _check_columns(df, [step.x, step.y])
    x = df[step.x].astype(float).to_numpy()
    y = df[step.y].astype(float).to_numpy()
    if len(x) < 2:
        raise PlanError('linear_fit butuh minimal 2 baris data')
    slope, intercept = np.polyfit(x, y, 1)
    y_pred = slope * x + intercept
    ss_res = float(((y - y_pred) ** 2).sum())
    ss_tot = float(((y - y.mean()) ** 2).sum())
    r2 = 1 - ss_res / ss_tot if ss_tot else 1.0
    return pd.DataFrame([{'slope': slope, 'intercept': intercept, 'r2': r2}])


OPERATIONS = {
    'compute': op_compute,
    'filter': op_filter,
    'select': op_select,
    'rename': op_rename,
    'sort': op_sort,
    'round': op_round,
    'group_agg': op_group_agg,
    'aggregate': op_aggregate,
    'linear_fit': op_linear_fit,
}


def apply_step(df: pd.DataFrame, step: Step) -> pd.DataFrame:
    try:
        return OPERATIONS[step.op](df, step)
    except PlanError:
        raise
    except Exception as e:  # error pandas lain juga diubah jadi PlanError biar bisa dibenerin LLM
        raise PlanError(f"op '{step.op}' gagal: {type(e).__name__}: {e}") from e


def describe_step(step: Step) -> str:
    # versi "manusia" dari tiap step, ditampilin di bawah tabel
    match step.op:
        case 'compute':
            return f'{step.new_column} = {step.expr}'
        case 'filter':
            return f'filter: {step.expr}'
        case 'select':
            return f"kolom: {', '.join(step.columns or [])}"
        case 'rename':
            return 'ganti nama: ' + ', '.join(f'{r.old} → {r.new}' for r in step.renames or [])
        case 'sort':
            arah = 'besar → kecil' if step.descending else 'kecil → besar'
            return f"urutkan {', '.join(step.by or [])} ({arah})"
        case 'round':
            cols = ', '.join(step.columns) if step.columns else 'semua angka'
            return f'bulatkan {cols} ke {step.decimals} desimal'
        case 'group_agg' | 'aggregate':
            aggs = ', '.join(f'{a.output} = {a.func}({a.column})' for a in step.aggregations or [])
            per = f" per {', '.join(step.by)}" if step.op == 'group_agg' and step.by else ''
            return f'{aggs}{per}'
        case 'linear_fit':
            return f'regresi linear: {step.y} = slope × {step.x} + intercept'
    return step.op
```

🧩 Bikin `tests/test_operations.py`:

```python
import pandas as pd
import pytest

from data_agent.custom_types import Aggregation, Step
from data_agent.operations import PlanError, apply_step, validate_expr

COLS = ['a', 'b']


def df() -> pd.DataFrame:
    return pd.DataFrame({'a': [1.0, 4.0, 9.0], 'b': [2, 2, 3], 'grup': ['x', 'y', 'x']})


# ---------- validasi rumus ----------
def test_rumus_valid_lolos():
    validate_expr('sqrt(a) * pi + b ** 2', COLS)


@pytest.mark.parametrize('expr', [
    "__import__('os').system('ls')",  # nyoba jalanin perintah sistem
    'a.__class__',                     # akses atribut
    'c + 1',                           # kolom gak ada
    'a ^ 2',                           # ^ bukan pangkat di Python
    'max(a)',                          # fungsi gak diizinkan
])
def test_rumus_berbahaya_atau_salah_ditolak(expr):
    with pytest.raises(PlanError):
        validate_expr(expr, COLS)


# ---------- tiap op ----------
def test_compute():
    out = apply_step(df(), Step(op='compute', new_column='c', expr='a / b'))
    assert out['c'].tolist() == [0.5, 2.0, 3.0]


def test_filter():
    out = apply_step(df(), Step(op='filter', expr="a > 2 and grup == 'x'"))
    assert out['a'].tolist() == [9.0]


def test_round_semua_kolom_angka():
    data = pd.DataFrame({'x': [1.23456], 'y': [2.98765], 'nama': ['a']})
    out = apply_step(data, Step(op='round', decimals=2))
    assert out.iloc[0].tolist() == [1.23, 2.99, 'a']


def test_group_agg():
    step = Step(op='group_agg', by=['grup'],
                aggregations=[Aggregation(column='a', func='sum', output='total')])
    out = apply_step(df(), step)
    assert dict(zip(out['grup'], out['total'])) == {'x': 10.0, 'y': 4.0}


def test_aggregate_jadi_satu_baris():
    step = Step(op='aggregate', aggregations=[Aggregation(column='a', func='mean', output='rata')])
    out = apply_step(df(), step)
    assert out.shape == (1, 1) and out['rata'][0] == pytest.approx(14 / 3)


def test_linear_fit():
    data = pd.DataFrame({'x': [1, 2, 3], 'y': [3, 5, 7]})  # y = 2x + 1
    out = apply_step(data, Step(op='linear_fit', x='x', y='y'))
    assert out['slope'][0] == pytest.approx(2)
    assert out['intercept'][0] == pytest.approx(1)
    assert out['r2'][0] == pytest.approx(1)


def test_parameter_wajib_kosong():
    with pytest.raises(PlanError, match="butuh parameter 'expr'"):
        apply_step(df(), Step(op='compute', new_column='c'))


def test_kolom_gak_ada():
    with pytest.raises(PlanError, match='gak ada'):
        apply_step(df(), Step(op='select', columns=['zzz']))
```

✅ **Cek:**

```fish
uv run pytest tests/test_operations.py -v
```

---

## Langkah 8: `executor.py`: jalanin rencana

🎯 **Tujuan:** jalanin `Plan` tabel demi tabel, step demi step.

💡 **Konsep:** tabel yang udah jadi disimpan di `frames`, jadi bisa dipakai jadi `source` tabel berikutnya. Contoh: tabel "Ringkasan" ngambil rata-rata dari tabel "Hasil".

```
frames = {"data": <sheet Excel>}
tabel "hasil"     (source="data")  → frames["hasil"] = ...
tabel "ringkasan" (source="hasil") → pakai hasil tabel sebelumnya
```

🧩 Bikin `src/data_agent/executor.py`:

```python
# executor.py: jalanin rencana (Plan) langkah demi langkah pakai pandas
import json

import pandas as pd

from data_agent.custom_types import Plan, ResultTable
from data_agent.operations import PlanError, apply_step, describe_step


def to_result_table(table_id: str, title: str, df: pd.DataFrame, formulas: list[str]) -> ResultTable:
    # to_json -> json.loads: ubah NaN jadi null dan tipe numpy jadi angka biasa
    data = json.loads(df.to_json(orient='split', index=False))
    return ResultTable(id=table_id, title=title, columns=data['columns'],
                       rows=data['data'], formulas=formulas)


def run_plan(plan: Plan, sheets: dict[str, pd.DataFrame]) -> list[ResultTable]:
    frames = dict(sheets)  # sumber data: sheet Excel + tabel yang udah jadi
    results: list[ResultTable] = []

    for table in plan.tables:
        if table.source not in frames:
            raise PlanError(
                f"tabel '{table.id}': source '{table.source}' gak ada. "
                f'Yang ada: {list(frames)}'
            )
        df = frames[table.source]
        for i, step in enumerate(table.steps, start=1):
            try:
                df = apply_step(df, step)
            except PlanError as e:
                raise PlanError(f"tabel '{table.id}', step {i}: {e}") from e

        frames[table.id] = df  # tabel ini bisa jadi source tabel berikutnya
        formulas = [describe_step(s) for s in table.steps]
        results.append(to_result_table(table.id, table.title, df, formulas))

    return results
```

🧩 Bikin `src/data_agent/evaluate.py` sekarang juga, karena fungsi `compare()`-nya dipakai di test (cara jalanin script eval-nya ada di Langkah 13):

```python
# evaluate.py: jalanin semua contoh di samples/ dan bandingin sama expected.json
# jalanin: uv run data-agent-eval
# dipakai tiap kali ganti model / ubah prompt, biar ketahuan hasilnya makin bagus atau jelek
import json
import logging
import math
import sys
import tempfile
from pathlib import Path

from data_agent.doc_loader import classify

SAMPLES_DIR = Path('samples')
TOLERANCE = 1e-3  # selisih relatif yang masih dianggap sama


def _same(a, b) -> bool:
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        return math.isclose(a, b, rel_tol=TOLERANCE, abs_tol=TOLERANCE)
    return str(a).strip() == str(b).strip()


def compare(expected: list[dict], actual: list[dict]) -> list[str]:
    # balikin daftar masalah; kosong = lolos
    problems = []
    if len(expected) != len(actual):
        problems.append(f'jumlah tabel: harusnya {len(expected)}, dapat {len(actual)}')
    for i, (exp, act) in enumerate(zip(expected, actual), start=1):
        if len(exp['rows']) != len(act['rows']):
            problems.append(f"tabel {i}: jumlah baris {len(act['rows'])}, harusnya {len(exp['rows'])}")
            continue
        for r, (er, ar) in enumerate(zip(exp['rows'], act['rows']), start=1):
            if len(er) != len(ar) or not all(_same(x, y) for x, y in zip(er, ar)):
                problems.append(f'tabel {i} baris {r}: dapat {ar}, harusnya {er}')
                break
    return problems


def main() -> None:
    # import di dalam fungsi: compare() bisa dipakai test tanpa harus nyiapin pipeline/LLM
    from data_agent.pipeline import run_all

    logging.basicConfig(level=logging.WARNING)
    folders = sorted(p for p in SAMPLES_DIR.iterdir() if (p / 'expected.json').exists())
    passed = 0
    for folder in folders:
        files = [str(f) for f in folder.iterdir() if classify(f.name)]
        guides = [f for f in files if classify(f) == 'guide']
        data = [f for f in files if classify(f) == 'data'][0]
        expected = json.loads((folder / 'expected.json').read_text())['tables']

        with tempfile.TemporaryDirectory() as work_dir:
            try:
                result = run_all(guides, data, work_dir)
                problems = compare(expected, [t.model_dump() for t in result.tables])
            except Exception as e:
                problems = [f'error: {e}']

        if problems:
            print(f'❌ {folder.name}')
            for p in problems:
                print('   -', p)
        else:
            passed += 1
            print(f'✅ {folder.name}')

    print(f'\n{passed}/{len(folders)} sample lolos')
    sys.exit(0 if passed == len(folders) else 1)
```

🧩 Bikin `tests/test_executor.py`:

```python
import json

import pytest

from data_agent.custom_types import Plan, Step, TablePlan
from data_agent.doc_loader import read_data
from data_agent.evaluate import compare
from data_agent.executor import run_plan
from data_agent.operations import PlanError


def test_rencana_bandul_sesuai_jawaban(bandul_dir, bandul_plan):
    sheets = read_data(str(bandul_dir / 'data.xlsx'))
    tables = run_plan(bandul_plan, sheets)
    expected = json.loads((bandul_dir / 'expected.json').read_text())['tables']

    assert compare(expected, [t.model_dump() for t in tables]) == []
    assert tables[0].columns == ['Percobaan', 'L (m)', 'T (s)', 'g (m/s2)']  # format template
    assert 'g = 4 * pi ** 2 * panjang_tali_m / t_periode ** 2' in tables[0].formulas


def test_source_salah(bandul_dir):
    sheets = read_data(str(bandul_dir / 'data.xlsx'))
    plan = Plan(tables=[TablePlan(id='x', title='X', source='gak_ada', steps=[])])
    with pytest.raises(PlanError, match="source 'gak_ada'"):
        run_plan(plan, sheets)


def test_error_nyebut_tabel_dan_step(bandul_dir):
    sheets = read_data(str(bandul_dir / 'data.xlsx'))
    plan = Plan(tables=[TablePlan(id='hasil', title='H', source='data', steps=[
        Step(op='compute', new_column='T', expr='waktu / 10'),  # kolom "waktu" gak ada
    ])])
    with pytest.raises(PlanError, match="tabel 'hasil', step 1"):
        run_plan(plan, sheets)
```

✅ **Cek:**

```fish
uv run pytest tests/test_executor.py -v
```

`test_rencana_bandul_sesuai_jawaban` lolos = op + executor ngitung persis kayak jawaban manual. 🎉

---

## Langkah 9: `prompts.py`: semua prompt di satu tempat

🎯 **Tujuan:** 3 prompt: ekstrak instruksi, bikin rencana, review.

💡 **Konsep:**
- prompt ditulis **bahasa Inggris** (model lebih konsisten), tapi model diminta tetap pakai **bahasa dokumen** buat judul & isi tabel
- `OPS_REFERENCE` = "buku manual" op buat LLM. **Harus selalu sama** dengan isi `operations.py`
- `make_plan()` bisa nerima rencana sebelumnya + pesan error buat percobaan ulang

🧩 Bikin `src/data_agent/prompts.py`:

```python
# prompts.py: semua teks prompt dikumpulin di sini
# prompt ditulis dalam bahasa Inggris karena model lebih konsisten,
# tapi model diminta tetap pakai bahasa dokumen untuk judul & isi tabel
import json

from data_agent.custom_types import InputBundle, Instructions, Plan, ResultTable

OPS_REFERENCE = """
Available operations (field "op") and their parameters:
- compute:    new_column, expr   -> add a column from a formula, e.g. expr "waktu / 10"
- filter:     expr               -> keep rows where the condition is true, e.g. "nilai > 0 and grup == 'A'"
- select:     columns            -> keep and ORDER these columns (use it last to match a template)
- rename:     renames [{old, new}] -> rename columns (use it to match column names in a template)
- sort:       by, descending
- round:      decimals, columns (optional, empty = all numeric columns)
- group_agg:  by, aggregations [{column, func, output}] -> one row per group
- aggregate:  aggregations [{column, func, output}]     -> ONE summary row for the whole table
- linear_fit: x, y               -> one row with slope, intercept, r2
func is one of: mean, sum, min, max, count, std, median

Formula rules (expr):
- use ONLY column names that exist at that point (listed below, plus columns you created earlier)
- power is ** (never ^). Constants: pi, e. Functions: sqrt, abs, log, log10, exp, sin, cos, tan
- strings in conditions use single quotes: grup == 'A'

Table rules:
- each table has: id (snake_case, unique), title (in the document's language), source, steps
- source is a sheet name from the data OR the id of an EARLIER table
  (e.g. a summary table can use source = id of the detailed table)
- make exactly one table for each table the guide asks for, in the same order
""".strip()


def _data_block(bundle: InputBundle) -> str:
    parts = []
    for s in bundle.sheets:
        parts.append(
            f'Sheet "{s.name}" ({s.n_rows} rows)\n'
            f'Columns and types: {json.dumps(s.dtypes)}\n'
            f'First rows: {json.dumps(s.sample_rows, ensure_ascii=False)}'
        )
    return '\n\n'.join(parts)


def _guide_block(bundle: InputBundle) -> str:
    text = bundle.guide_text or '(no extractable text, read the attached images)'
    note = f'\n({len(bundle.guide_images)} guide image(s) attached)' if bundle.guide_images else ''
    return text + note


def extract_instructions(bundle: InputBundle) -> str:
    return f"""You read a GUIDE that explains how to process raw (experimental) data into tables.

List every instruction in the guide as short, self-contained items:
formulas (write them exactly), rounding, filters, units, sorting,
and the required table layout (column names and their order) if the guide shows a template.
Also list the tables the guide asks for, in order.
Do not invent instructions that are not in the guide. Keep the guide's language.

GUIDE:
{_guide_block(bundle)}

DATA (only the structure and first rows, for context):
{_data_block(bundle)}"""


def make_plan(bundle: InputBundle, instructions: Instructions,
              previous: Plan | None = None, error: str | None = None) -> str:
    retry = ''
    if previous is not None and error:
        retry = f"""

Your previous plan FAILED with this error:
{error}
Previous plan:
{previous.model_dump_json()}
Fix the problem and return the full corrected plan."""

    return f"""Turn these instructions into a processing plan that will be executed with pandas.
Do NOT calculate numbers yourself; only describe the steps.

{OPS_REFERENCE}

INSTRUCTIONS:
{json.dumps(instructions.items, ensure_ascii=False, indent=1)}

TABLES REQUESTED:
{json.dumps(instructions.expected_tables, ensure_ascii=False)}

DATA:
{_data_block(bundle)}{retry}"""


def review(instructions: Instructions, tables: list[ResultTable]) -> str:
    preview = [
        {'title': t.title, 'columns': t.columns, 'first_rows': t.rows[:5], 'steps': t.formulas}
        for t in tables
    ]
    return f"""Check whether each instruction was followed in the result tables.
For every instruction give: instruction (copy it), done (true/false), note (short reason,
in the instruction's language). Be strict: a wrong formula or a missing column means done = false.

INSTRUCTIONS:
{json.dumps(instructions.items, ensure_ascii=False, indent=1)}

RESULT TABLES:
{json.dumps(preview, ensure_ascii=False, indent=1)}"""
```

✅ **Cek:**

```fish
uv run python -c "from data_agent import prompts; print(prompts.OPS_REFERENCE[:200])"
```

---

## Langkah 10: `pipeline.py`: 5 tahap jadi fungsi biasa

🎯 **Tujuan:** tiap tahap proses jadi fungsi biasa yang bisa dites tanpa Inngest.

💡 **Konsep 1:** `main.py` nanti tinggal ngebungkus tiap fungsi ini jadi 1 step Inngest. Karena fungsi biasa, gampang dites & dijalanin dari terminal.

💡 **Konsep 2: self-correction.** Di `step_plan`, rencana langsung **diuji di data asli**. Kalau error, pesan errornya dikirim ke LLM buat dibenerin (maks 3x):

```
LLM: compute T = waktu / 10
pandas: ❌ 'waktu' bukan kolom. Kolom yang ada: [percobaan, panjang_tali_m, waktu_10_ayunan_s]
LLM: compute T = waktu_10_ayunan_s / 10   ✅
```

💡 **Konsep 3: test pakai LLM palsu (`monkeypatch`).** Di test, `llm.structured` diganti fungsi palsu yang jawabannya udah kita tentuin. Jadi test jalan cepat, gratis, dan hasilnya selalu sama.

🧩 Bikin `src/data_agent/pipeline.py`:

```python
# pipeline.py: tahap-tahap proses, masing-masing fungsi biasa
# main.py ngebungkus tiap fungsi ini jadi 1 step Inngest,
# tapi karena fungsi biasa, gampang dites & dijalanin tanpa Inngest
import logging

from data_agent import llm, prompts
from data_agent.custom_types import InputBundle, Instructions, JobResult, Plan, Review, TableSet
from data_agent.doc_loader import load_inputs, read_data
from data_agent.executor import run_plan
from data_agent.operations import PlanError

logger = logging.getLogger(__name__)
MAX_PLAN_ATTEMPTS = 3  # rencana gagal dijalanin -> error dikirim ke LLM buat dibenerin


def step_load(guide_paths: list[str], data_path: str, work_dir: str) -> InputBundle:
    return load_inputs(guide_paths, data_path, work_dir)


def step_extract(bundle: InputBundle) -> Instructions:
    return llm.structured(prompts.extract_instructions(bundle), Instructions,
                          images=bundle.guide_images, label='extract')


def step_plan(bundle: InputBundle, instructions: Instructions) -> Plan:
    sheets = read_data(bundle.data_path)
    plan: Plan | None = None
    error: str | None = None

    for attempt in range(1, MAX_PLAN_ATTEMPTS + 1):
        prompt = prompts.make_plan(bundle, instructions, previous=plan, error=error)
        plan = llm.structured(prompt, Plan, label='plan')
        try:
            run_plan(plan, sheets)  # "uji coba" di data asli: kalau error, ketahuan di sini
            return plan
        except PlanError as e:
            error = str(e)
            logger.warning('rencana gagal (percobaan %s): %s', attempt, error)

    raise PlanError(f'rencana tetap gagal setelah {MAX_PLAN_ATTEMPTS} percobaan: {error}')


def step_run(bundle: InputBundle, plan: Plan) -> TableSet:
    return TableSet(tables=run_plan(plan, read_data(bundle.data_path)))


def step_review(instructions: Instructions, tables: TableSet) -> Review:
    return llm.structured(prompts.review(instructions, tables.tables), Review, label='review')


def run_all(guide_paths: list[str], data_path: str, work_dir: str) -> JobResult:
    # semua tahap berurutan, tanpa Inngest (buat CLI & evaluasi)
    bundle = step_load(guide_paths, data_path, work_dir)
    instructions = step_extract(bundle)
    plan = step_plan(bundle, instructions)
    tables = step_run(bundle, plan)
    review = step_review(instructions, tables)
    return JobResult(instructions=instructions, plan=plan, tables=tables.tables, review=review)
```

🧩 Bikin `tests/test_pipeline.py`:

```python
# test pipeline TANPA model asli: llm.structured diganti fungsi palsu (monkeypatch)
from data_agent import pipeline
from data_agent.custom_types import Instructions, Plan, Review, Step, TablePlan


def test_rencana_salah_dibenerin_pakai_pesan_error(bandul_dir, bandul_plan, monkeypatch):
    bad_plan = Plan(tables=[TablePlan(id='hasil', title='H', source='data', steps=[
        Step(op='compute', new_column='T', expr='waktu / 10'),  # kolom salah
    ])])
    answers = [bad_plan, bandul_plan]  # jawaban pertama salah, kedua benar
    prompts_seen = []

    def fake_structured(prompt, schema, images=None, label=''):
        prompts_seen.append(prompt)
        return answers.pop(0)

    monkeypatch.setattr(pipeline.llm, 'structured', fake_structured)
    bundle = pipeline.step_load([str(bandul_dir / 'guide.pdf')], str(bandul_dir / 'data.xlsx'),
                                str(bandul_dir.parent.parent / 'uploads' / 'test'))
    plan = pipeline.step_plan(bundle, Instructions(items=['T = t / 10'], expected_tables=['H']))

    assert plan == bandul_plan
    assert 'FAILED' in prompts_seen[1] and "'waktu' bukan kolom" in prompts_seen[1]


def test_run_all_dengan_llm_palsu(bandul_dir, bandul_plan, monkeypatch, tmp_path):
    def fake_structured(prompt, schema, images=None, label=''):
        if schema is Instructions:
            return Instructions(items=['hitung T', 'hitung g'], expected_tables=['Hasil', 'Ringkasan'])
        if schema is Plan:
            return bandul_plan
        return Review(items=[])

    monkeypatch.setattr(pipeline.llm, 'structured', fake_structured)
    result = pipeline.run_all([str(bandul_dir / 'guide.pdf')], str(bandul_dir / 'data.xlsx'), str(tmp_path))
    assert [t.title for t in result.tables] == ['Hasil Perhitungan', 'Ringkasan']
    assert result.tables[1].rows == [[9.791, 0.09]]
```

✅ **Cek:**

```fish
uv run pytest -v
```

Semua test sejauh ini lolos.

---

## Langkah 11: (jeda) commit pertama

🎯 **Tujuan:** simpan progress ke git.

```fish
cd ..                     # ke folder DATA-PROCESSOR
git init                  # kalau DATA-PROCESSOR belum di dalam repo lain
git add backend
git status                # pastiin .env, .venv, uploads GAK ada di daftar
git commit -m "backend: loader, operations, executor, pipeline + tests"
cd backend
```

> Kalau `DATA-PROCESSOR` ada **di dalam** repo `AI APPS` (sebelahan sama RAG-PDF), lewatin `git init`, langsung `git add` aja. Repo git di dalam repo git lain bikin ribet.

---

## Langkah 12: `cli.py`: jalanin pakai model asli 🚀

🎯 **Tujuan:** pertama kali jalanin **seluruh pipeline** pakai Ollama, dari terminal.

🧩 Bikin `src/data_agent/cli.py`:

```python
# cli.py: CLI buat jalanin pipeline langsung dari terminal (tanpa server)
# contoh: uv run data-agent samples/bandul/guide.pdf samples/bandul/data.xlsx
import argparse
import json
import logging
import tempfile


def main() -> None:
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(name)s: %(message)s')
    logging.getLogger('httpx').setLevel(logging.WARNING)

    parser = argparse.ArgumentParser(description='Proses data mentah sesuai guide')
    parser.add_argument('files', nargs='+', help='file guide (PDF/gambar) + 1 file data (.xlsx/.csv)')
    parser.add_argument('--json', action='store_true', help='print hasil lengkap sebagai JSON')
    args = parser.parse_args()

    # import di sini biar `--help` tetap jalan walau .env belum ada
    from data_agent.doc_loader import classify
    from data_agent.pipeline import run_all

    guides = [f for f in args.files if classify(f) == 'guide']
    datas = [f for f in args.files if classify(f) == 'data']
    if not guides or len(datas) != 1:
        parser.error('butuh minimal 1 guide dan tepat 1 file data')

    with tempfile.TemporaryDirectory() as work_dir:
        result = run_all(guides, datas[0], work_dir)

    if args.json:
        print(json.dumps(result.model_dump(mode='json'), ensure_ascii=False, indent=2))
        return

    for table in result.tables:
        print(f'\n=== {table.title} ===')
        print(' | '.join(table.columns))
        for row in table.rows:
            print(' | '.join(str(v) for v in row))
        print('rumus:', '; '.join(table.formulas))
    print('\n=== cek instruksi ===')
    for item in result.review.items:
        print('✅' if item.done else '❌', item.instruction, '-', item.note)
```

✅ **Cek:**

```fish
uv run data-agent samples/bandul/guide.pdf samples/bandul/data.xlsx
```

Yang diharapkan: log 3 panggilan LLM (`extract`, `plan`, `review`), lalu 2 tabel:

```
=== Hasil Perhitungan ===
Percobaan | L (m) | T (s) | g (m/s2)
1 | 0.3 | 1.102 | 9.753
...
=== Ringkasan ===
g rata-rata | error (%)
9.791 | 0.09
```

Mau lihat rencana yang dibikin LLM? Tambahin `--json`. Kalau angkanya beda, bandingin rencananya sama `bandul_plan` di `tests/conftest.py`. Biasanya beda di urutan pembulatan atau nama kolom.

> 🔄 Di laptop yang cuma CPU, perintah ini bisa makan **belasan sampai puluhan menit**. Pantau lognya: tiap baris `data_agent.llm` = 1 panggilan model selesai.

---

## Langkah 13: `evaluate.py`: rapor otomatis

🎯 **Tujuan:** satu perintah buat ngecek semua sample. Jalanin tiap kali **ganti model** atau **ubah prompt**.

`evaluate.py` udah dibikin di Langkah 8, dan perintahnya udah didaftarin di `pyproject.toml` (Langkah 1).

✅ **Cek:**

```fish
uv run data-agent-eval
```

```
✅ bandul

1/1 sample lolos
```

Nambah sample baru = bikin folder baru di `samples/` berisi guide + data + `expected.json` (lihat [G5](#g5-cara-nambah-sample-baru)).

---

## Langkah 14: `jobs.py` + `main.py`: server FastAPI + Inngest

🎯 **Tujuan:** pipeline bisa dipanggil lewat API, jalan di background via Inngest.

💡 **Konsep 1: endpoint.**

| Endpoint | Fungsi |
|---|---|
| `GET /api/health` | cek server hidup + model apa |
| `POST /api/jobs` | upload file → simpan → kirim event ke Inngest → balikin `event_id` |
| `GET /api/jobs/{event_id}` | status: `running` / `completed` / `failed` (+ hasil) |
| `GET /api/jobs/{event_id}/export` | download hasil sebagai Excel |
| `/api/inngest` | dipakai Inngest dev server (otomatis) |

💡 **Konsep 2: `in_thread`.** Fungsi pipeline itu "blocking" (nunggu LLM). Dijalanin di thread lain biar server tetap bisa ngelayanin request lain (misal cek status).

💡 **Konsep 3: keamanan upload.**
- cuma ekstensi tertentu yang diterima
- maksimal `MAX_UPLOAD_MB`
- `Path(filename).name` → nama file kayak `../../x.xlsx` gak bisa "kabur" dari folder upload

💡 **Konsep 4: CORS.** Frontend (`localhost:5173`) dan backend (`localhost:8000`) beda "origin". Browser ngeblok request lintas origin, kecuali server bilang boleh lewat `CORSMiddleware`.

💡 🔄 **Konsep 5: status job dari Inngest.** Inngest dev server punya 2 endpoint yang kelihatannya sama:

```
GET /v1/events/{event_id}/runs   → daftar run buat 1 event   (dipakai buat nyari run_id aja)
GET /v1/runs/{run_id}            → detail 1 run              (status + output yang BENER)
```

Di inngest-cli 1.46, daftar run per event bisa udah bilang `"Completed"` padahal run-nya **masih jalan** (`ended_at: null`, belum ada `output`). Kalau cuma pakai endpoint pertama, frontend berhenti polling dan nampilin hasil kosong. Jadi `jobs.py` ngambil status dari endpoint kedua.

🧩 Bikin `src/data_agent/jobs.py`:

```python
# jobs.py: nanya status job ke Inngest dev server + bikin file Excel dari hasilnya
import io
from typing import Any, Literal

import httpx
import pandas as pd
from pydantic import BaseModel

from data_agent import config


class JobStatus(BaseModel):
    status: Literal['running', 'completed', 'failed']
    result: dict[str, Any] | None = None   # isi JobResult kalau udah selesai
    error: str | None = None


async def get_job_status(event_id: str) -> JobStatus:
    # satu event -> satu "run" di Inngest. Kita tanya statusnya lewat REST API dev server
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(f'{config.INNGEST_API_BASE}/events/{event_id}/runs')
        resp.raise_for_status()
        runs = resp.json().get('data') or []
        if not runs:
            return JobStatus(status='running')  # run belum kebikin, tunggu sebentar

        # daftar run per event cuma dipakai buat nyari run_id: status di situ bisa udah
        # "Completed" padahal run masih jalan (dan output-nya belum ada).
        # status + output yang bener diambil dari detail run-nya langsung
        resp = await client.get(f"{config.INNGEST_API_BASE}/runs/{runs[0]['run_id']}")
        resp.raise_for_status()

    run = resp.json().get('data') or {}
    status = run.get('status')
    if status == 'Completed':
        return JobStatus(status='completed', result=run.get('output'))
    if status in ('Failed', 'Cancelled'):
        # output error dari Inngest bentuknya {name, message, stack, ...}: ambil pesannya aja
        output = run.get('output')
        message = output.get('message') if isinstance(output, dict) else None
        return JobStatus(status='failed', error=message or str(output))
    return JobStatus(status='running')


def tables_to_excel(result: dict[str, Any]) -> bytes:
    # tiap tabel jadi satu sheet di file Excel
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        for i, table in enumerate(result.get('tables', []), start=1):
            df = pd.DataFrame(table['rows'], columns=table['columns'])
            sheet = f"{i}_{table['id']}"[:31]  # nama sheet Excel maksimal 31 karakter
            df.to_excel(writer, sheet_name=sheet, index=False)
    return buffer.getvalue()
```

🧩 Bikin `src/data_agent/main.py`:

```python
# main.py: server FastAPI + fungsi Inngest
# jalanin: uv run uvicorn data_agent.main:app --reload --port 8000
import asyncio
import logging
import uuid
from collections.abc import Callable
from pathlib import Path

import inngest
import inngest.fast_api
from fastapi import FastAPI, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response

from data_agent import config, pipeline
from data_agent.custom_types import InputBundle, Instructions, JobResult, Plan, Review, TableSet
from data_agent.doc_loader import classify
from data_agent.jobs import JobStatus, get_job_status, tables_to_excel

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(name)s: %(message)s')
logging.getLogger('httpx').setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

app = FastAPI(title='Data Process Agent')

# CORS: izinin frontend (beda port = beda "origin") manggil API ini dari browser
app.add_middleware(
    CORSMiddleware,
    allow_origins=[config.FRONTEND_ORIGIN],
    allow_methods=['*'],
    allow_headers=['*'],
)

inngest_client = inngest.Inngest(
    app_id='data-process-agent',
    logger=logging.getLogger('uvicorn'),
    is_production=False,
    serializer=inngest.PydanticSerializer(),
)


def in_thread(fn: Callable) -> Callable:
    # fungsi pipeline itu "blocking" (nunggu LLM / baca file).
    # dijalanin di thread lain biar server tetap bisa ngelayanin request lain
    async def wrapper(*args):
        return await asyncio.to_thread(fn, *args)
    return wrapper


# ---------- fungsi Inngest: 5 step ----------
@inngest_client.create_function(
    fn_id='process-data-job',
    trigger=inngest.TriggerEvent(event='data/process'),
    retries=1,
)
async def process_job(ctx: inngest.Context) -> dict:
    data = ctx.event.data
    guide_paths = [str(p) for p in data['guide_paths']]
    data_path = str(data['data_path'])
    work_dir = str(data['work_dir'])

    bundle = await ctx.step.run('load_inputs', in_thread(pipeline.step_load),
                                guide_paths, data_path, work_dir, output_type=InputBundle)
    instructions = await ctx.step.run('extract_instructions', in_thread(pipeline.step_extract),
                                      bundle, output_type=Instructions)
    plan = await ctx.step.run('make_plan', in_thread(pipeline.step_plan),
                              bundle, instructions, output_type=Plan)
    tables = await ctx.step.run('run_plan', in_thread(pipeline.step_run),
                                bundle, plan, output_type=TableSet)
    review = await ctx.step.run('review', in_thread(pipeline.step_review),
                                instructions, tables, output_type=Review)

    result = JobResult(instructions=instructions, plan=plan, tables=tables.tables, review=review)
    return result.model_dump(mode='json')


inngest.fast_api.serve(app, inngest_client, [process_job])


# ---------- endpoint buat frontend ----------
@app.get('/api/health')
async def health() -> dict:
    return {'ok': True, 'model': config.LLM_MODEL}


@app.post('/api/jobs')
async def create_job(files: list[UploadFile]) -> dict:
    # 1. cek file: minimal 1 guide, tepat 1 file data
    guides = [f for f in files if classify(f.filename or '') == 'guide']
    datas = [f for f in files if classify(f.filename or '') == 'data']
    unknown = [f.filename for f in files if classify(f.filename or '') is None]
    if unknown:
        raise HTTPException(400, f'jenis file gak didukung: {unknown}')
    if not guides:
        raise HTTPException(400, 'butuh minimal 1 file guide (PDF/gambar)')
    if len(datas) != 1:
        raise HTTPException(400, 'butuh tepat 1 file data (.xlsx/.csv)')

    # 2. simpan file ke uploads/<job_id>/
    job_id = uuid.uuid4().hex
    job_dir = config.UPLOAD_DIR / job_id
    job_dir.mkdir(parents=True)
    saved: dict[str, list[str]] = {'guide': [], 'data': []}
    for f in guides + datas:
        content = await f.read()
        if len(content) > config.MAX_UPLOAD_MB * 1024 * 1024:
            raise HTTPException(413, f'{f.filename} lebih dari {config.MAX_UPLOAD_MB} MB')
        path = job_dir / Path(f.filename or 'file').name  # cuma nama file, biar gak bisa "kabur" dari folder
        path.write_bytes(content)
        saved[classify(path.name)].append(str(path))

    # 3. kirim event ke Inngest -> fungsi process_job jalan di background
    ids = await inngest_client.send(inngest.Event(name='data/process', data={
        'job_id': job_id,
        'work_dir': str(job_dir),
        'guide_paths': saved['guide'],
        'data_path': saved['data'][0],
    }))
    logger.info('job %s dibuat, event %s', job_id, ids[0])
    return {'job_id': job_id, 'event_id': ids[0]}


@app.get('/api/jobs/{event_id}')
async def job_status(event_id: str) -> JobStatus:
    return await get_job_status(event_id)


@app.get('/api/jobs/{event_id}/export')
async def export_job(event_id: str) -> Response:
    status = await get_job_status(event_id)
    if status.status != 'completed' or not status.result:
        raise HTTPException(409, 'job belum selesai')
    return Response(
        content=tables_to_excel(status.result),
        media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        headers={'Content-Disposition': f'attachment; filename="hasil_{event_id[:8]}.xlsx"'},
    )
```

🧩 Bikin `tests/test_api.py`:

```python
# test endpoint FastAPI pakai TestClient (gak perlu server beneran)
import pytest
from fastapi.testclient import TestClient

from data_agent import main


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(main.config, 'UPLOAD_DIR', tmp_path)
    sent = []

    async def fake_send(event):  # gantiin kirim event ke Inngest
        sent.append(event)
        return ['event-123']

    monkeypatch.setattr(main.inngest_client, 'send', fake_send)
    c = TestClient(main.app)
    c.sent = sent
    return c


def test_health(client):
    assert client.get('/api/health').json()['ok'] is True


def test_upload_tanpa_file_data_ditolak(client):
    res = client.post('/api/jobs', files=[('files', ('guide.pdf', b'%PDF', 'application/pdf'))])
    assert res.status_code == 400 and 'file data' in res.json()['detail']


def test_upload_jenis_file_aneh_ditolak(client):
    res = client.post('/api/jobs', files=[('files', ('virus.exe', b'x', 'application/octet-stream'))])
    assert res.status_code == 400


def test_upload_valid_kirim_event(client, tmp_path):
    files = [
        ('files', ('guide.pdf', b'%PDF', 'application/pdf')),
        ('files', ('../../data.xlsx', b'xlsx', 'application/octet-stream')),  # nama file "nakal"
    ]
    res = client.post('/api/jobs', files=files)
    assert res.status_code == 200 and res.json()['event_id'] == 'event-123'

    data = client.sent[0].data
    assert data['data_path'].startswith(str(tmp_path))  # tetap di dalam folder upload
    assert data['data_path'].endswith('data.xlsx')
```

🧩 🔄 Bikin `tests/test_jobs.py`. Inngest-nya dipalsuin pakai `httpx.MockTransport`, jadi gak perlu dev server:

```python
# test cara baca status job dari Inngest, pakai server Inngest palsu (httpx.MockTransport)
import asyncio

import httpx
import pytest

from data_agent import jobs


def fake_inngest(monkeypatch, runs: list[dict], detail: dict) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if '/events/' in request.url.path:
            return httpx.Response(200, json={'data': runs})       # daftar run per event
        return httpx.Response(200, json={'data': detail})         # detail satu run

    real_client = httpx.AsyncClient
    monkeypatch.setattr(jobs.httpx, 'AsyncClient',
                        lambda **kw: real_client(transport=httpx.MockTransport(handler), **kw))


def status_of(event_id: str = 'evt') -> jobs.JobStatus:
    return asyncio.run(jobs.get_job_status(event_id))


def test_run_belum_kebikin(monkeypatch):
    fake_inngest(monkeypatch, runs=[], detail={})
    assert status_of().status == 'running'


def test_daftar_bilang_completed_tapi_run_masih_jalan(monkeypatch):
    # kejadian asli di inngest-cli 1.46: daftar run udah "Completed" waktu run masih jalan
    fake_inngest(monkeypatch,
                 runs=[{'run_id': 'r1', 'status': 'Completed', 'ended_at': None}],
                 detail={'run_id': 'r1', 'status': 'Running', 'ended_at': None})
    assert status_of().status == 'running'


def test_run_selesai_bawa_hasil(monkeypatch):
    output = {'tables': [{'id': 'hasil'}]}
    fake_inngest(monkeypatch,
                 runs=[{'run_id': 'r1', 'status': 'Completed'}],
                 detail={'run_id': 'r1', 'status': 'Completed', 'output': output})
    job = status_of()
    assert job.status == 'completed' and job.result == output


@pytest.mark.parametrize('status', ['Failed', 'Cancelled'])
def test_run_gagal_cuma_bawa_pesan_error(monkeypatch, status):
    # bentuk output error asli dari Inngest: ada stack trace yang gak perlu ditampilin ke user
    output = {'code': 'step_errored', 'name': 'PlanError',
              'message': 'rencana tetap gagal setelah 3 percobaan', 'stack': 'Traceback ...'}
    fake_inngest(monkeypatch,
                 runs=[{'run_id': 'r1', 'status': status}],
                 detail={'run_id': 'r1', 'status': status, 'output': output})
    job = status_of()
    assert job.status == 'failed' and job.error == 'rencana tetap gagal setelah 3 percobaan'
```

🧩 Bikin `tests/test_inngest_function.py`. Inngest punya client "mocked" buat ngetes fungsi 5 step tanpa dev server:

```python
# test fungsi Inngest lengkap (5 step) pakai client "mocked" dari Inngest + LLM palsu
import inngest
from inngest.experimental import mocked

from data_agent import main, pipeline
from data_agent.custom_types import Instructions, Plan, Review


def test_process_job_jalan_sampai_selesai(bandul_dir, bandul_plan, monkeypatch, tmp_path):
    def fake_structured(prompt, schema, images=None, label=''):
        if schema is Instructions:
            return Instructions(items=['hitung g'], expected_tables=['Hasil', 'Ringkasan'])
        if schema is Plan:
            return bandul_plan
        return Review(items=[])

    monkeypatch.setattr(pipeline.llm, 'structured', fake_structured)
    client = mocked.Inngest(app_id='test', serializer=inngest.PydanticSerializer())
    event = inngest.Event(name='data/process', data={
        'job_id': 'test',
        'work_dir': str(tmp_path),
        'guide_paths': [str(bandul_dir / 'guide.pdf')],
        'data_path': str(bandul_dir / 'data.xlsx'),
    })

    res = mocked.trigger(main.process_job, event, client)

    assert res.status == mocked.Status.COMPLETED
    assert [t['id'] for t in res.output['tables']] == ['hasil', 'ringkasan']
```

✅ **Cek:**

```fish
uv run pytest -v          # 36 test lolos
```

---

## Langkah 15: Jalanin server + Inngest dev server

🎯 **Tujuan:** backend jalan beneran, job bisa dikirim lewat API dan dipantau di dashboard.

🧩 Buka **2 terminal**, dua-duanya di folder `backend/`:

```fish
# terminal 1: server FastAPI
uv run uvicorn data_agent.main:app --reload --port 8000
```

```fish
# terminal 2: Inngest dev server (dashboard di http://localhost:8288)
npx --allow-scripts=inngest-cli inngest-cli@latest dev -u http://127.0.0.1:8000/api/inngest --no-discovery
```

> 🔄 **npm 12:** install script package cuma jalan kalau namanya ada di `allow-scripts`. `inngest-cli` butuh install script buat download binary-nya, jadi wajib `--allow-scripts=inngest-cli`. Flag lama `--ignore-scripts=false` udah **gak cukup**.

✅ **Cek:** di **terminal 3**, kirim job pakai `curl`:

```fish
curl http://localhost:8000/api/health

curl -F files=@samples/bandul/guide.pdf -F files=@samples/bandul/data.xlsx http://localhost:8000/api/jobs
# → {"job_id":"...","event_id":"01J..."}

curl http://localhost:8000/api/jobs/<event_id>
# ulangi sampai "status":"completed"
```

Buka **http://localhost:8288** → menu **Runs** → klik run-nya. Di situ kelihatan 5 step, input/output tiap step, berapa lama, dan error kalau ada. 🎉

Download Excel-nya: buka `http://localhost:8000/api/jobs/<event_id>/export` di browser.

**Part 1 selesai.** Commit dulu:

```fish
cd ..; git add backend; git commit -m "backend: cli, eval, FastAPI + Inngest"; cd backend
```

---
# F. Part 2: Frontend (React)

## Langkah F0: Bikin project Vite + React + TypeScript

🎯 **Tujuan:** kerangka frontend.

🧩 Dari folder `DATA-PROCESSOR/`:

```fish
npm create vite@latest frontend -- --template react-ts
cd frontend
npm install
npm install tailwindcss @tailwindcss/vite @tanstack/react-query @tanstack/react-table react-dropzone
npm install -D @types/node
```

Hapus file contoh yang gak kepake:

```fish
rm -f src/App.css
rm -rf src/assets
```

Ganti judul tab di `index.html`: `<title>frontend</title>` → `<title>Data Process Agent</title>`.

Tambahin `.env` ke `frontend/.gitignore`:

```fish
printf '\n# setting lokal\n.env\n' >> .gitignore
```

Bikin `.env` (alamat backend) dan contohnya:

```fish
printf 'VITE_API_URL=http://localhost:8000\n' > .env
cp .env .env.example
```

> Variabel env di Vite **wajib** diawali `VITE_` biar bisa dibaca dari kode browser. Jangan pernah taruh rahasia di sini: semua yang `VITE_` kelihatan oleh user.

✅ **Cek:** `npm run dev` → buka http://localhost:5173 → muncul halaman contoh Vite.

---

## Langkah F1: Tailwind + alias `@/` + shadcn/ui

🎯 **Tujuan:** styling siap, dan komponen shadcn ke-install.

💡 **Konsep: alias `@/`.** Biar import gak jadi `../../../components/...`:

```ts
import { Button } from '@/components/ui/button'   // @ = folder src/
```

Alias ini harus didaftarin di **dua** tempat: `vite.config.ts` (buat Vite) dan `tsconfig` (buat TypeScript).

🧩 Ganti `vite.config.ts`:

```ts
import path from 'node:path'
import tailwindcss from '@tailwindcss/vite'
import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react(), tailwindcss()],
  resolve: {
    // "@/..." = folder src/, biar import gak "../../../"
    alias: { '@': path.resolve(import.meta.dirname, './src') },
  },
})
```

🧩 Ganti `tsconfig.json`:

```json
{
  "files": [],
  "references": [
    {
      "path": "./tsconfig.app.json"
    },
    {
      "path": "./tsconfig.node.json"
    }
  ],
  "compilerOptions": {
    "paths": {
      "@/*": [
        "./src/*"
      ]
    }
  }
}
```

🧩 Ganti `tsconfig.app.json`:

```json
{
  "compilerOptions": {
    "tsBuildInfoFile": "./node_modules/.tmp/tsconfig.app.tsbuildinfo",
    "target": "es2023",
    "lib": [
      "ES2023",
      "DOM"
    ],
    "module": "esnext",
    "types": [
      "vite/client"
    ],
    "allowArbitraryExtensions": true,
    "skipLibCheck": true,
    "moduleResolution": "bundler",
    "allowImportingTsExtensions": true,
    "verbatimModuleSyntax": true,
    "moduleDetection": "force",
    "noEmit": true,
    "jsx": "react-jsx",
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "erasableSyntaxOnly": true,
    "noFallthroughCasesInSwitch": true,
    "paths": {
      "@/*": [
        "./src/*"
      ]
    }
  },
  "include": [
    "src"
  ]
}
```

🧩 Ganti isi `src/index.css` jadi satu baris aja (nanti shadcn yang nambahin sisanya):

```css
@import "tailwindcss";
```

🧩 Install shadcn/ui:

```fish
npx shadcn@latest init -t vite -b radix -p nova

npx shadcn@latest add button card table badge alert
```

| Flag | Artinya |
|---|---|
| `-t vite` | project-nya Vite |
| `-b radix` | komponen pakai Radix UI. **Wajib**, karena `App.tsx` pakai `<Button asChild>` (itu fitur Radix) |
| `-p nova` | preset tampilan (ikon Lucide, font Geist, base color **Neutral**). 🔄 shadcn 4 nanya preset, bukan base color |

`shadcn init` otomatis:
- bikin `components.json` + `src/lib/utils.ts` (fungsi `cn()` buat gabungin class Tailwind)
- nambahin warna tema ke `src/index.css`
- install `radix-ui`, `class-variance-authority`, `cn`, `lucide-react`, `tw-animate-css`, `@fontsource-variable/geist`

> 🔄 `cn` itu package resmi dari shadcn (repo `shadcn-ui/cn`), pengganti `clsx` + `tailwind-merge` di versi lama. Isi `src/lib/utils.ts` jadi cuma `export { cn } from "cn"`.

`shadcn add` nyalin kode komponen ke `src/components/ui/`. Kodenya punya lu sekarang, boleh dibaca & diubah.

✅ **Cek:** `ls src/components/ui` → ada `alert.tsx badge.tsx button.tsx card.tsx table.tsx`.

---

## Langkah F2: Lapisan API (`src/api/`)

🎯 **Tujuan:** semua urusan ngobrol sama backend dikumpulin di satu folder.

💡 **Konsep:** `types.ts` = **kembaran `custom_types.py`**. TypeScript bakal teriak kalau lu salah nama field. Tapi ini cuma jalan kalau dua file itu tetap **sama**. Ubah salah satu → ubah juga yang lain.

🧩 Bikin `src/api/types.ts`:

```ts
// types.ts: "kembaran" custom_types.py di backend
// kalau bentuk data di backend berubah, ubah juga di sini

export type Cell = string | number | boolean | null

export interface ResultTable {
  id: string
  title: string
  columns: string[]
  rows: Cell[][]
  formulas: string[]
}

export interface CheckItem {
  instruction: string
  done: boolean
  note: string
}

export interface JobResult {
  instructions: { items: string[]; expected_tables: string[] }
  tables: ResultTable[]
  review: { items: CheckItem[] }
}

export interface JobStatus {
  status: 'running' | 'completed' | 'failed'
  result: JobResult | null
  error: string | null
}

export interface CreateJobResponse {
  job_id: string
  event_id: string
}
```

🧩 Bikin `src/api/client.ts`:

```ts
// client.ts: semua panggilan ke backend dikumpulin di sini
import type { CreateJobResponse, JobStatus } from './types'

// alamat backend diambil dari .env frontend (VITE_API_URL), default localhost:8000
export const API_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:8000'

async function handle<T>(res: Response): Promise<T> {
  if (!res.ok) {
    // FastAPI ngirim error dalam bentuk { detail: "..." }
    const body = await res.json().catch(() => null)
    throw new Error(body?.detail ?? `Request gagal (${res.status})`)
  }
  return res.json() as Promise<T>
}

export async function createJob(files: File[]): Promise<CreateJobResponse> {
  const form = new FormData()
  files.forEach((f) => form.append('files', f)) // nama field "files" = parameter di FastAPI
  const res = await fetch(`${API_URL}/api/jobs`, { method: 'POST', body: form })
  return handle<CreateJobResponse>(res)
}

export async function getJobStatus(eventId: string): Promise<JobStatus> {
  const res = await fetch(`${API_URL}/api/jobs/${eventId}`)
  return handle<JobStatus>(res)
}

export function exportUrl(eventId: string): string {
  return `${API_URL}/api/jobs/${eventId}/export`
}
```

🧩 Bikin `src/api/files.ts` (aturan file, sama kayak di backend, biar user dikasih tau lebih awal):

```ts
// files.ts: tebak jenis file dari ekstensinya (sama kayak classify() di backend)
export type FileKind = 'guide' | 'data'

const GUIDE_EXT = ['.pdf', '.png', '.jpg', '.jpeg', '.webp']
const DATA_EXT = ['.xlsx', '.csv']

export function fileKind(name: string): FileKind | null {
  const ext = name.slice(name.lastIndexOf('.')).toLowerCase()
  if (GUIDE_EXT.includes(ext)) return 'guide'
  if (DATA_EXT.includes(ext)) return 'data'
  return null
}

// balikin pesan kalau kombinasi file belum lengkap, null kalau udah oke
export function validateFiles(files: File[]): string | null {
  const guides = files.filter((f) => fileKind(f.name) === 'guide').length
  const datas = files.filter((f) => fileKind(f.name) === 'data').length
  if (guides === 0) return 'Tambahin minimal 1 file guide (PDF/gambar)'
  if (datas !== 1) return 'Butuh tepat 1 file data (.xlsx/.csv)'
  return null
}
```

---

## Langkah F3: Hook `useJob` + `QueryClientProvider`

🎯 **Tujuan:** logika "upload → pantau status sampai selesai" dipisah dari tampilan.

💡 **Konsep:**

```
useMutation  → buat AKSI   (upload file, sekali jalan)
useQuery     → buat DATA   (status job); refetchInterval = tanya ulang tiap 1,5 detik
               berhenti otomatis kalau status completed / failed
```

🧩 Bikin `src/hooks/useJob.ts`:

```ts
// useJob.ts: kirim job + pantau statusnya sampai selesai
import { useMutation, useQuery } from '@tanstack/react-query'
import { createJob, getJobStatus } from '@/api/client'

const POLL_MS = 1500 // cek status tiap 1,5 detik

export function useJob() {
  // useMutation = buat aksi yang "ngubah sesuatu" (upload file)
  const upload = useMutation({ mutationFn: createJob })
  const eventId = upload.data?.event_id

  // useQuery = buat "ngambil data"; refetchInterval bikin dia nanya ulang terus
  const status = useQuery({
    queryKey: ['job', eventId],
    queryFn: () => getJobStatus(eventId!),
    enabled: Boolean(eventId), // baru jalan setelah upload sukses
    refetchInterval: (query) => {
      const s = query.state.data?.status
      return s === 'completed' || s === 'failed' ? false : POLL_MS // berhenti kalau udah selesai
    },
  })

  const isRunning =
    upload.isPending || (Boolean(eventId) && (!status.data || status.data.status === 'running'))

  return {
    start: upload.mutate,
    reset: upload.reset,
    eventId,
    isRunning,
    uploadError: upload.error,
    job: status.data,
    pollError: status.error,
  }
}
```

🧩 Ganti `src/main.tsx`:

```tsx
import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import App from './App.tsx'
import './index.css'

// QueryClient = "otak" TanStack Query: nyimpen cache & ngatur fetch ulang
const queryClient = new QueryClient()

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <QueryClientProvider client={queryClient}>
      <App />
    </QueryClientProvider>
  </StrictMode>,
)
```

---

## Langkah F4: `FileDropzone.tsx`

🎯 **Tujuan:** area drag & drop + daftar file yang udah dipilih, lengkap dengan label `guide` / `data`.

🧩 Bikin `src/components/FileDropzone.tsx`:

```tsx
// FileDropzone.tsx: area drag & drop + daftar file yang udah dipilih
import { FileSpreadsheet, FileText, Upload, X } from 'lucide-react'
import { useDropzone } from 'react-dropzone'
import { fileKind } from '@/api/files'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { cn } from '@/lib/utils'

interface Props {
  files: File[]
  onChange: (files: File[]) => void
  disabled?: boolean
}

export function FileDropzone({ files, onChange, disabled }: Props) {
  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    disabled,
    accept: {
      'application/pdf': ['.pdf'],
      'image/*': ['.png', '.jpg', '.jpeg', '.webp'],
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx'],
      'text/csv': ['.csv'],
    },
    // file baru ditambahin ke daftar (bukan ngeganti)
    onDrop: (accepted) => onChange([...files, ...accepted]),
  })

  const remove = (index: number) => onChange(files.filter((_, i) => i !== index))

  return (
    <div className="space-y-3">
      <div
        {...getRootProps()}
        className={cn(
          'flex cursor-pointer flex-col items-center gap-2 rounded-lg border-2 border-dashed p-8 text-center transition-colors',
          isDragActive ? 'border-primary bg-muted' : 'hover:bg-muted/50',
          disabled && 'cursor-not-allowed opacity-50',
        )}
      >
        <input {...getInputProps()} />
        <Upload className="size-8 text-muted-foreground" />
        <p className="font-medium">
          {isDragActive ? 'Lepas file di sini…' : 'Drag & drop file, atau klik buat pilih'}
        </p>
        <p className="text-sm text-muted-foreground">
          Guide: PDF / gambar · Data: 1 file .xlsx / .csv
        </p>
      </div>

      {files.length > 0 && (
        <ul className="space-y-2">
          {files.map((file, i) => {
            const kind = fileKind(file.name)
            const Icon = kind === 'data' ? FileSpreadsheet : FileText
            return (
              <li key={`${file.name}-${i}`} className="flex items-center gap-3 rounded-md border px-3 py-2">
                <Icon className="size-4 shrink-0 text-muted-foreground" />
                <span className="flex-1 truncate text-sm">{file.name}</span>
                <Badge variant={kind === 'data' ? 'default' : 'secondary'}>{kind ?? '?'}</Badge>
                <Button variant="ghost" size="icon" onClick={() => remove(i)} disabled={disabled}
                        aria-label={`Hapus ${file.name}`}>
                  <X />
                </Button>
              </li>
            )
          })}
        </ul>
      )}
    </div>
  )
}
```

---

## Langkah F5: `ResultTable.tsx`, tabel hasil (TanStack Table v9)

🎯 **Tujuan:** nampilin satu tabel hasil yang bisa di-sort, plus daftar rumus di bawahnya.

💡 **Konsep 1:** data dari backend bentuknya **array per baris** (`[1, 0.3, 1.102, 9.753]`), jadi kolom ke-`i` diambil pakai `row[i]`.

💡 **Konsep 2: TanStack Table v9.** Fitur didaftarin dulu lewat `tableFeatures(...)`. Di sini cuma sorting. `features` dan `helper` ditaruh **di luar komponen** biar gak dibikin ulang tiap render.

> ⚠️ Kalau nemu tutorial pakai `useReactTable` / `getCoreRowModel`, itu API **v8** (lama). Di v9 pakai `useTable` + `tableFeatures`.

🧩 Bikin `src/components/ResultTable.tsx`:

```tsx
// ResultTable.tsx: nampilin SATU tabel hasil, bisa di-sort dengan klik judul kolom
import { useMemo } from 'react'
import {
  createColumnHelper,
  createSortedRowModel,
  rowSortingFeature,
  sortFn_alphanumeric,
  sortFn_basic,
  tableFeatures,
  useTable,
} from '@tanstack/react-table'
import { ArrowUpDown } from 'lucide-react'
import type { Cell, ResultTable as ResultTableData } from '@/api/types'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'

type Row = Cell[]

// fitur tabel yang dipakai: cuma sorting. Ditaruh di luar komponen biar gak dibikin ulang tiap render
const features = tableFeatures({
  rowSortingFeature,
  sortedRowModel: createSortedRowModel(),
  sortFns: { alphanumeric: sortFn_alphanumeric, basic: sortFn_basic },
})
const helper = createColumnHelper<typeof features, Row>()

export function ResultTable({ table }: { table: ResultTableData }) {
  // data dari backend bentuknya array per baris, jadi kolom ke-i diambil pakai row[i]
  const columns = useMemo(
    () =>
      helper.columns(
        table.columns.map((name, i) => helper.accessor((row) => row[i], { id: String(i), header: name })),
      ),
    [table.columns],
  )

  const instance = useTable({ features, columns, data: table.rows })

  return (
    <Card>
      <CardHeader>
        <CardTitle>{table.title}</CardTitle>
        <CardDescription>{table.rows.length} baris</CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <Table>
          <TableHeader>
            {instance.getHeaderGroups().map((group) => (
              <TableRow key={group.id}>
                {group.headers.map((header) => (
                  <TableHead key={header.id}>
                    <button
                      className="inline-flex items-center gap-1 hover:text-foreground"
                      onClick={header.column.getToggleSortingHandler()}
                    >
                      <instance.FlexRender header={header} />
                      <ArrowUpDown className="size-3" />
                    </button>
                  </TableHead>
                ))}
              </TableRow>
            ))}
          </TableHeader>
          <TableBody>
            {instance.getRowModel().rows.map((row) => (
              <TableRow key={row.id}>
                {row.getAllCells().map((cell) => (
                  <TableCell key={cell.id} className="tabular-nums">
                    {String(cell.getValue() ?? '')}
                  </TableCell>
                ))}
              </TableRow>
            ))}
          </TableBody>
        </Table>

        {/* rumus yang dipakai: biar user bisa ngecek LLM gak salah baca guide */}
        <div className="rounded-md bg-muted p-3">
          <p className="mb-1 text-xs font-medium text-muted-foreground">Langkah & rumus</p>
          <ul className="space-y-1 font-mono text-xs">
            {table.formulas.map((f, i) => (
              <li key={i}>{f}</li>
            ))}
          </ul>
        </div>
      </CardContent>
    </Card>
  )
}
```

---

## Langkah F6: `ReviewList.tsx`

🎯 **Tujuan:** nampilin hasil step `review`: tiap instruksi ✅ atau ❌.

🧩 Bikin `src/components/ReviewList.tsx`:

```tsx
// ReviewList.tsx: hasil step "cek ulang", tiap instruksi udah dipenuhi atau belum
import { CircleCheck, CircleX } from 'lucide-react'
import type { CheckItem } from '@/api/types'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'

export function ReviewList({ items }: { items: CheckItem[] }) {
  const done = items.filter((i) => i.done).length
  return (
    <Card>
      <CardHeader>
        <CardTitle>Cek instruksi</CardTitle>
        <CardDescription>
          {done}/{items.length} instruksi terpenuhi
        </CardDescription>
      </CardHeader>
      <CardContent>
        <ul className="space-y-3">
          {items.map((item, i) => (
            <li key={i} className="flex gap-3">
              {item.done ? (
                <CircleCheck className="size-5 shrink-0 text-green-600" />
              ) : (
                <CircleX className="size-5 shrink-0 text-destructive" />
              )}
              <div>
                <p className="text-sm">{item.instruction}</p>
                <p className="text-xs text-muted-foreground">{item.note}</p>
              </div>
            </li>
          ))}
        </ul>
      </CardContent>
    </Card>
  )
}
```

---

## Langkah F7: `App.tsx`, halaman utama

🎯 **Tujuan:** gabungin semuanya: upload → **Enter** → loading → tabel + cek instruksi + download Excel.

💡 **Konsep:** tombol Enter dipasang di `window` lewat `useEffect`, jadi bisa dipencet di mana aja (kecuali lagi ngetik di input).

🧩 Ganti `src/App.tsx`:

```tsx
// App.tsx: halaman utama: upload -> Enter -> tunggu -> tabel hasil
import { useEffect, useState } from 'react'
import { Download, Loader2, RotateCcw } from 'lucide-react'
import { exportUrl } from '@/api/client'
import { validateFiles } from '@/api/files'
import { FileDropzone } from '@/components/FileDropzone'
import { ResultTable } from '@/components/ResultTable'
import { ReviewList } from '@/components/ReviewList'
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { useJob } from '@/hooks/useJob'

export default function App() {
  const [files, setFiles] = useState<File[]>([])
  const { start, reset, eventId, isRunning, uploadError, job, pollError } = useJob()

  const problem = validateFiles(files)
  const canSubmit = !problem && !isRunning
  const submit = () => canSubmit && start(files)

  // pencet Enter di mana aja = proses (kecuali lagi ngetik di input)
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      const typing = e.target instanceof HTMLInputElement || e.target instanceof HTMLTextAreaElement
      if (e.key === 'Enter' && !typing) submit()
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  })

  const startOver = () => {
    setFiles([])
    reset()
  }

  const error = uploadError?.message ?? pollError?.message ?? (job?.status === 'failed' ? job.error : null)
  const result = job?.status === 'completed' ? job.result : null

  return (
    <main className="mx-auto max-w-4xl space-y-6 px-4 py-10">
      <header>
        <h1 className="text-2xl font-bold">Data Process Agent</h1>
        <p className="text-muted-foreground">
          Masukin guide + data mentah, pencet <kbd className="rounded border px-1 text-xs">Enter</kbd>,
          dapat tabel sesuai format guide.
        </p>
      </header>

      <Card>
        <CardHeader>
          <CardTitle>1 · File</CardTitle>
          <CardDescription>{problem ?? 'Siap diproses'}</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <FileDropzone files={files} onChange={setFiles} disabled={isRunning} />
          <div className="flex gap-2">
            <Button onClick={submit} disabled={!canSubmit}>
              {isRunning && <Loader2 className="animate-spin" />}
              {isRunning ? 'Memproses…' : 'Proses (Enter)'}
            </Button>
            {(eventId || files.length > 0) && !isRunning && (
              <Button variant="outline" onClick={startOver}>
                <RotateCcw /> Mulai ulang
              </Button>
            )}
          </div>
        </CardContent>
      </Card>

      {error && (
        <Alert variant="destructive">
          <AlertTitle>Gagal</AlertTitle>
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {result && eventId && (
        <section className="space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-xl font-semibold">2 · Hasil ({result.tables.length} tabel)</h2>
            <Button variant="outline" asChild>
              <a href={exportUrl(eventId)}>
                <Download /> Download Excel
              </a>
            </Button>
          </div>
          {result.tables.map((t) => (
            <ResultTable key={t.id} table={t} />
          ))}
          <ReviewList items={result.review.items} />
        </section>
      )}
    </main>
  )
}
```

✅ **Cek:**

```fish
npm run build      # harus "✓ built", tanpa error TypeScript
npm run lint
```

Warning `only-export-components` dari `badge.tsx` / `button.tsx` itu normal (file bawaan shadcn), boleh dicuekin.

---

## Langkah F8: Jalanin semuanya 🎉

Buka **3 terminal**:

| Terminal | Folder | Perintah |
|---|---|---|
| 1 | `backend/` | `uv run uvicorn data_agent.main:app --reload --port 8000` |
| 2 | `backend/` | `npx --allow-scripts=inngest-cli inngest-cli@latest dev -u http://127.0.0.1:8000/api/inngest --no-discovery` |
| 3 | `frontend/` | `npm run dev` |

✅ **Cek:**
1. Buka http://localhost:5173
2. Drag `backend/samples/bandul/guide.pdf` + `data.xlsx`
3. Pencet **Enter**
4. Tunggu → muncul **2 tabel** + rumus + cek instruksi
5. Klik judul kolom → tabel ke-sort
6. Klik **Download Excel** → dapat file `.xlsx` dengan 2 sheet
7. Buka http://localhost:8288 → lihat run-nya di dashboard Inngest

Commit:

```fish
cd ..; git add frontend; git commit -m "frontend: upload, polling, tabel hasil"
```

**App jadi.** 🚀

---

# G. Maintenance

## G1. Perintah sehari-hari

| Mau ngapain | Perintah (folder) |
|---|---|
| Jalanin app | 3 terminal di [F8](#langkah-f8-jalanin-semuanya-) |
| Jalanin semua test | `uv run pytest` (backend) |
| Rapor kualitas model/prompt | `uv run data-agent-eval` (backend) |
| Proses file dari terminal | `uv run data-agent guide.pdf data.xlsx` (backend) |
| Cek frontend | `npm run build && npm run lint` (frontend) |
| Install ulang semua package | `uv sync` (backend) / `npm ci` (frontend) |

## G2. Aturan emas

1. **Tiap ubah kode backend** → `uv run pytest` harus tetap hijau
2. **Tiap ubah prompt / ganti model** → `uv run data-agent-eval` harus tetap lolos
3. **Tiap ubah `custom_types.py`** → ubah juga `frontend/src/api/types.ts`
4. **Tiap nambah/ubah op** → ubah juga `OPS_REFERENCE` di `prompts.py`
5. **`uv.lock` dan `package-lock.json` selalu di-commit**, `.env` gak pernah

## G3. Ganti model

Cukup edit `backend/.env`, lalu restart uvicorn:

```bash
LLM_MODEL=qwen3-vl:2b-instruct      # 🔄 yang dipakai sekarang (laptop cuma CPU)
# LLM_MODEL=qwen3-vl:4b-instruct    # lebih pinter, ~2x lebih lambat
# LLM_MODEL=glm-5.3-flash:cloud     # Ollama cloud (harus `ollama signin` + credit dulu)
```

Habis ganti, **selalu** jalanin `uv run data-agent-eval` buat bandingin hasilnya.

> Model cloud: guide & data dikirim ke server Ollama (kebanyakan di Amerika). Ollama bilang prompt gak dicatat & gak dipakai training, tapi tetap: data gak cuma di laptop lagi.

## G4. Cara nambah op baru

Contoh: op `percent` (persentase tiap baris terhadap total kolom).

| # | File | Yang ditambah |
|---|---|---|
| 1 | `custom_types.py` | `'percent'` ke `OpName` (+ field baru di `Step` kalau perlu) |
| 2 | `operations.py` | fungsi `op_percent(df, step)` |
| 3 | `operations.py` | daftarin di `OPERATIONS` |
| 4 | `operations.py` | case baru di `describe_step` |
| 5 | `prompts.py` | baris baru di `OPS_REFERENCE` |
| 6 | `tests/test_operations.py` | test buat op baru |

```python
def op_percent(df: pd.DataFrame, step: Step) -> pd.DataFrame:
    # kolom baru = nilai / total kolom * 100
    _need(step, 'new_column', 'columns')
    _check_columns(df, step.columns)
    col = step.columns[0]
    df = df.copy()
    df[step.new_column] = df[col] / df[col].sum() * 100
    return df
```

## G5. Cara nambah sample baru

```
samples/
└─ nama_sample/
   ├─ guide.pdf        (atau .png/.jpg)
   ├─ data.xlsx        (atau .csv)
   └─ expected.json    {"tables": [{"title": "...", "columns": [...], "rows": [[...]]}]}
```

`expected.json` dihitung **manual** (Excel / kalkulator / script sendiri), jangan pakai output app, nanti salahnya ikut kesimpen. Makin banyak sample yang beda-beda (filter, group, regresi, foto guide), makin ketahuan kelemahan model/prompt.

## G6. Update dependency

```fish
# backend
uv lock --upgrade          # naikin semua versi di uv.lock
uv sync
uv run pytest && uv run data-agent-eval

# frontend
npm outdated               # lihat yang bisa di-update
npm update
npm run build
```

Update **satu per satu** untuk versi mayor (misal pandas 3 → 4), terus jalanin test tiap kali. Kalau rusak, `git checkout uv.lock` buat balik.

## G7. Baca log & pantau token

Tiap panggilan LLM nyatat satu baris log:

```
INFO data_agent.llm: [plan#1] model=qwen3-vl:8b input=2150 output=430 waktu=14.2s speed=30.3 tok/s
```

- `plan#2`, `plan#3` muncul = rencana pertama gagal dan dibenerin. Kalau sering, berarti prompt atau model perlu diperbaiki
- `input` mendekati `LLM_NUM_CTX` = guide kepanjangan, sebagian bisa kepotong. Naikin `LLM_NUM_CTX` atau pecah guide-nya
- error lengkap tiap step kelihatan di dashboard Inngest (http://localhost:8288)

## G8. README.md buat repo

Bikin `DATA-PROCESSOR/README.md`:

````markdown
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
````

---

# 🆘 Troubleshooting

| Gejala | Penyebab | Solusi |
|---|---|---|
| `KeyError: 'LLM_MODEL'` | `.env` gak ketemu | jalanin perintah dari folder `backend/`, cek isi `.env` |
| `ConnectionError: Failed to connect to Ollama` | server Ollama mati | `sudo systemctl start ollama` |
| `Server disconnected without sending a response` | 🔄 Ollama dibunuh kernel karena RAM habis (cek: `journalctl -u ollama` → `oom-kill`) | pakai model lebih kecil, atau turunin `LLM_NUM_CTX` (misal 8192) |
| `model "qwen3-vl:8b" not found` | belum di-download | `ollama pull <nama model>` |
| `ModuleNotFoundError` | package belum ke-install | `uv sync` |
| model lambat banget | jalan di CPU / mode mikir | cek `ollama ps`; isi `LLM_THINK=false`; pakai versi `-instruct` yang lebih kecil; atau Ollama cloud |
| `out of memory` / CUDA error | konteks kegedean | `LLM_NUM_CTX=8192` di `.env` |
| warning "output gak sesuai schema" terus | model kesulitan ngikutin JSON | cek Langkah 5; coba model lain; sederhanain guide |
| `rencana tetap gagal setelah 3 percobaan` | LLM gak nemu kolom/rumus yang bener | lihat pesan error di log; cek nama kolom di Excel; tambah contoh di `OPS_REFERENCE` |
| angka hasil beda dari harapan | LLM salah baca rumus | lihat "Langkah & rumus" di UI; guide yang rumusnya teks biasa (bukan gambar) lebih aman |
| frontend: `Failed to fetch` | backend mati / CORS | cek terminal 1; `FRONTEND_ORIGIN` di `backend/.env` harus `http://localhost:5173` |
| status `running` terus | Inngest dev server mati / gak nyambung | cek terminal 2; buka http://localhost:8288 → Apps → harus ada `data-process-agent` |
| `Inngest CLI binary not found` | 🔄 npm 12 nge-skip install script | pakai `npx --allow-scripts=inngest-cli ...`. Kalau masih error: hapus folder di `~/.npm/_npx/` yang isinya `node_modules/inngest-cli`, terus jalanin lagi |
| `shadcn init` nanya preset terus | 🔄 shadcn 4 | pakai `npx shadcn@latest init -t vite -b radix -p nova` |
| `Cannot find module '@/...'` | alias belum diatur | cek `vite.config.ts` + `tsconfig.json` + `tsconfig.app.json` (Langkah F1) |
| `useReactTable is not exported` | pakai contoh TanStack Table v8 | pakai API v9 (`useTable`, `tableFeatures`), lihat F5 |

---

# H. Pengembangan berikutnya

Kerjain **setelah** app di atas jalan stabil dan `data-agent-eval` lolos.

## H1. Konfirmasi rencana sebelum ngitung

Inngest bisa **pause** di tengah proses dan nunggu event dari user (`ctx.step.wait_for_event`). Alurnya:

```
make_plan → [tampilin rencana di UI, user klik "Setuju"] → run_plan → review
```

Cocok buat data eksperimen penting: user ngecek rumus dulu sebelum hasilnya dipakai.

## H2. Perpustakaan template (Qdrant)

Simpan guide yang pernah diproses + rencananya yang **udah terbukti benar**. Waktu ada guide baru, cari guide lama yang mirip, terus kasih rencananya ke LLM sebagai contoh.

```
guide baru → embedding (qwen3-embedding:0.6b, dim 1024) → cari di Qdrant → 2 rencana lama paling mirip
          → dimasukin ke prompt make_plan sebagai contoh → rencana baru lebih akurat
```

Yang ditambah: `ollama pull qwen3-embedding:0.6b`, `uv add qdrant-client`, Qdrant via Docker, file `vector_db.py` (bisa contek `QdrantStorage` dari RAG-PDF, ganti `dim=1024`), dan fungsi `embed()` di `llm.py`.

## H3. Riwayat job

Sekarang hasil job cuma ada di Inngest dev server (hilang kalau dev server di-restart). Langkah berikutnya: simpan `JobResult` ke database kecil (SQLite) atau file JSON di `uploads/<job_id>/result.json`, plus halaman "riwayat" di frontend.

## H4. Deploy

- Inngest: ganti dev server ke Inngest Cloud (butuh `INNGEST_EVENT_KEY` + `INNGEST_SIGNING_KEY`, dan `is_production=True`)
- `jobs.py`: ganti cara cek status (REST API dev server beda dengan versi cloud)
- Frontend: `npm run build` → folder `dist/` bisa di-host di mana aja; set `VITE_API_URL` ke alamat backend
- Model: server dengan GPU, atau pindah ke Ollama cloud lewat `.env`
