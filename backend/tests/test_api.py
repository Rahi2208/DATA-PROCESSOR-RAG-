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
