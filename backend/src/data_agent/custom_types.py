# custom_types.py: "bentuk" data yang lewat antar step
# Pydantic ngecek bentuknya otomatis, jadi data yang salah langsung ketahuan
from typing import Any, Literal

from pydantic import BaseModel


# ---------- 1. input yang udah dibaca ----------
class SheetSummary(BaseModel):
    name: str                      # nama sheet di Excel
    columns: list[str]             # nama kolom (udah dirapihin, lihat doc_loader)
    dtypes: dict[str, str]         # tipe data tiap kolom
    n_rows: int
    sample_rows: list[dict[str, Any]]  # beberapa baris contoh buat LLM


class InputBundle(BaseModel):
    guide_text: str                # teks dari guide (PDF)
    guide_images: list[str]        # path gambar (foto guide / halaman PDF scan)
    data_path: str                 # path file Excel/CSV
    sheets: list[SheetSummary]


# ---------- 2. hasil LLM: daftar instruksi ----------
class Instructions(BaseModel):
    items: list[str]               # tiap instruksi di guide, satu per item
    expected_tables: list[str]     # tabel apa aja yang diminta guide


# ---------- 3. hasil LLM: rencana proses ----------
OpName = Literal[
    'compute', 'filter', 'select', 'rename', 'sort',
    'round', 'group_agg', 'aggregate', 'linear_fit',
]
AggFunc = Literal['mean', 'sum', 'min', 'max', 'count', 'std', 'median']


class Aggregation(BaseModel):
    column: str                    # kolom yang dihitung
    func: AggFunc                  # fungsi: mean, sum, ...
    output: str                    # nama kolom hasilnya


class RenamePair(BaseModel):
    old: str
    new: str


class Step(BaseModel):
    # satu model buat semua op (bukan satu model per op),
    # biar schema-nya simpel dan gampang diikutin model lokal yang kecil.
    # parameter yang wajib per op dicek di operations.py
    op: OpName
    new_column: str | None = None          # compute
    expr: str | None = None                # compute (rumus) / filter (kondisi)
    columns: list[str] | None = None       # select / round
    renames: list[RenamePair] | None = None  # rename
    by: list[str] | None = None            # sort / group_agg
    descending: bool | None = None         # sort
    decimals: int | None = None            # round
    aggregations: list[Aggregation] | None = None  # group_agg / aggregate
    x: str | None = None                   # linear_fit
    y: str | None = None                   # linear_fit


class TablePlan(BaseModel):
    id: str                        # id unik, contoh: "hasil_g"
    title: str                     # judul yang ditampilin
    source: str                    # nama sheet ATAU id tabel sebelumnya
    steps: list[Step]


class Plan(BaseModel):
    tables: list[TablePlan]


# ---------- 4. hasil akhir ----------
class ResultTable(BaseModel):
    id: str
    title: str
    columns: list[str]
    rows: list[list[Any]]
    formulas: list[str]            # langkah/rumus yang dipakai, buat ditampilin di UI


class TableSet(BaseModel):
    tables: list[ResultTable]


class CheckItem(BaseModel):
    instruction: str
    done: bool
    note: str


class Review(BaseModel):
    items: list[CheckItem]


class JobResult(BaseModel):
    instructions: Instructions
    plan: Plan
    tables: list[ResultTable]
    review: Review
