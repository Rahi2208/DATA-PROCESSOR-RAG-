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
