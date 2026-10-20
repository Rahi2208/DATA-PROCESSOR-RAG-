# conftest.py: disiapin pytest sebelum semua test jalan
import os
import subprocess
import sys
from pathlib import Path

import pytest

# test gak butuh .env asli; config.py cuma butuh LLM_MODEL ada isinya
os.environ.setdefault('LLM_MODEL', 'test-model')

from data_agent.custom_types import Aggregation, Plan, RenamePair, Step, TablePlan  # noqa: E402

BACKEND = Path(__file__).parent.parent
SAMPLE = BACKEND / 'samples' / 'bandul'


@pytest.fixture(scope='session')
def bandul_dir() -> Path:
    # bikin file sample kalau belum ada
    if not (SAMPLE / 'expected.json').exists():
        subprocess.run([sys.executable, str(SAMPLE.parent / 'make_bandul.py')], check=True)
    return SAMPLE


@pytest.fixture
def bandul_plan() -> Plan:
    # rencana yang BENAR untuk sample bandul (contoh jawaban ideal dari LLM)
    return Plan(tables=[
        TablePlan(id='hasil', title='Hasil Perhitungan', source='data', steps=[
            Step(op='compute', new_column='t_periode', expr='waktu_10_ayunan_s / 10'),
            Step(op='compute', new_column='g', expr='4 * pi ** 2 * panjang_tali_m / t_periode ** 2'),
            Step(op='round', columns=['t_periode', 'g'], decimals=3),
            Step(op='rename', renames=[
                RenamePair(old='percobaan', new='Percobaan'),
                RenamePair(old='panjang_tali_m', new='L (m)'),
                RenamePair(old='t_periode', new='T (s)'),
                RenamePair(old='g', new='g (m/s2)'),
            ]),
            Step(op='select', columns=['Percobaan', 'L (m)', 'T (s)', 'g (m/s2)']),
        ]),
        TablePlan(id='ringkasan', title='Ringkasan', source='hasil', steps=[
            Step(op='aggregate', aggregations=[
                Aggregation(column='g (m/s2)', func='mean', output='g_rata_rata'),
            ]),
            Step(op='round', columns=['g_rata_rata'], decimals=3),
            Step(op='compute', new_column='error', expr='abs(g_rata_rata - 9.8) / 9.8 * 100'),
            Step(op='round', columns=['error'], decimals=2),
            Step(op='rename', renames=[
                RenamePair(old='g_rata_rata', new='g rata-rata'),
                RenamePair(old='error', new='error (%)'),
            ]),
        ]),
    ])
