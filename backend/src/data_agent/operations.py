# operations.py: "kamus" operasi pandas yang boleh dipakai rencana
# LLM cuma milih op + parameter; yang ngitung tetap kode kita (hasilnya pasti)
import ast
import math

import numpy as np
import pandas as pd

from data_agent.custom_types import Step


class PlanError(Exception):
    # error karena rencana salah (kolom gak ada, rumus aneh, dll)
    # pesannya dikirim balik ke LLM biar dia bisa benerin
    pass


CONSTANTS = {'pi': math.pi, 'e': math.e}
ALLOWED_FUNCS = {'sqrt', 'abs', 'log', 'log10', 'exp', 'sin', 'cos', 'tan'}

# jenis "potongan" rumus yang diizinkan. Selain ini (akses atribut, import, lambda, dll) ditolak
_ALLOWED_NODES = (
    ast.Expression, ast.BinOp, ast.UnaryOp, ast.BoolOp, ast.Compare,
    ast.Name, ast.Load, ast.Constant, ast.Call,
    ast.Add, ast.Sub, ast.Mult, ast.Div, ast.Pow, ast.Mod, ast.FloorDiv,
    ast.USub, ast.UAdd, ast.Not, ast.And, ast.Or, ast.BitAnd, ast.BitOr,
    ast.Eq, ast.NotEq, ast.Lt, ast.LtE, ast.Gt, ast.GtE,
)


def validate_expr(expr: str, columns: list[str]) -> None:
    # cek rumus SEBELUM dijalanin: cuma boleh angka, nama kolom, konstanta, fungsi matematika
    if '^' in expr:
        raise PlanError(f"rumus '{expr}' pakai '^'. Untuk pangkat pakai '**'")
    try:
        tree = ast.parse(expr, mode='eval')
    except SyntaxError as e:
        raise PlanError(f"rumus '{expr}' gak valid: {e.msg}") from e

    for node in ast.walk(tree):
        if not isinstance(node, _ALLOWED_NODES):
            raise PlanError(f"rumus '{expr}' pakai sintaks yang gak diizinkan: {type(node).__name__}")
        if isinstance(node, ast.Call):
            if not isinstance(node.func, ast.Name) or node.func.id not in ALLOWED_FUNCS:
                raise PlanError(f"rumus '{expr}': fungsi yang boleh cuma {sorted(ALLOWED_FUNCS)}")
            if node.keywords:
                raise PlanError(f"rumus '{expr}': fungsi gak boleh pakai argumen bernama")
        if isinstance(node, ast.Name):
            allowed = set(columns) | set(CONSTANTS) | ALLOWED_FUNCS
            if node.id not in allowed:
                raise PlanError(f"rumus '{expr}': '{node.id}' bukan kolom. Kolom yang ada: {columns}")


def _need(step: Step, *names: str) -> None:
    # pastiin parameter wajib buat op ini diisi
    for name in names:
        if getattr(step, name) in (None, [], ''):
            raise PlanError(f"op '{step.op}' butuh parameter '{name}'")


def _check_columns(df: pd.DataFrame, cols: list[str]) -> None:
    missing = [c for c in cols if c not in df.columns]
    if missing:
        raise PlanError(f'kolom {missing} gak ada. Kolom yang ada: {list(df.columns)}')


# ---------- satu fungsi per op ----------

def op_compute(df: pd.DataFrame, step: Step) -> pd.DataFrame:
    # bikin kolom baru dari rumus, contoh: T = waktu_10_ayunan / 10
    _need(step, 'new_column', 'expr')
    validate_expr(step.expr, list(df.columns))
    df = df.copy()
    df[step.new_column] = df.eval(step.expr, resolvers=[CONSTANTS])
    return df


def op_filter(df: pd.DataFrame, step: Step) -> pd.DataFrame:
    # saring baris, contoh: percobaan > 1 and panjang_tali <= 1
    _need(step, 'expr')
    validate_expr(step.expr, list(df.columns))
    return df.query(step.expr, resolvers=[CONSTANTS])


def op_select(df: pd.DataFrame, step: Step) -> pd.DataFrame:
    # pilih + urutin kolom (dipakai buat nyamain format template)
    _need(step, 'columns')
    _check_columns(df, step.columns)
    return df[step.columns]


