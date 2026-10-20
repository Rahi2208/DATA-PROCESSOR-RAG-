import pandas as pd
import pytest

from data_agent.custom_types import Aggregation, Step
from data_agent.operations import PlanError, apply_step, validate_expr

COLS = ['a', 'b']


def df() -> pd.DataFrame:
    return pd.DataFrame({'a': [1.0, 4.0, 9.0], 'b': [2, 2, 3], 'grup': ['x', 'y', 'x']})


# ---------- validasi rumus ----------
def test_rumus_valid_lolos():
    validate_expr('sqrt(a) * pi + b ** 2', COLS)


@pytest.mark.parametrize('expr', [
    "__import__('os').system('ls')",  # nyoba jalanin perintah sistem
    'a.__class__',                     # akses atribut
    'c + 1',                           # kolom gak ada
    'a ^ 2',                           # ^ bukan pangkat di Python
    'max(a)',                          # fungsi gak diizinkan
])
def test_rumus_berbahaya_atau_salah_ditolak(expr):
    with pytest.raises(PlanError):
        validate_expr(expr, COLS)


# ---------- tiap op ----------
def test_compute():
    out = apply_step(df(), Step(op='compute', new_column='c', expr='a / b'))
    assert out['c'].tolist() == [0.5, 2.0, 3.0]


def test_filter():
    out = apply_step(df(), Step(op='filter', expr="a > 2 and grup == 'x'"))
    assert out['a'].tolist() == [9.0]


def test_round_semua_kolom_angka():
    data = pd.DataFrame({'x': [1.23456], 'y': [2.98765], 'nama': ['a']})
    out = apply_step(data, Step(op='round', decimals=2))
    assert out.iloc[0].tolist() == [1.23, 2.99, 'a']


def test_group_agg():
    step = Step(op='group_agg', by=['grup'],
                aggregations=[Aggregation(column='a', func='sum', output='total')])
    out = apply_step(df(), step)
    assert dict(zip(out['grup'], out['total'])) == {'x': 10.0, 'y': 4.0}


def test_aggregate_jadi_satu_baris():
    step = Step(op='aggregate', aggregations=[Aggregation(column='a', func='mean', output='rata')])
    out = apply_step(df(), step)
    assert out.shape == (1, 1) and out['rata'][0] == pytest.approx(14 / 3)


def test_linear_fit():
    data = pd.DataFrame({'x': [1, 2, 3], 'y': [3, 5, 7]})  # y = 2x + 1
    out = apply_step(data, Step(op='linear_fit', x='x', y='y'))
    assert out['slope'][0] == pytest.approx(2)
    assert out['intercept'][0] == pytest.approx(1)
    assert out['r2'][0] == pytest.approx(1)


def test_parameter_wajib_kosong():
    with pytest.raises(PlanError, match="butuh parameter 'expr'"):
        apply_step(df(), Step(op='compute', new_column='c'))


def test_kolom_gak_ada():
    with pytest.raises(PlanError, match='gak ada'):
        apply_step(df(), Step(op='select', columns=['zzz']))
