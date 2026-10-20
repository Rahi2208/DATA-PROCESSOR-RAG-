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