def op_rename(df: pd.DataFrame, step: Step) -> pd.DataFrame:
    _need(step, 'renames')
    mapping = {r.old: r.new for r in step.renames}
    _check_columns(df, list(mapping))
    return df.rename(columns=mapping)


def op_sort(df: pd.DataFrame, step: Step) -> pd.DataFrame:
    _need(step, 'by')
    _check_columns(df, step.by)
    return df.sort_values(step.by, ascending=not step.descending)


def op_round(df: pd.DataFrame, step: Step) -> pd.DataFrame:
    # kalau columns kosong: bulatin semua kolom angka
    _need(step, 'decimals')
    cols = step.columns or list(df.select_dtypes('number').columns)
    _check_columns(df, cols)
    df = df.copy()
    df[cols] = df[cols].round(step.decimals)
    return df


def op_group_agg(df: pd.DataFrame, step: Step) -> pd.DataFrame:
    # rata-rata/jumlah per kelompok, contoh: rata-rata g per panjang_tali
    _need(step, 'by', 'aggregations')
    _check_columns(df, step.by + [a.column for a in step.aggregations])
    named = {a.output: (a.column, a.func) for a in step.aggregations}
    return df.groupby(step.by, as_index=False).agg(**named)


def op_aggregate(df: pd.DataFrame, step: Step) -> pd.DataFrame:
    # ringkasan satu baris untuk seluruh data, contoh: rata-rata g
    _need(step, 'aggregations')
    _check_columns(df, [a.column for a in step.aggregations])
    row = {a.output: df[a.column].agg(a.func) for a in step.aggregations}
    return pd.DataFrame([row])


def op_linear_fit(df: pd.DataFrame, step: Step) -> pd.DataFrame:
    # regresi linear y = slope * x + intercept, plus R²
    _need(step, 'x', 'y')
    _check_columns(df, [step.x, step.y])
    x = df[step.x].astype(float).to_numpy()
    y = df[step.y].astype(float).to_numpy()
    if len(x) < 2:
        raise PlanError('linear_fit butuh minimal 2 baris data')
    slope, intercept = np.polyfit(x, y, 1)
    y_pred = slope * x + intercept
    ss_res = float(((y - y_pred) ** 2).sum())
    ss_tot = float(((y - y.mean()) ** 2).sum())
    r2 = 1 - ss_res / ss_tot if ss_tot else 1.0
    return pd.DataFrame([{'slope': slope, 'intercept': intercept, 'r2': r2}])


OPERATIONS = {
    'compute': op_compute,
    'filter': op_filter,
    'select': op_select,
    'rename': op_rename,
    'sort': op_sort,
    'round': op_round,
    'group_agg': op_group_agg,
    'aggregate': op_aggregate,
    'linear_fit': op_linear_fit,
}


def apply_step(df: pd.DataFrame, step: Step) -> pd.DataFrame:
    try:
        return OPERATIONS[step.op](df, step)
    except PlanError:
        raise
    except Exception as e:  # error pandas lain juga diubah jadi PlanError biar bisa dibenerin LLM
        raise PlanError(f"op '{step.op}' gagal: {type(e).__name__}: {e}") from e


def describe_step(step: Step) -> str:
    # versi "manusia" dari tiap step, ditampilin di bawah tabel
    match step.op:
        case 'compute':
            return f'{step.new_column} = {step.expr}'
        case 'filter':
            return f'filter: {step.expr}'
        case 'select':
            return f"kolom: {', '.join(step.columns or [])}"
        case 'rename':
            return 'ganti nama: ' + ', '.join(f'{r.old} → {r.new}' for r in step.renames or [])
        case 'sort':
            arah = 'besar → kecil' if step.descending else 'kecil → besar'
            return f"urutkan {', '.join(step.by or [])} ({arah})"
        case 'round':
            cols = ', '.join(step.columns) if step.columns else 'semua angka'
            return f'bulatkan {cols} ke {step.decimals} desimal'
        case 'group_agg' | 'aggregate':
            aggs = ', '.join(f'{a.output} = {a.func}({a.column})' for a in step.aggregations or [])
            per = f" per {', '.join(step.by)}" if step.op == 'group_agg' and step.by else ''
            return f'{aggs}{per}'
        case 'linear_fit':
            return f'regresi linear: {step.y} = slope × {step.x} + intercept'
    return step.op
