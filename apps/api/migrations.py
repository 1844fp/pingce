"""Ordered, checksummed SQLite migrations with explicit legacy adoption."""
import hashlib
from pathlib import Path

DIRECTORY=Path(__file__).resolve().parents[2]/'infra/sqlite'
EXPECTED={'resources':['id','project','kind','name','body','created'],
          'runs':['id','project','name','spec','status','created','updated','idem','digest','error'],
          'results':['id','run_id','case_id','repetition','body'],
          'reviews':['id','run_id','case_id','repetition','decision','reason','created']}


def migrate(db,directory=DIRECTORY):
    files=sorted(Path(directory).glob('[0-9][0-9][0-9]_*.sql'))
    if not files: raise RuntimeError('缺少数据库迁移文件')
    db.execute('BEGIN IMMEDIATE')
    try:
        tables={r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        if 'schema_migrations' not in tables and tables.intersection(EXPECTED):
            if not set(EXPECTED).issubset(tables): raise RuntimeError('旧数据库表不完整，拒绝自动接管')
            for table,columns in EXPECTED.items():
                info=list(db.execute(f'PRAGMA table_info({table})'))
                if [r[1] for r in info]!=columns or not any(r[1]=='id' and r[5]==1 for r in info):
                    raise RuntimeError('旧数据库结构不兼容：'+table)
            for table,expected in [('runs',('project','idem')),('results',('run_id','case_id','repetition'))]:
                unique={tuple(r[2] for r in db.execute(f'PRAGMA index_info("{idx[1]}")')) for idx in db.execute(f'PRAGMA index_list({table})') if idx[2]}
                if expected not in unique:raise RuntimeError('旧数据库唯一约束不兼容：'+table)
            for table in ('results','reviews'):
                if not any(r[2]=='runs' and r[3]=='run_id' and r[4]=='id' for r in db.execute(f'PRAGMA foreign_key_list({table})')):
                    raise RuntimeError('旧数据库外键不兼容：'+table)
        db.execute('CREATE TABLE IF NOT EXISTS schema_migrations(version INTEGER PRIMARY KEY,name TEXT NOT NULL,sha256 TEXT NOT NULL)')
        applied={r[0]:(r[1],r[2]) for r in db.execute('SELECT version,name,sha256 FROM schema_migrations')}
        versions=[int(f.name[:3]) for f in files]
        if len(set(versions))!=len(versions) or versions!=list(range(1,len(files)+1)):
            raise RuntimeError('迁移版本必须连续且唯一')
        if set(applied)-set(versions): raise RuntimeError('数据库版本高于程序，拒绝降级启动')
        if applied and sorted(applied)!=list(range(1,max(applied)+1)):raise RuntimeError('已应用迁移记录不连续')
        for file,version in zip(files,versions):
            raw=file.read_bytes();checksum=hashlib.sha256(raw).hexdigest()
            if version in applied:
                if applied[version]!=(file.name,checksum):raise RuntimeError('已应用迁移被修改：'+file.name)
                continue
            for statement in raw.decode('utf-8').split(';'):
                if statement.strip():db.execute(statement)
            db.execute('INSERT INTO schema_migrations VALUES(?,?,?)',(version,file.name,checksum))
        db.commit()
        return max(versions)
    except Exception:
        db.rollback();raise
