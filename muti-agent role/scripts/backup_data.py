#!/usr/bin/env python3
"""Create a consistent SQLite + referenced uploads archive without API secrets."""
import argparse
import json
import os
import sqlite3
import tarfile
import tempfile
from datetime import datetime, timezone
from pathlib import Path


def backup(data_dir: Path, output: Path) -> None:
    database = data_dir / 'research.sqlite3'
    uploads = data_dir / 'uploads'
    if not database.is_file():
        raise SystemExit('数据库不存在，未创建备份')
    output.parent.mkdir(parents=True, exist_ok=True)
    if output.exists():
        raise SystemExit('目标备份已存在，未覆盖')
    with tempfile.TemporaryDirectory(prefix='study-backup-', dir=output.parent) as work:
        copy = Path(work) / 'research.sqlite3'
        source_db = sqlite3.connect(f'file:{database}?mode=ro', uri=True)
        target_db = sqlite3.connect(copy)
        try:
            source_db.backup(target_db)
            result = target_db.execute('PRAGMA integrity_check').fetchone()[0]
            if result != 'ok':
                raise SystemExit(f'数据库完整性检查未通过：{result}')
            paths = [row[0] for row in target_db.execute('SELECT stored_path FROM files ORDER BY stored_path')]
        finally:
            target_db.close()
            source_db.close()

        checked = []
        for relative in paths:
            path = (uploads / relative).resolve()
            if not path.is_relative_to(uploads.resolve()) or not path.is_file():
                raise SystemExit(f'数据库引用的上传文件缺失或路径无效：{relative}')
            checked.append((relative, path))
        manifest = {'created_at_utc': datetime.now(timezone.utc).isoformat(timespec='seconds'),
                    'file_count': len(checked), 'database': 'research.sqlite3'}
        fd, temp_name = tempfile.mkstemp(prefix='.backup-', suffix='.tar.gz', dir=output.parent)
        os.close(fd)
        try:
            with tarfile.open(temp_name, 'w:gz') as archive:
                archive.add(copy, arcname='research.sqlite3')
                for relative, path in checked:
                    archive.add(path, arcname='uploads/' + relative)
                payload = json.dumps(manifest, ensure_ascii=False).encode()
                info = tarfile.TarInfo('manifest.json')
                info.size = len(payload)
                import io
                archive.addfile(info, io.BytesIO(payload))
            os.chmod(temp_name, 0o600)
            os.replace(temp_name, output)
        finally:
            if os.path.exists(temp_name):
                os.unlink(temp_name)
    print(f'备份已创建：{output}（{len(checked)} 个上传文件）')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--data-dir', type=Path, default=Path(os.environ.get('DATA_DIR', Path(__file__).resolve().parents[1] / 'data')))
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    backup(args.data_dir.resolve(), args.output.resolve())
