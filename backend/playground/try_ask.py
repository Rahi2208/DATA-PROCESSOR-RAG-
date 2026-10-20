# try_ask.py: tes pertama ngobrol sama model (bukan bagian app, cuma buat nyoba)
# jalanin: uv run python playground/try_ask.py
import logging

from data_agent import config, llm

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(name)s: %(message)s')
logging.getLogger('httpx').setLevel(logging.WARNING)

print('host :', config.OLLAMA_HOST)
print('model:', config.LLM_MODEL)
print(llm.ask('Sebutkan rumus periode bandul sederhana dalam satu baris'))
