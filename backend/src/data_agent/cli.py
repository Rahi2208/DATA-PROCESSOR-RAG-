# cli.py: CLI buat jalanin pipeline langsung dari terminal (tanpa server)
# contoh: uv run data-agent samples/bandul/guide.pdf samples/bandul/data.xlsx
import argparse
import json
import logging
import tempfile


def main() -> None:
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(name)s: %(message)s')
    logging.getLogger('httpx').setLevel(logging.WARNING)

    parser = argparse.ArgumentParser(description='Proses data mentah sesuai guide')
    parser.add_argument('files', nargs='+', help='file guide (PDF/gambar) + 1 file data (.xlsx/.csv)')
    parser.add_argument('--json', action='store_true', help='print hasil lengkap sebagai JSON')
    args = parser.parse_args()

    # import di sini biar `--help` tetap jalan walau .env belum ada
    from data_agent.doc_loader import classify
    from data_agent.pipeline import run_all

    guides = [f for f in args.files if classify(f) == 'guide']
    datas = [f for f in args.files if classify(f) == 'data']
    if not guides or len(datas) != 1:
        parser.error('butuh minimal 1 guide dan tepat 1 file data')

    with tempfile.TemporaryDirectory() as work_dir:
        result = run_all(guides, datas[0], work_dir)

    if args.json:
        print(json.dumps(result.model_dump(mode='json'), ensure_ascii=False, indent=2))
        return

    for table in result.tables:
        print(f'\n=== {table.title} ===')
        print(' | '.join(table.columns))
        for row in table.rows:
            print(' | '.join(str(v) for v in row))
        print('rumus:', '; '.join(table.formulas))
    print('\n=== cek instruksi ===')
    for item in result.review.items:
        print('✅' if item.done else '❌', item.instruction, '-', item.note)
