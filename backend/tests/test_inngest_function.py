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
