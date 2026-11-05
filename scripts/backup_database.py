"""Consistent SQLite backup and restore-to-new-file, never overwrite a live DB."""
import argparse
import hashlib
import json
import sqlite3
from contextlib import closing
from pathlib import Path


def snapshot(source, destination, restore=False):
    source=Path(source).resolve(); destination=Path(destination).resolve()
    if not source.is_file(): raise ValueError('来源数据库不存在')
    if source==destination: raise ValueError('来源和目标不能相同')
    destination.parent.mkdir(parents=True,exist_ok=True)
    # Reserve exclusively, refusing accidental overwrite and collisions.
    with destination.open('xb'): pass
    try:
        with closing(sqlite3.connect(source.as_uri()+'?mode=ro',uri=True)) as src, closing(sqlite3.connect(destination)) as dst:
            src.backup(dst)
            if dst.execute('PRAGMA integrity_check').fetchone()[0]!='ok': raise ValueError('数据库完整性校验失败')
            tables={r[0] for r in dst.execute("SELECT name FROM sqlite_master WHERE type='table'")}
            if not {'resources','runs','results','reviews'}.issubset(tables): raise ValueError('不是完整评测数据库')
            interrupted=0
            if restore:
                cursor=dst.execute("UPDATE runs SET status='ERROR',error='从备份恢复，未自动重放旧任务' WHERE status IN ('QUEUED','RUNNING')")
                interrupted=cursor.rowcount
                dst.commit()
            counts={t:dst.execute(f'SELECT count(*) FROM {t}').fetchone()[0] for t in ('resources','runs','results','reviews')}
        return {'destination':str(destination),'sha256':hashlib.sha256(destination.read_bytes()).hexdigest(),'counts':counts,'interrupted_tasks':interrupted}
    except Exception:
        destination.unlink(missing_ok=True)
        raise


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('operation',choices=['backup','restore'])
    parser.add_argument('--source',type=Path,required=True)
    parser.add_argument('--destination',type=Path,required=True)
    args=parser.parse_args()
    root=Path(__file__).resolve().parents[1]
    if not args.destination.resolve().is_relative_to(root): parser.error('目标文件必须位于评测项目根目录内')
    try:
        print(json.dumps(snapshot(args.source,args.destination,args.operation=='restore'),ensure_ascii=False));return 0
    except Exception as exc:
        print(json.dumps({'error':str(exc)},ensure_ascii=False));return 1


if __name__=='__main__': raise SystemExit(main())
