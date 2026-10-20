# make_bandul.py: bikin sample pertama (praktikum bandul) buat tes & evaluasi
# jalanin dari folder backend: uv run python samples/make_bandul.py
import json
import math
from pathlib import Path

import pandas as pd
import pymupdf

OUT = Path(__file__).parent / 'bandul'
OUT.mkdir(exist_ok=True)

# ---------- 1. data mentah (Excel) ----------
data = pd.DataFrame({
    'Percobaan': [1, 2, 3, 4, 5],
    'Panjang Tali (m)': [0.3, 0.5, 0.7, 0.9, 1.1],
    'Waktu 10 Ayunan (s)': [11.02, 14.15, 16.83, 19.01, 21.10],
})
data.to_excel(OUT / 'data.xlsx', sheet_name='Data', index=False)

# ---------- 2. guide (PDF) ----------
GUIDE = """PANDUAN PENGOLAHAN DATA - PRAKTIKUM BANDUL SEDERHANA

Data mentah ada di file Excel (sheet Data).

Langkah pengolahan:
1. Hitung periode satu ayunan: T = t / 10, dengan t = waktu 10 ayunan.
2. Hitung percepatan gravitasi: g = 4 x pi^2 x L / T^2, dengan L = panjang tali.
3. Bulatkan T dan g ke 3 angka di belakang koma.

Tabel 1 - Hasil Perhitungan, dengan kolom berurutan:
| Percobaan | L (m) | T (s) | g (m/s2) |

Tabel 2 - Ringkasan, berisi:
- g rata-rata (dibulatkan 3 desimal)
- persen error terhadap g literatur 9.8 m/s2:
  error = |g rata-rata - 9.8| / 9.8 x 100 (dibulatkan 2 desimal)
"""
doc = pymupdf.open()
page = doc.new_page()
page.insert_textbox(pymupdf.Rect(50, 50, 550, 800), GUIDE, fontsize=11)
doc.save(OUT / 'guide.pdf')

# ---------- 3. jawaban yang benar (dihitung manual, BUKAN pakai app) ----------
rows = []
for p, L, t in data.itertuples(index=False):
    T = round(t / 10, 3)
    g = round(4 * math.pi ** 2 * L / (t / 10) ** 2, 3)
    rows.append([p, L, T, g])
g_mean = round(sum(r[3] for r in rows) / len(rows), 3)
error = round(abs(g_mean - 9.8) / 9.8 * 100, 2)

expected = {'tables': [
    {'title': 'Hasil Perhitungan', 'columns': ['Percobaan', 'L (m)', 'T (s)', 'g (m/s2)'], 'rows': rows},
    {'title': 'Ringkasan', 'columns': ['g rata-rata', 'error (%)'], 'rows': [[g_mean, error]]},
]}
(OUT / 'expected.json').write_text(json.dumps(expected, indent=2))
print('sample dibuat di', OUT)
