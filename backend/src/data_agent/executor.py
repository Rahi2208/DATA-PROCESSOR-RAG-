# executor.py: jalanin rencana (Plan) langkah demi langkah pakai pandas
import json

import pandas as pd

from data_agent.custom_types import Plan, ResultTable
from data_agent.operations import PlanError, apply_step, describe_step


def to_result_table(table_id: str, title: str, df: pd.DataFrame, formulas: list[str]) -> ResultTable:
    # to_json -> json.loads: ubah NaN jadi null dan tipe numpy jadi angka biasa
    data = json.loads(df.to_json(orient='split', index=False))
    return ResultTable(id=table_id, title=title, columns=data['columns'],
                       rows=data['data'], formulas=formulas)


def run_plan(plan: Plan, sheets: dict[str, pd.DataFrame]) -> list[ResultTable]:
    frames = dict(sheets)  # sumber data: sheet Excel + tabel yang udah jadi
    results: list[ResultTable] = []

    for table in plan.tables:
        if table.source not in frames:
            raise PlanError(
                f"tabel '{table.id}': source '{table.source}' gak ada. "
                f'Yang ada: {list(frames)}'
            )
        df = frames[table.source]
        for i, step in enumerate(table.steps, start=1):
            try:
                df = apply_step(df, step)
            except PlanError as e:
                raise PlanError(f"tabel '{table.id}', step {i}: {e}") from e

        frames[table.id] = df  # tabel ini bisa jadi source tabel berikutnya
        formulas = [describe_step(s) for s in table.steps]
        results.append(to_result_table(table.id, table.title, df, formulas))

    return results
