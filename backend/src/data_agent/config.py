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
