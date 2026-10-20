import pandas as pd
import pymupdf
import pytest

from data_agent.doc_loader import classify, load_inputs, normalize_column, read_data


@pytest.mark.parametrize('raw, clean', [
    ('Panjang Tali (m)', 'panjang_tali_m'),
    ('  Waktu 10 Ayunan (s) ', 'waktu_10_ayunan_s'),
    ('10 cm', 'c_10_cm'),
    ('%%%', 'kolom'),
])
def test_normalize_column(raw, clean):
    assert normalize_column(raw) == clean


def test_classify():
    assert classify('panduan.PDF') == 'guide'
    assert classify('foto.jpg') == 'guide'
    assert classify('data.xlsx') == 'data'
    assert classify('virus.exe') is None


def test_read_data_nama_kolom_kembar(tmp_path):
    path = tmp_path / 'd.csv'
    pd.DataFrame([[1, 2]], columns=['Nilai', 'nilai ']).to_csv(path, index=False)
    sheets = read_data(str(path))
    assert list(sheets['data'].columns) == ['nilai', 'nilai_2']


def test_load_inputs_pdf_scan_dirender(tmp_path):
    # halaman 1 ada teks, halaman 2 kosong (kayak hasil scan) -> halaman 2 jadi gambar
    pdf = tmp_path / 'guide.pdf'
    doc = pymupdf.open()
    doc.new_page().insert_text((50, 72), 'Hitung rata-rata kolom nilai. ' * 5)
    doc.new_page()
    doc.save(pdf)
    data = tmp_path / 'data.csv'
    pd.DataFrame({'Nilai': [1, 2, 3]}).to_csv(data, index=False)

    bundle = load_inputs([str(pdf)], str(data), str(tmp_path / 'job'))

    assert 'rata-rata' in bundle.guide_text
    assert len(bundle.guide_images) == 1 and bundle.guide_images[0].endswith('page2.png')
    assert bundle.sheets[0].columns == ['nilai'] and bundle.sheets[0].n_rows == 3
