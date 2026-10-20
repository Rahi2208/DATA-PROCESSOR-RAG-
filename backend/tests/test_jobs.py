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
