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
