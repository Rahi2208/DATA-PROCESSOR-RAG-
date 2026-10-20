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
