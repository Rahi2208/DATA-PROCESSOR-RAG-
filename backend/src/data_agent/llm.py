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
